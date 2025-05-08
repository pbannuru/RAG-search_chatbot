from app.services.opensearch_service_upgraded_api import OpenSearchService
from sqlalchemy.orm import Session
from app.config import app_config
from app.internal.utils.timer import Timer
from app.config.env import environment
from typing import List
from app.dto.autosuggest import ResponseMetadata, AutoSuggestResponse
from app.sql_app.dbenums.core_enums import (
    PersonaEnum,
    DomainEnum,
    SourceEnum,
    LanguageEnum,
)


app_configs = app_config.AppConfig.get_all_configs()


class CoreAutoSuggestService:
    def __init__(self, db: Session):
        self.db = db

    async def auto_suggest(
        self,
        query: str,
        persona: PersonaEnum,
        limit: int,
        domain: DomainEnum,
        device: str,
        source: List[SourceEnum],
        language: LanguageEnum,
    ):

        timer = Timer().start_timer()
        response = OpenSearchService.get_auto_suggest_response(
            query, device, persona, limit, domain, source, language
        )
        print(response)
        timer.end_timer()
        suggestions = []

        for search_hits in response["hits"]["hits"]:
            if environment.DEBUG_MODE:
                print("-------------------------------------------------------")
                print('printing_highlight',search_hits["highlight"])

            if "text" in search_hits["highlight"]:
                suggestions.append(search_hits["highlight"]["text"][0])

            elif "text._index_prefix" in search_hits["highlight"]:
                suggestions.append(
                    search_hits["highlight"]["text._index_prefix"][0]
                )

        # removing duplicates
        suggestions = list(dict.fromkeys(suggestions))

        metadata = ResponseMetadata(
            size=len(suggestions),
            limit=limit,
            query=query,
            device=device,
            persona=persona,
            domain=domain,
            source=source,
            language=language,
        )

        return AutoSuggestResponse(metadata=metadata, data=suggestions)
