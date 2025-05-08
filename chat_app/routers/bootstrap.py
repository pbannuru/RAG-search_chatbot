from fastapi.exceptions import RequestValidationError
from middlewares.authentication import BearerTokenTenantAuthBackend
from middlewares.exception import ExceptionHandlerMiddleware
from middlewares.profiler import register_profiler_middlewares
from routers import chatapi_router
from routers import chatapi_router_tools
from service.config.env import environment
from fastapi import FastAPI, Query, HTTPException,Request
from starlette.middleware.authentication import AuthenticationMiddleware
from slowapi.middleware import SlowAPIMiddleware
from utils.rate_limiter import limiter
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_429_TOO_MANY_REQUESTS, HTTP_500_INTERNAL_SERVER_ERROR

subapp = FastAPI(
    debug=environment.DEBUG_MODE,
    title="Chat_compilation_API",
    description="""Token Generation:\n 
    Please Use the below details on Postman to get the access token for API authorization. \n
    Request URL: `https://login-itg.external.hp.com/as/token.oauth2?grant_type=client_credentials`,\n
    Method: `Post`,\n
    Body: contains `client_id` and `client_secret` with enocding type `x-www-form-urlencoded`, \n""",
    summary="Knowledge Service acts as a unified gateway using OpenSearch to consolidate knowledge assets from various sources across HP IPS Service organization and presenting them through a single cohesive service layer for efficient and seamless access.",
    version="1.0.0",
    contact={
        "name": "Knowledge Search",
        "email": "knowlegesearch@hp.com",
    },
)

subapp.include_router(chatapi_router.router)
subapp.include_router(chatapi_router_tools.router)
@subapp.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": "E1002",
        },
    )

@subapp.exception_handler(RateLimitExceeded)
async def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error_code": "E1003",
        },
    )

@subapp.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "E2001",
        }
    )

subapp.state.limiter = limiter

def register_middlewares(app: FastAPI):
    app.add_middleware(ExceptionHandlerMiddleware)
    app.add_middleware(AuthenticationMiddleware, backend=BearerTokenTenantAuthBackend())
    app.add_middleware(SlowAPIMiddleware)
    register_profiler_middlewares(app)   
                                   
register_middlewares(subapp)