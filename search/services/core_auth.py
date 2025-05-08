from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Request, HTTPException

from app.middlewares.authentication import verify_tenant_jwt
from app.services.core_tenant_service import CoreTenantService
from app.sql_app.database import DbDepends
from app.sql_app.dbmodels.core_tenant import CoreTenant


class JWTBearerApplicationAdminOnly(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearerApplicationAdminOnly, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> CoreTenant:
        credentials: HTTPAuthorizationCredentials = await super(
            JWTBearerApplicationAdminOnly, self
        ).__call__(request)
        if credentials:
            if credentials.scheme != "Bearer":
                raise HTTPException(
                    status_code=403, detail="Invalid authentication scheme."
                )
            print(credentials.credentials)
            is_token_valid, payload = verify_tenant_jwt(credentials.credentials)
            # get db client_id

            if not is_token_valid:
                raise HTTPException(
                    status_code=403, detail="Invalid token or expired token."
                )
            with DbDepends() as db:
                tenant = CoreTenantService(db).get_by_client_id(payload.client_id)

            if not tenant:
                raise HTTPException(status_code=403, detail="Invalid tenant.")

            if not tenant.application_admin:
                raise HTTPException(
                    status_code=403,
                    detail="Only application admins are allowed to access this resource.",
                )
            return tenant
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")
