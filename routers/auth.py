# routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from core.database import get_db
from core.auth import (
    get_auth_service, get_current_user,
    require_privileges, generate_password, oauth2_scheme
)
from schemas.user import (
    UserCreate, UserResponse, UserCreateOAuth,
    UserDetailResponse, UserUpdate,
    BootstrapAdminRequest, BootstrapAdminResponse
)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=dict, summary="Obtain access & refresh tokens")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service=Depends(get_auth_service),
):
    tokens = auth_service.authenticate_user(form_data.username, form_data.password)
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_service.create_tokens(tokens.id)

@router.post("/refresh", response_model=dict, summary="Refresh access token")
async def refresh(
    token: str = Depends(oauth2_scheme),
    auth_service=Depends(get_auth_service),
):
    return auth_service.refresh_token(token)

@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    user_in: UserCreate,
    auth_service=Depends(get_auth_service),
):
    return auth_service.create_user(user_in)

@router.post("/register-oauth", response_model=UserResponse, status_code=201)
async def register_oauth(
    user_in: UserCreateOAuth,
    auth_service=Depends(get_auth_service),
):
    return auth_service.get_or_create_oauth_user(**user_in.dict())

@router.get("/me", response_model=UserResponse, summary="Get profile")
async def me(current_user=Depends(get_current_user)):
    return current_user

@router.get("/me/detail", response_model=UserDetailResponse, summary="Get profile w/ OAuth")
async def me_detail(current_user=Depends(get_current_user),
                    auth_service=Depends(get_auth_service)):
    detail = UserDetailResponse.from_orm(current_user)
    detail.oauth_accounts = auth_service.get_oauth_accounts(current_user.id)
    return detail

@router.put("/me", response_model=UserResponse, summary="Update profile")
async def update_me(
    user_in: UserUpdate,
    current_user=Depends(get_current_user),
    auth_service=Depends(get_auth_service),
):
    return auth_service.update_user(current_user.id, user_in.dict(exclude_unset=True))

@router.post("/bootstrap", response_model=BootstrapAdminResponse, status_code=201,
             summary="Bootstrap first superuser")
async def bootstrap(
    info: BootstrapAdminRequest,
    db: Session = Depends(get_db),
    auth_service=Depends(get_auth_service),
):
    # Check existance of any superuser
    from models.user import User
    if db.query(User).filter(User.is_superuser == True).first():
        raise HTTPException(status_code=400, detail="Platform already set up")
    pwd = info.password or generate_password()
    # create with is_superuser=True
    user_in = UserCreate(
        email=info.email,
        password=pwd,
        full_name=info.full_name,
        is_superuser=True,
    )
    admin = auth_service.create_user(user_in)
    return BootstrapAdminResponse(email=admin.email, password=pwd)
