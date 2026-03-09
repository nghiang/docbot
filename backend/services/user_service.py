"""User service for handling user-related business logic."""

from typing import Optional

from sqlmodel import Session, select

from models.user import User
from services.auth_service import auth_service


class UserService:
    """Service class for user operations."""

    def __init__(self):
        self._auth_service = auth_service

    def get_by_email(self, session: Session, email: str) -> Optional[User]:
        """Get a user by email address.

        Args:
            session: Database session.
            email: User's email address.

        Returns:
            User object if found, None otherwise.
        """
        statement = select(User).where(User.email == email)
        return session.exec(statement).first()

    def get_by_username(self, session: Session, username: str) -> Optional[User]:
        """Get a user by username.

        Args:
            session: Database session.
            username: User's username.

        Returns:
            User object if found, None otherwise.
        """
        statement = select(User).where(User.username == username)
        return session.exec(statement).first()

    def get_by_id(self, session: Session, user_id: int) -> Optional[User]:
        """Get a user by ID.

        Args:
            session: Database session.
            user_id: User's ID.

        Returns:
            User object if found, None otherwise.
        """
        return session.get(User, user_id)

    def create(
        self,
        session: Session,
        email: str,
        username: str,
        password: str,
        full_name: Optional[str] = None,
    ) -> User:
        """Create a new user.

        Args:
            session: Database session.
            email: User's email address.
            username: User's username.
            password: Plain text password (will be hashed).
            full_name: Optional full name.

        Returns:
            Created User object.
        """
        hashed_password = self._auth_service.hash_password(password)
        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            full_name=full_name,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    def authenticate(
        self,
        session: Session,
        email: str,
        password: str,
    ) -> Optional[User]:
        """Authenticate a user by email and password.

        Args:
            session: Database session.
            email: User's email address.
            password: Plain text password.

        Returns:
            User object if authentication successful, None otherwise.
        """
        user = self.get_by_email(session, email)
        if not user:
            return None
        if not self._auth_service.verify_password(password, user.hashed_password):
            return None
        return user

    def is_email_taken(self, session: Session, email: str) -> bool:
        """Check if email is already registered.

        Args:
            session: Database session.
            email: Email address to check.

        Returns:
            True if email is taken, False otherwise.
        """
        return self.get_by_email(session, email) is not None

    def is_username_taken(self, session: Session, username: str) -> bool:
        """Check if username is already taken.

        Args:
            session: Database session.
            username: Username to check.

        Returns:
            True if username is taken, False otherwise.
        """
        return self.get_by_username(session, username) is not None


# Singleton instance
user_service = UserService()
