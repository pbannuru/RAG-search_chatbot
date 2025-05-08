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
)
from starlette.middleware.authentication import AuthenticationMiddleware

# ISearchUI and OTHER Application
subapp_internal = FastAPI(
    debug=environment.DEBUG_MODE,
    title="Internal Modules",
    description="Internal Modules to both isearchui and expose",
    summary="",
    version="1.0.0",
    contact={},
)

# ISearchUI Search Feedback API
subapp_internal.include_router(isearchui_opensearch_query_execute.router)

subapp_internal.include_router(core_auth.router)  # should be moved to isearch_ui

# Tenant API
subapp_internal.include_router(core_tenant.router)


def register_middlewares(app: FastAPI):
    app.add_middleware(ExceptionHandlerMiddleware)
    app.add_middleware(AuthenticationMiddleware, backend=BearerTokenTenantAuthBackend())

    register_profiler_middlewares(app)


register_middlewares(subapp_internal)
