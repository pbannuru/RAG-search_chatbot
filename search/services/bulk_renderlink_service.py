from app.config.app_config import AppConfig
from app.dto.bulk_renderlink_response import (
    BulkRenderLinkMetadata,
    BulkRenderLinkResponse,
)
from batch_jobs.tasks.utils.utils import get_kaas_access_token
import requests
from app.sql_app.dbenums.core_enums import LanguageEnum

app_configs = AppConfig.get_sectionwise_configs("kaas_config")


class BulkRenderLinkService:

    def __init__(self, db=None):
        self.db = db

    async def renderlink(self, documentIDs: list[str], language: LanguageEnum):
        access_token = await get_kaas_access_token()
        print(access_token)
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + access_token,
        }

        data = {
            "languageCode": language.value,
            "requests": [
                {
                    "languageCode": language.value,
                    "ids": documentIDs,
                },
            ],
        }

        response = requests.post(
            app_configs["bulk_render_url"], headers=headers, json=data
        )
        response.raise_for_status()
        response = response.json()
        modified_response = modify_response(response)
        metadata = BulkRenderLinkMetadata(documentID=documentIDs, language=language)
        result = BulkRenderLinkResponse(metadata=metadata, data=modified_response)
        return result


def modify_response(response):
    """
    modifies the response json in order to match API response model
    defined in Pydantic.
    """
    updated_response = []
    for item in response:

        for link in item.get("renderLinks", []):
            transformed_link = {
                "documentid": link.get("id"),
                "success": link.get("status") == "SUCCESS",
                "render_link": link.get("renderLink"),
                "error_message": link.get("message"),
                "language": link.get("languageCode"),
            }

            updated_response.append(transformed_link)
    return updated_response
