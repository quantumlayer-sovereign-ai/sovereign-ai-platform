"""
JWT Authentication for Sovereign AI Platform

Features:
- JWT token validation
- API key support for service-to-service calls
- User context extraction
- Bearer token handling
"""

import os
from datetime import datetime, timedelta
from typing import Any

from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Configuration
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", "30"))

# API key for service-to-service calls
SERVICE_API_KEYS = set(
    os.environ.get("SERVICE_API_KEYS", "").split(",")
) - {""}

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """Data extracted from JWT token"""
    user_id: str
    email: str | None = None
    roles: list[str] = []
    exp: datetime | None = None


class UserContext(BaseModel):
    """User context for request handling"""
    user_id: str
    email: str | None = None
    roles: list[str] = []
    is_service_account: bool = False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token

    Args:
        data: Token payload data (should include 'sub' for user_id)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """
    Decode and validate a JWT token

    Args:
        token: JWT token string

    Returns:
        TokenData with extracted user information

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: missing user identifier"
            )

        return TokenData(
            user_id=user_id,
            email=payload.get("email"),
            roles=payload.get("roles", []),
            exp=datetime.fromtimestamp(payload.get("exp")) if payload.get("exp") else None
        )

    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {e!s}"
        ) from e


def validate_api_key(api_key: str) -> bool:
    """
    Validate a service API key

    Args:
        api_key: The API key to validate

    Returns:
        True if valid, False otherwise
    """
    if not SERVICE_API_KEYS:
        return False
    return api_key in SERVICE_API_KEYS


class JWTBearer(HTTPBearer):
    """
    FastAPI dependency for JWT authentication

    Usage:
        @app.get("/protected", dependencies=[Depends(JWTBearer())])
        async def protected_endpoint():
            ...

        # Or to get user context:
        @app.get("/me")
        async def get_me(user: UserContext = Depends(JWTBearer())):
            return user
    """

    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> UserContext:
        # Check for API key first (service-to-service)
        api_key = request.headers.get("X-API-Key")
        if api_key:
            if validate_api_key(api_key):
                return UserContext(
                    user_id="service-account",
                    roles=["service"],
                    is_service_account=True
                )
            else:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid API key"
                )

        # Fall back to JWT Bearer token
        credentials: HTTPAuthorizationCredentials | None = await super().__call__(request)

        if credentials:
            if credentials.scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=401,
                    detail="Invalid authentication scheme. Use Bearer token."
                )

            token_data = decode_token(credentials.credentials)

            return UserContext(
                user_id=token_data.user_id,
                email=token_data.email,
                roles=token_data.roles,
                is_service_account=False
            )

        raise HTTPException(
            status_code=401,
            detail="Authorization header required"
        )


class OptionalJWTBearer(JWTBearer):
    """
    Optional JWT authentication - doesn't fail if no token provided

    Useful for endpoints that have different behavior for authenticated vs anonymous users
    """

    def __init__(self):
        super().__init__(auto_error=False)

    async def __call__(self, request: Request) -> UserContext | None:
        try:
            return await super().__call__(request)
        except HTTPException:
            return None


# Dev mode token generation (only enabled if DEV_MODE=true)
DEV_MODE = os.environ.get("DEV_MODE", "false").lower() == "true"


def create_dev_token(user_id: str = "dev-user", email: str = "dev@example.com") -> dict[str, str]:
    """
    Create a development token (only works in DEV_MODE)

    Args:
        user_id: User ID for the token
        email: Email for the token

    Returns:
        Dict with access_token and token_type
    """
    if not DEV_MODE:
        raise HTTPException(
            status_code=403,
            detail="Dev token generation is disabled in production"
        )

    token = create_access_token(
        data={
            "sub": user_id,
            "email": email,
            "roles": ["developer", "admin"]
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }
