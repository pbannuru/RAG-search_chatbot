
from fastapi import APIRouter, FastAPI, Depends, Query, Request
from pydantic import BaseModel, field_validator
from typing import Optional, Union, List
from service.chatapi_tools import fetch_result
from service.config import app_config
from utils.coreenum import *
from service.ReplaceLinks import update_markdown_links
from uuid import uuid4
from service.config import app_config
from sql_app.dbenums.core_enums import *
from pydantic import BaseModel
from middlewares.authentication import JWTBearerTenantApiSwaggerAuthenticated
from utils.exception_examples import response_example_search
from utils.rate_limiter import limiter
import re
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from utils.utils import get_emb

router = APIRouter(
    prefix="/Chat_API",
    tags=["search"],
)

app_configs = app_config.AppConfig.get_all_configs()
limit_string = app_configs["chat_api_limit"] + "/minute"
class SearchRequest(BaseModel):
    search_query: str
    domain: DomainEnum
    device: Optional[str] = ""  # Optional with default empty string
    persona: PersonaEnum
    size: int = 5  # Default value
    source: List[SourceEnum] # Can be None (default) or a specific index
    language: LanguageEnum  # Default value

    @field_validator("search_query")
    def validate_search_query(cls, value):
        """Ensure search query contains only alphabets, numbers, and date formats (YYYY-MM-DD or MM/DD/YYYY)."""
        pattern = r"^[a-zA-Z0-9\s\-/:.,()]+$"
        # Allows letters, numbers, spaces, hyphens, slashes, and colons
        
        if len(value) > 400:
            raise ValueError("Search query must not exceed 400 characters.")
        
        if not re.match(pattern, value):
            raise ValueError("Search query can only contain alphabets, numbers, spaces, and date formats (YYYY-MM-DD or MM/DD/YYYY).")
        
        query_emb = get_emb(value)
        query_vec = np.array(query_emb).reshape(1, -1)

        emb_df= pd.read_pickle(app_configs['query_embidding_path'])
        threat_vecs = np.vstack(emb_df["embeddings"].values)
        similarity_scores = cosine_similarity(query_vec, threat_vecs)[0]
        max_similarity = np.max(similarity_scores)

        if max_similarity > 0.79:   #checks if score is >=0.80 then rejects the query
            raise ValueError("Search query is out of my scope. Please ask a valid query.")

        return value
    
@router.put(
    "",
    summary="Chat API for getting the data for entered filters and matching query in body of request",
    responses=response_example_search
)
@limiter.limit(limit_string)
async def search_route(request: Request , searchRequest: SearchRequest,token_payload=Depends(JWTBearerTenantApiSwaggerAuthenticated()),
                       profile: bool = Query(False, description="Enable profiling (default: False)") ):

# async def search_route(request: SearchRequest):
    index_configs = app_config.AppConfig.get_sectionwise_configs("index_values")
    source_list = [source_item.value for source_item in searchRequest.source]
    indices = [index_configs[source_name] for source_name in set(source_list)]

    # Fetch results using async function
    result = await fetch_result(
        search_query=searchRequest.search_query,
        domain=searchRequest.domain.name,
        device=searchRequest.device,
        persona=searchRequest.persona.name,
        size=searchRequest.size,
        source=indices,  # Passing list if no source is provided
        language=searchRequest.language.value,
    )

    post_process_res = update_markdown_links(result["content"],token_payload)
    result["content"]=post_process_res

    return result