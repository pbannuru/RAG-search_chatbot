from typing import AsyncIterator
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi_cache import FastAPICache
from app.config.env import environment
from app.routers.bootstrap import subapp
from app.routers.bootstrap_internal import subapp_internal
from app.routers.bootstrap_isearchui import subapp_isearchUI
from app.routers.bootstrap_load_tester import subapp_simple, subapp_tenant
from fastapi_cache.backends.inmemory import InMemoryBackend
from app.internal.utils.opensearch_utils import OpenSearchUtils


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

# create_database()


# Top level application - for healthcheckups
@app.get("/")
async def read_root():
    return {"Hello": "World"}


# Mount all sub-applications
app.mount("/api/v1", subapp)
app.mount("/api/latest", subapp)
app.mount("/api/internal", subapp_internal)
app.mount("/api/isearchui", subapp_isearchUI)

app.mount("/api/load/simple", subapp_simple)
app.mount("/api/load/tenant", subapp_tenant)
