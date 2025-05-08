from app.config.app_config import AppConfig
from app.dto.render_link_response import RenderLinkResponse
from app.sql_app.database import get_db
from batch_jobs.tasks.utils.utils import get_kaas_access_token
import requests

app_configs = AppConfig.get_sectionwise_configs("kaas_config")


class RenderLinkService:

    def __init__(self, db=None):
        self.db = db

    async def renderlink_ish(self, documentID: str):

        access_token = await get_kaas_access_token()
        headers = {
            "Authorization": "Bearer " + access_token,
        }

        encrypted_token_url = app_configs["kaas_encrypted_token_url"]

        body = {"accessToken": "Bearer " + access_token, "docId": documentID}
        response = requests.post(encrypted_token_url, headers=headers, json=body)
        response.raise_for_status()

        response_data = response.json()
        encrypted_token = response_data.get("encryptedToken")

        if not encrypted_token:
            raise Exception("Encrypted token not found in the response")

        render_url_base = app_configs["render_url"]
        render_url_full = f"{render_url_base}/{encrypted_token}/{documentID}"
        result = RenderLinkResponse(documentID=documentID, render_link=render_url_full)
        return result

    async def renderlink_pdf(self, documentID: str):
        access_token = await get_kaas_access_token()
        headers = {
            "Authorization": "Bearer " + access_token,
        }

        encrypted_token_url = f'{app_configs["render_url_pdf"]}{documentID}'

        response = requests.get(encrypted_token_url, headers=headers)
        response.raise_for_status()

        response_data = response.json()

        if not response_data.get("totalCount"):
            raise Exception("Document Not Found")

        render_url_full = response_data["matches"][0].get("renderLink")

        result = RenderLinkResponse(documentID=documentID, render_link=render_url_full)
        return result
