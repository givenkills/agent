"""端到端测试：模拟完整多轮对话流程"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from services.ai_service import judge_intent, compress_game_summary


def test_judge_intent():
    print("\n" + "=" * 60)
    print("1. 测试意图判断 (judge_intent)")
    print("=" * 60)

    cases = [
        ("帮我做一个五子棋游戏", "game"),
        ("做贪吃蛇", "game"),
        ("生成俄罗斯方块", "game"),
        ("帮我做个射击游戏", "game"),
        ("改成红色主题", "feature"),
        ("增加人机对战功能", "feature"),
        ("优化性能", "feature"),
        ("加快游戏速度", "feature"),
    ]

    all_pass = True
    for prompt, expected in cases:
        result = judge_intent(prompt)
        status = "✅" if result == expected else "❌"
        if result != expected:
            all_pass = False
        print(f"  {status} 输入: '{prompt}' → {result} (期望: {expected})")

    return all_pass


def test_compress_summary():
    print("\n" + "=" * 60)
    print("2. 测试摘要压缩 (compress_game_summary)")
    print("=" * 60)

    # 模拟五子棋 → 改成红色 的完整历史
    history = [
        {"role": "user", "content": "帮我做一个五子棋游戏"},
        {"role": "assistant", "content": "<html><body>五子棋游戏完整代码...</body></html>"},
        {"role": "user", "content": "改成红色主题"},
        {"role": "assistant", "content": "<html><body>红色主题五子棋代码...</body></html>"},
    ]

    summary = compress_game_summary(history)
    if summary is None:
        print("  ❌ compress_game_summary 返回 None")
        return False

    required_keys = ["game_name", "game_type", "features", "summary"]
    for key in required_keys:
        if key not in summary:
            print(f"  ❌ 缺少必要字段: {key}")
            return False

    print(f"  ✅ game_name: {summary['game_name']}")
    print(f"  ✅ game_type: {summary['game_type']}")
    print(f"  ✅ features ({len(summary['features'])}项): {summary['features']}")
    print(f"  ✅ summary: {summary['summary']}")

    if "红色" in str(summary) or "红" in str(summary):
        print(f'  ✅ 包含颜色特征: {"红色主题" in str(summary) or "红" in str(summary)}')

    return True


def test_full_conversation_flow():
    print("\n" + "=" * 60)
    print("3. 模拟完整对话流程 (使用真实数据库)")
    print("=" * 60)

    import asyncio
    import bcrypt
    from datetime import datetime
    from sqlalchemy import select, delete
    from database import AsyncSessionLocal, init_db
    from models import User, ChatMessage, GameMemory
    from services.vector_store import vector_store

    async def run():
        await init_db()
        async with AsyncSessionLocal() as db:
            # --- 准备测试用户 ---
            result = await db.execute(
                select(User).where(User.username == "e2e_test_user")
            )
            user = result.scalar_one_or_none()
            if user is None:
                user = User(
                    username="e2e_test_user",
                    password_hash=bcrypt.hashpw(b"test123", bcrypt.gensalt()).decode(),
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
            print(f"\n  测试用户: {user.username}")

            async def add_msg(role, content):
                db.add(ChatMessage(user_id=user.id, role=role, content=content))
                await db.commit()

            async def get_history():
                rows = await db.execute(
                    select(ChatMessage)
                    .where(ChatMessage.user_id == user.id)
                    .order_by(ChatMessage.created_at.asc())
                )
                msgs = rows.scalars().all()
                return [{"role": m.role, "content": m.content} for m in msgs]

            # ========== 第1轮：做五子棋 ==========
            print("\n  --- 第1轮: '帮我做一个五子棋游戏' ---")
            intent1 = judge_intent("帮我做一个五子棋游戏")
            print(f"  意图判断: {intent1}")
            if intent1 != "game":
                print("  ❌ 意图应该为 game")
                return False

            await add_msg("user", "帮我做一个五子棋游戏")
            await add_msg("assistant", "<html><body>五子棋游戏代码...</body></html>")

            # ========== 第2轮：改成红色 ==========
            print("\n  --- 第2轮: '改成红色主题' ---")
            intent2 = judge_intent("改成红色主题")
            print(f"  意图判断: {intent2}")
            if intent2 != "feature":
                print("  ❌ 意图应该为 feature")
                return False

            await add_msg("user", "改成红色主题")
            await add_msg("assistant", "<html><body>红色主题五子棋代码...</body></html>")

            # ========== 第3轮：做贪吃蛇（应触发存档） ==========
            print("\n  --- 第3轮: '做贪吃蛇'（应触发存档） ---")
            intent3 = judge_intent("做贪吃蛇")
            print(f"  意图判断: {intent3}")
            if intent3 != "game":
                print("  ❌ 意图应该为 game")
                return False

            # 获取历史并压缩摘要
            history = await get_history()
            print(f"  对话历史: {len(history)} 条 (user: {len([h for h in history if h['role']=='user'])} 条)")

            summary_data = compress_game_summary(history)
            if summary_data is None:
                print("  ❌ compress_game_summary 返回 None")
                return False
            print(f"  摘要生成: {summary_data['game_name']} ({summary_data['game_type']}) - {summary_data['summary']}")

            # 保存到 SQLite
            game_name = summary_data["game_name"]
            summary_text = json.dumps(summary_data, ensure_ascii=False)
            memory = GameMemory(
                user_id=user.id,
                game_name=game_name,
                game_type=summary_data.get("game_type", ""),
                summary_json=summary_text,
            )
            db.add(memory)
            await db.commit()
            print(f"  ✅ 写入 SQLite: {game_name}")

            # 保存到 ChromaDB
            vector_store.upsert_game_summary(
                user_id=user.id,
                game_name=game_name,
                summary=summary_text,
                metadata={
                    "game_name": game_name,
                    "game_type": summary_data.get("game_type", ""),
                },
            )
            print(f"  ✅ 写入 ChromaDB")

            # 清除旧对话历史（模拟存档后的行为）
            await db.execute(delete(ChatMessage).where(ChatMessage.user_id == user.id))
            await db.commit()

            # ========== 验证存档 ==========
            print("\n  --- 验证存档 ---")

            # SQLite 验证
            result = await db.execute(
                select(GameMemory).where(GameMemory.user_id == user.id).order_by(GameMemory.created_at.desc())
            )
            memories = result.scalars().all()
            print(f"  SQLite game_memories: {len(memories)} 条")
            for m in memories:
                loaded = json.loads(m.summary_json)
                print(f"    - {m.game_name} | {m.game_type} | features: {len(loaded.get('features', []))}项")

            if len(memories) == 0:
                print("  ❌ SQLite 中没有存档")
                return False

            # ChromaDB 验证
            results = vector_store.search_similar(user.id, "五子棋", n_results=5)
            print(f"  ChromaDB 搜'五子棋': {len(results)} 条")
            for r in results:
                print(f"    - {r.get('game_name')} (distance={r.get('distance', 'N/A')})")

            results2 = vector_store.search_similar(user.id, "贪吃蛇", n_results=5)
            print(f"  ChromaDB 搜'贪吃蛇': {len(results2)} 条")
            for r in results2:
                print(f"    - {r.get('game_name')} (distance={r.get('distance', 'N/A')})")

            # Memories API 验证 (模拟 memory_routes.py)
            result = await db.execute(
                select(GameMemory)
                .where(GameMemory.user_id == user.id)
                .order_by(GameMemory.created_at.desc())
            )
            api_memories = result.scalars().all()
            memory_list = [
                {
                    "id": m.id,
                    "game_name": m.game_name,
                    "game_type": m.game_type,
                    "created_at": m.created_at.isoformat(),
                }
                for m in api_memories
            ]
            print(f"  /api/memories/names 返回: {len(memory_list)} 条")
            for m in memory_list:
                print(f"    - {m['game_name']} ({m['game_type']})")

            if len(memory_list) == 0:
                print("  ❌ 存档页面 API 返回为空")
                return False

            # ========== 清理测试数据 ==========
            await db.execute(delete(GameMemory).where(GameMemory.user_id == user.id))
            await db.execute(delete(ChatMessage).where(ChatMessage.user_id == user.id))
            await db.execute(delete(User).where(User.id == user.id))
            await db.commit()
            vector_store.clear_user(user.id)
            print("\n  ✅ 测试数据已清理")

            return True

    result = asyncio.run(run())
    return result


if __name__ == "__main__":
    results = []

    print("\n" + "=" * 60)
    print("AI 游戏存档系统 - 端到端测试")
    print("=" * 60)

    results.append(("意图判断 (judge_intent)", test_judge_intent()))
    results.append(("摘要压缩 (compress_game_summary)", test_compress_summary()))
    results.append(("完整对话流程 (SQLite + ChromaDB)", test_full_conversation_flow()))

    print("\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)
    all_pass = True
    for name, ok in results:
        status = "✅ 通过" if ok else "❌ 失败"
        print(f"  {status}: {name}")
        if not ok:
            all_pass = False

    print(f"\n结论: {'✅ 全部通过' if all_pass else '❌ 有失败项'}")
    sys.exit(0 if all_pass else 1)
