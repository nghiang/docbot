"""FastAPI dependencies for authentication and database sessions."""

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from core.postgres import postgres_client
from models.user import User
from services.auth_service import auth_service
from services.user_service import user_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

# Use postgres_client.get_session as dependency
get_session = postgres_client.get_session


def get_current_user(
    session: Annotated[Session, Depends(get_session)],
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    """Get the current authenticated user from JWT token.

    Args:
        session: Database session.
        token: JWT token from Authorization header.

    Returns:
        User object.

    Raises:
        HTTPException: If token is invalid or user not found.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = auth_service.decode_access_token(token)
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = user_service.get_by_id(session, int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


def get_optional_user(
    session: Annotated[Session, Depends(get_session)],
    token: Annotated[Optional[str], Depends(oauth2_scheme)],
) -> Optional[User]:
    """Get the current user if authenticated, None otherwise.

    Args:
        session: Database session.
        token: Optional JWT token from Authorization header.

    Returns:
        User object if authenticated, None otherwise.
    """
    if not token:
        return None

    try:
        payload = auth_service.decode_access_token(token)
        user_id = payload.get("sub")
        if user_id:
            return user_service.get_by_id(session, int(user_id))
    except HTTPException:
        pass

    return None


# Type aliases for dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[Optional[User], Depends(get_optional_user)]
DbSession = Annotated[Session, Depends(get_session)]
