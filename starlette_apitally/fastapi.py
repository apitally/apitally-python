from typing import Optional

from fastapi.exceptions import HTTPException
from fastapi.openapi.models import APIKey, APIKeyIn
from fastapi.requests import Request
from fastapi.security import SecurityScopes
from fastapi.security.base import SecurityBase
from fastapi.security.utils import get_authorization_scheme_param
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from starlette_apitally.client import ApitallyClient
from starlette_apitally.keys import Key
from starlette_apitally.starlette import ApitallyMiddleware


__all__ = ["ApitallyMiddleware", "Key", "api_key_auth"]


class AuthorizationAPIKeyHeader(SecurityBase):
    def __init__(self, *, auto_error: bool = True):
        self.model = APIKey(
            **{"in": APIKeyIn.header},  # type: ignore[arg-type]
            name="Authorization",
            description="Provide your API key using the <code>Authorization</code> header and the scheme prefix <code>ApiKey</code>.<br>Example: <pre>Authorization: ApiKey your_api_key_here</pre>",
        )
        self.scheme_name = "Authorization header with ApiKey scheme"
        self.auto_error = auto_error

    async def __call__(self, request: Request, security_scopes: SecurityScopes) -> Optional[Key]:
        authorization = request.headers.get("Authorization")
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "apikey":
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated" if not authorization else "Invalid authorization scheme",
                    headers={"WWW-Authenticate": "ApiKey"},
                )
            else:
                return None  # pragma: no cover
        key = ApitallyClient.get_instance().keys.get(param)
        if key is None and self.auto_error:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="Invalid API key",
            )
        if key is not None and self.auto_error and not key.check_scopes(security_scopes.scopes):
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )
        return key


api_key_auth = AuthorizationAPIKeyHeader()
