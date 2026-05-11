from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import User
from schemas import UserRegister, UserLogin, TokenResponse
from auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(body: UserRegister, db: AsyncSession = Depends(get_db)):
    if len(body.username) < 2 or len(body.username) > 32:
        raise HTTPException(status_code=400, detail="用户名长度需在2-32个字符之间")
    if len(body.password) < 4:
        raise HTTPException(status_code=400, detail="密码长度至少4位")

    existing = await db.execute(select(User).where(User.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="用户名已存在")

    user = User(username=body.username, password_hash=hash_password(body.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id, user.username)
    return TokenResponse(access_token=token, username=user.username)


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_access_token(user.id, user.username)
    return TokenResponse(access_token=token, username=user.username)
