from slowapi import Limiter
from starlette.requests import Request

def custom_rate_limit(request: Request):
    return request.user.uuid


limiter = Limiter(
    key_func=custom_rate_limit,
)
