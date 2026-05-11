from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class UserRegister(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class GenerateGameRequest(BaseModel):
    prompt: str


class GameMemoryOut(BaseModel):
    id: str
    game_name: str
    game_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class GameMemoryList(BaseModel):
    games: List[GameMemoryOut]


class ClearResponse(BaseModel):
    ok: bool = True


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class HistoryResponse(BaseModel):
    messages: List[MessageOut]
