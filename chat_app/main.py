from utils.opensearch_utils import OpenSearchUtils
import asyncio
from fastapi import FastAPI, Query, HTTPException
from uuid import uuid4
from service.config import app_config
from sql_app.dbenums.core_enums import *
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Union, List, AsyncIterator
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi.concurrency import asynccontextmanager
from service.config.env import environment
from routers.bootstrap import subapp


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    FastAPICache.init(InMemoryBackend())
    yield


app = FastAPI(
    debug=environment.DEBUG_MODE,
    title="Title",
    description="description",
    summary="Summary",
    version="1.0.0",
    contact={
        "name": "Contact Name",
        "url": "http://hp.example.com/contact/",
        "email": "hp@hp.example.com",
    },
    lifespan=lifespan,
)

# Initialise product_mapping dictionary
OpenSearchUtils.init()


# Top level application - for healthcheckups
@app.get("/")
async def read_root():
    return {"Hello": "World"}


app.mount("/chat_compilation/v1", subapp)
