from fastapi import FastAPI
from app.config.env import environment
from app.middlewares.authentication import (
    BearerTokenTenantAuthBackend,
)

from app.middlewares.exception import ExceptionHandlerMiddleware
from app.middlewares.profiler import register_profiler_middlewares
from app.routers import (
    core_tenant,
    core_auth,
    isearchui_opensearch_query_execute,
    load,
)
from starlette.middleware.authentication import AuthenticationMiddleware

# ISearchUI and OTHER Application
subapp_simple = FastAPI(
    debug=environment.DEBUG_MODE,
    title="Profiler",
    description="Internal Modules to both isearchui and expose",
    summary="",
    version="1.0.0",
    contact={},
)


subapp_simple.include_router(load.simple_router)


subapp_tenant = FastAPI(
    debug=environment.DEBUG_MODE,
    title="Profiler",
    description="Internal Modules to both isearchui and expose",
    summary="",
    version="1.0.0",
    contact={},
)
subapp_tenant.include_router(load.tenant_router)


def register_middlewares(app: FastAPI):
    app.add_middleware(ExceptionHandlerMiddleware)
    app.add_middleware(AuthenticationMiddleware, backend=BearerTokenTenantAuthBackend())

    register_profiler_middlewares(app)


register_middlewares(subapp_tenant)
