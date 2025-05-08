import asyncio
import logging
import re,json
from traceback import print_exception
import traceback
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from utils.timer import Timer
from service.core_audit_log_service import CoreAuditLogService
from sql_app.database import DbDepends
from sql_app.dbenums.audit_log_enums import ContextEnum, ServiceEnum
from sql_app.dbmodels.core_audit_log import CoreAuditLog

logger = logging.getLogger(__name__)


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        route = request.url.path
        if (
            route.endswith("docs")
            or route.endswith("redoc")
            or route.endswith("openapi.json")
        ):
            return await call_next(request)

        timer = Timer().start_timer()
        if not request.user.is_authenticated:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Unauthorized",
                    "messages": f"Please pass a valid token associated with a valid tenant",
                },
            )

        with DbDepends() as db:

            try:
                request_body = await request.body()

                response = await call_next(request)
                timer.end_timer()

                await self.audit_info_log(request, timer, db, request_body)

                return response
            except Exception as e:
                timer.end_timer()
                print_exception(e)
                audit_error_log = await self.audit_error_log(request, timer, db, request_body)
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": e.__class__.__name__,
                        "messages": f"Internal Server Error. LogID - {audit_error_log.id}",
                        "error_log_id": audit_error_log.id,
                    },
                )

    @staticmethod
    async def audit_error_log(request: Request, timer: Timer, db,request_body) -> CoreAuditLog:
        # Access query parameters to form log_input dict
        log_input_dict, route, service = await ExceptionHandlerMiddleware.retrive_log_details(
            request, request_body
        )
        audit_error_log = await CoreAuditLogService(db).log_service_api_error(
            route="/" + route,
            context=ContextEnum.API,
            service=service,
            tenant_id=request.user.uuid,
            log_input=log_input_dict,
            duration_ms=timer.elapsed_time_ms,
            stack_trace=traceback.format_exc(),
        )
        return audit_error_log

    @staticmethod
    async def audit_info_log(request: Request, timer: Timer, db,request_body):
        # Access query parameters to form log_input dict
        log_input_dict, route, service = await ExceptionHandlerMiddleware.retrive_log_details(
            request,request_body
        )
        await CoreAuditLogService(db).log_service_api(
            route="/" + route,
            context=ContextEnum.API,
            service=service,
            tenant_id=request.user.uuid,
            log_input=log_input_dict,
            duration_ms=timer.elapsed_time_ms,
        )

    @staticmethod
    async def retrive_log_details(request: Request,request_body):

        # print("_______________this the request_________________",asyncio.run(request.body()))
        log_input_dict = {
            "query_params": dict(request.query_params),
            "path_params": request.path_params if request.path_params else {},
            "body_params": {}
        }

        # Read the request body (synchronously)
        try:
            log_input_dict["body_params"] = json.loads(request_body.decode()) if request_body else {}
            print(log_input_dict)
            # log_input_dict["body_params"] = json.loads(body.decode()) if body else {}
        except Exception:
            log_input_dict["body_params"] = {}  # If body is empty or not valid JSON   

        # Use regular expression pattern to exclude `/api/<str>/` from route path
        # examples for route path: `/api/v1/search`, `/api/v20/search`, `/api/internal/search`
        urlRoute = request.url.path
        pattern = r"\/([^\/]+)\/([^\/]+)\/?(.*)"
        match = re.search(pattern, urlRoute)
        service_name = match.group(2)  # Extract "v1"
        route = match.group(3) 

        service = None
        if service_name == "v1":
            if route == "Chat_API":
                service = ServiceEnum.CORE

        return log_input_dict, route, service
    

