import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import User, ChatMessage, GameMemory
from schemas import GenerateGameRequest, HistoryResponse, ClearResponse
from auth import get_current_user
from services.ai_service import (
    judge_intent,
    compress_game_summary,
    build_messages,
    stream_game_response,
)
from services.vector_store import vector_store

router = APIRouter(prefix="/api", tags=["game"])


async def _get_chat_history(user_id: str, db: AsyncSession) -> List[dict]:
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = result.scalars().all()
    return [{"role": m.role, "content": m.content, "id": m.id, "created_at": m.created_at} for m in messages]


async def _clear_chat_history(user_id: str, db: AsyncSession):
    await db.execute(delete(ChatMessage).where(ChatMessage.user_id == user_id))
    await db.commit()


async def _save_message(user_id: str, role: str, content: str, db: AsyncSession):
    msg = ChatMessage(user_id=user_id, role=role, content=content)
    db.add(msg)
    await db.commit()


async def _search_similar_games(user_id: str, query: str, db: AsyncSession):
    similar = vector_store.search_similar(user_id, query, n_results=1)
    if similar:
        distance = similar[0].get("distance", 1.0)
        cosine_similarity = 1 - distance
        if cosine_similarity > 0.8:
            return similar[0]
    return None


@router.post("/generate-game")
async def generate_game(
    body: GenerateGameRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    prompt = body.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="请输入游戏描述")

    intent = judge_intent(prompt)

    history = await _get_chat_history(user.id, db)
    history_for_ai = [{"role": h["role"], "content": h["content"]} for h in history]

    recalled_summary = None

    if intent == "game":
        if history:
            summary_data = compress_game_summary(history_for_ai)
            if summary_data:
                game_name = summary_data.get("game_name", "未命名游戏")
                summary_text = json.dumps(summary_data, ensure_ascii=False)

                existing = await db.execute(
                    select(GameMemory).where(
                        GameMemory.user_id == user.id,
                        GameMemory.game_name == game_name,
                    )
                )
                existing_memory = existing.scalar_one_or_none()

                if existing_memory:
                    existing_memory.summary_json = summary_text
                    existing_memory.game_type = summary_data.get("game_type", "")
                    print(f"更新已存档游戏: {game_name} (用户: {user.username})")
                else:
                    memory = GameMemory(
                        user_id=user.id,
                        game_name=game_name,
                        game_type=summary_data.get("game_type", ""),
                        summary_json=summary_text,
                    )
                    db.add(memory)
                    print(f"已存档游戏: {game_name} (用户: {user.username})")

                await db.commit()

                vector_store.upsert_game_summary(
                    user_id=user.id,
                    game_name=game_name,
                    summary=summary_text,
                    metadata={
                        "game_name": game_name,
                        "game_type": summary_data.get("game_type", ""),
                    },
                )

            await _clear_chat_history(user.id, db)
            history_for_ai = []

        similar = await _search_similar_games(user.id, prompt, db)
        if similar:
            recalled_summary = similar.get("summary", "")
            print(f"召回历史游戏: {similar.get('game_name')} (用户: {user.username})")

    await _save_message(user.id, "user", prompt, db)

    if recalled_summary:
        messages_for_ai = build_messages(history_for_ai, recalled_summary=recalled_summary, current_prompt=prompt)
    else:
        messages_for_ai = build_messages(history_for_ai, current_prompt=prompt)

    full_content = []

    async def event_stream():
        nonlocal full_content
        for chunk in stream_game_response(messages_for_ai):
            full_content.append(chunk)
            yield chunk

        content = "".join(full_content)
        if content:
            await _save_message(user.id, "assistant", content, db)

    return StreamingResponse(event_stream(), media_type="text/html; charset=utf-8")


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    history = await _get_chat_history(user.id, db)
    return HistoryResponse(messages=history)


@router.post("/clear", response_model=ClearResponse)
async def clear_chat(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _clear_chat_history(user.id, db)
    return ClearResponse(ok=True)
