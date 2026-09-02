"""
name: auth_router.py
description: FastAPI authentication router providing login verification against
             the database User model. Registration is strictly disallowed via API.
"""

from __future__ import annotations

import logging
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.database import async_session_maker
from app.models import User
from app.core.security import verify_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


async def get_db() -> AsyncSession:
    """Dependency yielding an async database session."""
    async with async_session_maker() as session:
        yield session


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50, description="Login username")
    password: str = Field(..., min_length=1, description="Account password")


class UserDTO(BaseModel):
    id: str
    username: str
    full_name: str
    is_active: bool


class LoginResponse(BaseModel):
    success: bool
    message: str
    user: UserDTO


@router.post("/login", response_model=LoginResponse, summary="Login User")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Authenticates username and password against PostgreSQL database.
    """
    username = req.username.strip()
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        logger.warning("Failed login attempt for non-existent username: %s", username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không chính xác.",
        )

    if not user.is_active:
        logger.warning("Login attempt for deactivated user: %s", username)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản này đã bị tạm khóa.",
        )

    if not verify_password(req.password, user.hashed_password):
        logger.warning("Invalid password attempt for user: %s", username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không chính xác.",
        )

    logger.info("User '%s' logged in successfully.", username)
    return LoginResponse(
        success=True,
        message="Đăng nhập thành công.",
        user=UserDTO(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
        ),
    )
