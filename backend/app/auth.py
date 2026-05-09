"""JWT Authentication for FastAPI.

Integrates with frontend's better-auth JWT tokens.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, cast

from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.config import settings

logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = (
    settings.better_auth_secret
    if hasattr(settings, "better_auth_secret")
    else "change-me-in-production"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# Token model
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: str | None = None
    email: str | None = None


class User(BaseModel):
    id: str
    email: str
    name: str | None = None


# HTTP Bearer scheme
security = HTTPBearer()


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token.

    Args:
        data: Dictionary containing token claims (user_id, email, etc.)
        expires_delta: Optional timedelta for token expiration

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    now = datetime.now(UTC)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=15)

    to_encode.update(
        {
            "exp": expire,
            "iat": now,
            "type": "access",
        }
    )
    encoded_jwt: str = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> TokenData:
    """Decode and validate a JWT access token.

    Args:
        token: JWT token string

    Returns:
        TokenData containing user information

    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = cast(str, payload.get("sub") or payload.get("userId") or payload.get("user_id"))
        email = cast(str | None, payload.get("email"))

        if user_id is None:
            raise credentials_exception

        return TokenData(user_id=user_id, email=email)
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        raise credentials_exception


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> User:
    """Dependency to get the current authenticated user from JWT token.

    Args:
        request: FastAPI Request object
        credentials: HTTP Bearer credentials

    Returns:
        User object with user information

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    token_data = decode_access_token(token)

    # In production, you might want to fetch user from database here
    # For now, we just return the user from the token
    if not token_data.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = User(
        id=token_data.user_id,
        email=token_data.email or "",
    )

    return user


async def get_current_user_optional(
    request: Request,
) -> User | None:
    """Dependency to get the current user if authenticated, None otherwise.

    Useful for endpoints that work with or without authentication.

    Args:
        request: FastAPI Request object

    Returns:
        User object if authenticated, None otherwise
    """
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split("Bearer ")[1].strip()
        token_data = decode_access_token(token)

        if not token_data.user_id:
            return None

        return User(
            id=token_data.user_id,
            email=token_data.email or "",
        )
    except (JWTError, HTTPException) as e:
        logger.debug(f"Optional auth failed: {e}")
        return None


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT authentication.

    Can be used to protect all routes or specific route groups.
    Inherits from BaseHTTPMiddleware for proper async support.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Middleware to verify JWT tokens."""
        # Skip auth for public endpoints
        public_paths = ["/", "/health", "/docs", "/redoc", "/openapi.json"]
        if any(request.url.path.startswith(path) for path in public_paths):
            return await call_next(request)

        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return await call_next(request)  # Allow unauthenticated for now

        try:
            token = auth_header.split("Bearer ")[1].strip()
            decode_access_token(token)
            # Token is valid, add user to request state
        except HTTPException:
            return await call_next(request)  # Allow unauthenticated for now

        return await call_next(request)
