import uuid
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import create_access_token, decode_access_token
from src.db.base import get_db_session
from src.models.user import User
from src.schemas.schemas import (
    UserLoginRequest,
    UserLoginResponse,
    UserRequest,
    UserResponse,
)

bearer_scheme = HTTPBearer()
router = APIRouter(prefix="/users", tags=["users"])
DbSession = Annotated[AsyncSession, Depends(get_db_session)]
password_hasher = PasswordHash.recommended()


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(payload: UserRequest, session: DbSession) -> UserResponse:
    result = await session.execute(select(User).where(User.email == payload.email))
    if result.scalars().first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "такой пользователь уже есть")
    db_user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=password_hasher.hash(payload.password),
    )
    session.add(db_user)
    await session.flush()
    await session.refresh(db_user)
    return UserResponse.model_validate(db_user)


@router.post("/login", response_model=UserLoginResponse)
async def login_user(
    payload: UserLoginRequest, session: DbSession
) -> UserLoginResponse:
    result = await session.execute(select(User).where(User.email == payload.email))
    user = result.scalars().first()
    # одно и то же сообщение для «нет пользователя» и «неверный пароль»
    if user is None or not password_hasher.verify(
        payload.password, user.hashed_password
    ):
        raise _unauthorized("неверный email или пароль")
    return UserLoginResponse(access_token=create_access_token({"sub": str(user.id)}))


async def get_current_user(
    session: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> User:
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise _unauthorized("токен истёк")
    except jwt.InvalidTokenError:
        raise _unauthorized("неверный токен")
    try:
        user_id = uuid.UUID(str(payload.get("sub")))
    except ValueError:
        raise _unauthorized("неверный токен")
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise _unauthorized("пользователь не найден")
    return user


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return UserResponse.model_validate(current_user)
