"""Authentication routes for login and registration."""

from fastapi import APIRouter, HTTPException, status

from core.dependencies import DbSession, CurrentUser
from schemas.user import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from services.auth_service import auth_service
from services.user_service import user_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
def register(request: RegisterRequest, session: DbSession) -> TokenResponse:
    """Register a new user.

    Args:
        request: Registration data.
        session: Database session.

    Returns:
        TokenResponse with JWT access token.

    Raises:
        HTTPException: If email or username is already taken.
    """
    # Check if email is already taken
    if user_service.is_email_taken(session, request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Check if username is already taken
    if user_service.is_username_taken(session, request.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Create user
    user = user_service.create(
        session=session,
        email=request.email,
        username=request.username,
        password=request.password,
        full_name=request.full_name,
    )

    # Generate access token
    access_token = auth_service.create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, session: DbSession) -> TokenResponse:
    """Login with email and password.

    Args:
        request: Login credentials.
        session: Database session.

    Returns:
        TokenResponse with JWT access token.

    Raises:
        HTTPException: If credentials are invalid.
    """
    user = user_service.authenticate(session, request.email, request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = auth_service.create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(user: CurrentUser) -> UserResponse:
    """Get current user information.

    Args:
        user: Current authenticated user.

    Returns:
        UserResponse with user data.
    """
    return UserResponse(
        id=user.id if user.id else 0,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
    )
