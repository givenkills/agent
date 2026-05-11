from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import User, GameMemory
from schemas import GameMemoryList, GameMemoryOut
from auth import get_current_user
from services.vector_store import vector_store

router = APIRouter(prefix="/api/memories", tags=["memories"])


@router.get("/names", response_model=GameMemoryList)
async def get_memory_names(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GameMemory)
        .where(GameMemory.user_id == user.id)
        .order_by(GameMemory.created_at.desc())
    )
    memories = result.scalars().all()
    return GameMemoryList(
        games=[
            GameMemoryOut(
                id=m.id,
                game_name=m.game_name,
                game_type=m.game_type,
                created_at=m.created_at,
            )
            for m in memories
        ]
    )


@router.get("/search")
async def search_memories(
    q: str = Query(..., min_length=1),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GameMemory)
        .where(GameMemory.user_id == user.id)
        .where(GameMemory.game_name.ilike(f"%{q}%"))
        .order_by(GameMemory.created_at.desc())
        .limit(5)
    )
    memories = result.scalars().all()
    return {
        "games": [
            {
                "id": m.id,
                "game_name": m.game_name,
                "game_type": m.game_type,
                "summary": m.summary_json,
                "created_at": m.created_at.isoformat(),
            }
            for m in memories
        ]
    }


@router.post("/clear")
async def clear_memories(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(delete(GameMemory).where(GameMemory.user_id == user.id))
    await db.commit()
    vector_store.clear_user(user.id)
    return {"ok": True}
