from fastapi import FastAPI
from app.config.env import environment
from app.middlewares.authentication import BearerTokenISearchUserAuthBackend
from app.middlewares.profiler import register_profiler_middlewares
from app.routers import (
    isearchui_search_feedback,
    isearchui_users,
    isearchui_opensearch_query,
)
from starlette.middleware.authentication import AuthenticationMiddleware
from fastapi.middleware.cors import CORSMiddleware

# ISearchUI and OTHER Application
subapp_isearchUI = FastAPI(
    debug=environment.DEBUG_MODE,
    title="ISearch UI Specific APIs",
    description="This API is specifically built for isearch UI",
    summary="",
    version="1.0.0",
    contact={},
)

# ISearchUI Search Feedback API
subapp_isearchUI.include_router(isearchui_search_feedback.router)
subapp_isearchUI.include_router(isearchui_users.router)
subapp_isearchUI.include_router(isearchui_opensearch_query.router)


def register_middlewares(app: FastAPI):
    # app.add_middleware(ExceptionHandlerMiddleware)
    app.add_middleware(
        AuthenticationMiddleware, backend=BearerTokenISearchUserAuthBackend()
    )

    register_profiler_middlewares(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


register_middlewares(subapp_isearchUI)
