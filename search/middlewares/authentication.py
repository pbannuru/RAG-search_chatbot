from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from pydantic import BaseModel, EmailStr
import requests
from app.services.core_tenant_service import CoreTenantService
from app.services.isearchui_users_service import ISearchUIUsersService
from app.sql_app.database import DbDepends
from starlette.authentication import (
    AuthenticationBackend,
    AuthenticationError,
)

from app.sql_app.dbmodels.core_tenant import CoreTenant

#
# FROM https://login-itg.external.hp.com/ext/oauth/jwks
jwks = {
        
        "keys": [
            {
                "kty": "RSA",
                "kid": "Key",
                "use": "sig",
                "n": "iGp1mNINc6Wmqh8OXJ3tvK_LYH4bVrXNoViFTkMmOHZhDrxGGUDdIpTfdw4wZ6C0yMeEV6JKbLVIrP-6VwYLNjh63D1eWw5OfmSPjd31zgBx4V3X-EQWVe2Qjv9vww3OdZ3J5BvNmWt0vJMrAnpECyKbLp_-56aBLoNiaHAI8AkWq-jatTgAaTzBKRdRMQtOZVPDM42W48fUF3IoW8xJ9DEhQWw5qWymXYQuKSavxu0xOfhZwGnVBLGDsjvvSGUUE_J3P3zW0p-tKLxCaN4XesdyzdtNDy3-_mQUju9GWaOuR8u1Je7KG7sUMXK385KZ-MIbzTq2GovPSzR33-IVDw",
                "e": "AQAB",
                "x5c": [
                    "MIIFZzCCBE+gAwIBAgIQBVljNJOzKm2FLpbDrxQ9gjANBgkqhkiG9w0BAQsFADB5MQswCQYDVQQGEwJVUzEfMB0GA1UEChMWSFAgR2xvYmFsIFBLSSBTZXJ2aWNlczEcMBoGA1UECxMTSFAgRGlnaXRhbEJhZGdlIFBLSTErMCkGA1UEAxMiSFAgSW5jIFByaXZhdGUgU1NMIEludGVybWVkaWF0ZSBDQTAeFw0yNTAyMTAwMDAwMDBaFw0yNjAyMTAyMzU5NTlaMGgxCzAJBgNVBAYTAlVTMRMwEQYDVQQIEwpDYWxpZm9ybmlhMRIwEAYDVQQHEwlQYWxvIEFsdG8xDzANBgNVBAoTBkhQIEluYzEfMB0GA1UEAxMWbG9naW4taXRnLm9hdXRoLmhwLmNvbTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAIhqdZjSDXOlpqofDlyd7byvy2B+G1a1zaFYhU5DJjh2YQ68RhlA3SKU33cOMGegtMjHhFeiSmy1SKz/ulcGCzY4etw9XlsOTn5kj43d9c4AceFd1/hEFlXtkI7/b8MNznWdyeQbzZlrdLyTKwJ6RAsimy6f/uemgS6DYmhwCPAJFqvo2rU4AGk8wSkXUTELTmVTwzONluPH1BdyKFvMSfQxIUFsOalspl2ELikmr8btMTn4WcBp1QSxg7I770hlFBPydz981tKfrSi8QmjeF3rHcs3bTQ8t/v5kFI7vRlmjrkfLtSXuyhu7FDFyt/OSmfjCG806thqLz0s0d9/iFQ8CAwEAAaOCAfowggH2MB8GA1UdIwQYMBaAFMmpCCl+5EK97OK+S7Ti6DmKkzHtMB0GA1UdDgQWBBTmVW/42O+2cHWi4WDCL4C0PuCwHzAhBgNVHREEGjAYghZsb2dpbi1pdGcub2F1dGguaHAuY29tMEEGA1UdIAQ6MDgwNgYJYIZIAYb9bAEBMCkwJwYIKwYBBQUHAgEWG2h0dHA6Ly93d3cuZGlnaWNlcnQuY29tL0NQUzAOBgNVHQ8BAf8EBAMCBaAwHQYDVR0lBBYwFAYIKwYBBQUHAwEGCCsGAQUFBwMCMIGPBgNVHR8EgYcwgYQwQKA+oDyGOmh0dHA6Ly9jcmwzLmRpZ2ljZXJ0LmNvbS9IUEluY1ByaXZhdGVTU0xJbnRlcm1lZGlhdGVDQS5jcmwwQKA+oDyGOmh0dHA6Ly9jcmw0LmRpZ2ljZXJ0LmNvbS9IUEluY1ByaXZhdGVTU0xJbnRlcm1lZGlhdGVDQS5jcmwwfwYIKwYBBQUHAQEEczBxMCQGCCsGAQUFBzABhhhodHRwOi8vb2NzcC5kaWdpY2VydC5jb20wSQYIKwYBBQUHMAKGPWh0dHA6Ly9jYWNlcnRzLmRpZ2ljZXJ0LmNvbS9IUEluY1ByaXZhdGVTU0xJbnRlcm1lZGlhdGVDQS5jcnQwDAYDVR0TAQH/BAIwADANBgkqhkiG9w0BAQsFAAOCAQEAkX7QS1xmZT/UdfPYW5TYXof23N+67yTTGWjgVqotDhZ5FTGQhBPbqbjjSEzgVmNUImgCCyeHXYa6kr0TWMVPvRnW5Q9jHLDovZxV0WubNFSgx5TdD+3hh8qMKk1TrS1yqu7MMM8H6qDh1jJ1WMG6MHwXBb47zd3wOsg/TkriSn+5PQE/FHSlidSYgomsko6s1JlL7E/xKHTWJ4Xq45fWvL19vGRxt7sHwqYXHCcXECqHXuPSmKtLO5NFu19OHKQfsuCyGE5ZprxsvPOHZZMe7Jp+duKMPsFgd7BSSH0I51lSRLYkjJ2f0PKfnOWSBJvl5l8gWUWtKQ2POd3K9O8F/Q=="
                ],
                "x5t": "ig5DY5jhbDeFTCFnWdp1VnG3w2A",
            }
        ]
    }

# used an online converter to obtain the public key from JWK

public_key = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAiGp1mNINc6Wmqh8OXJ3t
vK/LYH4bVrXNoViFTkMmOHZhDrxGGUDdIpTfdw4wZ6C0yMeEV6JKbLVIrP+6VwYL
Njh63D1eWw5OfmSPjd31zgBx4V3X+EQWVe2Qjv9vww3OdZ3J5BvNmWt0vJMrAnpE
CyKbLp/+56aBLoNiaHAI8AkWq+jatTgAaTzBKRdRMQtOZVPDM42W48fUF3IoW8xJ
9DEhQWw5qWymXYQuKSavxu0xOfhZwGnVBLGDsjvvSGUUE/J3P3zW0p+tKLxCaN4X
esdyzdtNDy3+/mQUju9GWaOuR8u1Je7KG7sUMXK385KZ+MIbzTq2GovPSzR33+IV
DwIDAQAB
-----END PUBLIC KEY-----"""


class VerifiedTokenBody(BaseModel):
    client_id: str
    # scope: list[str]
    # authorization_details: list[str]
    iss: str
    exp: int


def verify_tenant_service_token(token: str) -> VerifiedTokenBody:
    decoded_payload = jwt.decode(
        token,
        public_key,
        algorithms=[
            "RS256",
        ],
    )
    return VerifiedTokenBody(**decoded_payload)


def verify_tenant_jwt(jwtoken: str) -> list[bool | VerifiedTokenBody]:
    is_token_valid: bool = False
    payload = None

    try:
        payload = verify_tenant_service_token(jwtoken)
    except Exception as e:
        print("TokenError: ", e)
        payload = None
        raise AuthenticationError(f"TokenError while verifying service token: {e}")
    if payload:
        is_token_valid = True

    return is_token_valid, payload


class BearerTokenTenantAuthBackend(AuthenticationBackend):

    async def authenticate(self, request):
        if "Authorization" not in request.headers:
            return

        auth = request.headers["Authorization"]

        try:
            scheme, token = auth.split()
            if scheme.lower() != "bearer":
                return
            is_token_valid, payload = verify_tenant_jwt(token)
        except (ValueError, UnicodeDecodeError) as exc:
            raise AuthenticationError("Invalid JWT Token.")

        if not is_token_valid:
            raise HTTPException(
                status_code=403, detail="Invalid token or expired token."
            )

        with DbDepends() as db:
            tenant = CoreTenantService(db).get_by_client_id(payload.client_id)
            if not tenant:
                raise HTTPException(status_code=403, detail="Tenant Not Found.")

        return auth, tenant


# ISearch UI


class VerifiedTokenBodyISearchUI(BaseModel):
    uid: EmailStr
    sub: EmailStr
    ntUserDomainId: str
    givenName: str
    employeeNumber: int


def verify_isearch_user_service_token(token: str) -> VerifiedTokenBodyISearchUI:
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        "https://login-itg.external.hp.com/idp/userinfo.openid", headers=headers
    )
    response.raise_for_status()
    return VerifiedTokenBodyISearchUI(**response.json())


def verify_isearch_user_jwt(jwtoken: str) -> list[bool | VerifiedTokenBodyISearchUI]:
    is_token_valid: bool = False
    payload = None

    try:
        payload = verify_isearch_user_service_token(jwtoken)
    except Exception as e:
        print("TokenError: ", e)
        payload = None
        raise AuthenticationError(f"TokenError while verifying service token: {e}")
    if payload:
        is_token_valid = True

    return is_token_valid, payload


class BearerTokenISearchUserAuthBackend(AuthenticationBackend):

    async def authenticate(self, request):
        if "Authorization" not in request.headers:
            return

        auth = request.headers["Authorization"]

        try:
            scheme, token = auth.split()
            if scheme.lower() != "bearer":
                return
            is_token_valid, payload = verify_isearch_user_jwt(token)
        except (ValueError, UnicodeDecodeError) as exc:
            raise AuthenticationError("Invalid JWT Token.")

        if not is_token_valid:
            raise HTTPException(
                status_code=403, detail="Invalid token or expired token."
            )

        with DbDepends() as db:
            user = ISearchUIUsersService(db).get_or_create_user(email=payload.uid)

            if not user:
                raise HTTPException(
                    status_code=403, detail="User Not Found, or Creation Failed."
                )

        return auth, user


# used for swagger documentation
class JWTBearerTenantApiSwaggerAuthenticated(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearerTenantApiSwaggerAuthenticated, self).__init__(
            auto_error=auto_error
        )

    async def __call__(self, request: Request) -> CoreTenant:
        credentials: HTTPAuthorizationCredentials = await super(
            JWTBearerTenantApiSwaggerAuthenticated, self
        ).__call__(request)


# used for swagger documentation
class JWTBearerISearchUserSwaggerAuthenticated(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearerISearchUserSwaggerAuthenticated, self).__init__(
            auto_error=auto_error
        )

    async def __call__(self, request: Request) -> CoreTenant:
        credentials: HTTPAuthorizationCredentials = await super(
            JWTBearerISearchUserSwaggerAuthenticated, self
        ).__call__(request)
