from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.auth import UserCreate, Token, UserResponse
from app.services import auth_service, AuthServiceError
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_create: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Register a new user.
    
    Args:
        user_create: User registration data (email, password).
        db: Database session.
    
    Returns:
        Access token for the newly registered user.
    """
    try:
        _, access_token = await auth_service.register_user(db, user_create)
        return Token(access_token=access_token)
    except AuthServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Authenticate a user and return an access token.
    
    Uses OAuth2 password flow (form data: username, password).
    Note: 'username' field is used for email.
    
    Args:
        form_data: OAuth2 form with username (email) and password.
        db: Database session.
    
    Returns:
        Access token for authenticated user.
    """
    result = await auth_service.authenticate_user(db, form_data.username, form_data.password)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    _, access_token = result
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get the currently authenticated user's information.
    
    Args:
        current_user: The authenticated user (from JWT).
    
    Returns:
        User information.
    """
    return current_user
