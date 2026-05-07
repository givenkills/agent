import os
import json
import uuid
import threading
from typing import List, Optional, Generator
from dataclasses import dataclass, field
from flask import Flask, Response, request
from flask_cors import CORS
from openai import OpenAI
import chromadb
from chromadb.config import Settings

# ============ 配置 ============

app = Flask(__name__)
CORS(app)

client = OpenAI(
    api_key="sk-289a5ec21aad4116b36cddc316a60184",
    base_url="https://api.deepseek.com"
)

CHROMA_DIR = os.path.join(os.path.dirname(__file__), ".chroma_db")

# ============ 向量数据库 ============

class VectorStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True
        try:
            self._client = chromadb.PersistentClient(
                path=CHROMA_DIR,
                settings=Settings(anonymized_telemetry=False)
            )
            self._collection = self._client.get_or_create_collection(
                name="game_memories",
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            print(f"ChromaDB 初始化失败: {e}")
            self._collection = None

    def add_game_summary(self, game_name: str, summary: str, metadata: dict = None):
        if self._collection is None:
            return
        try:
            doc_id = f"game_{game_name}"
            meta = metadata or {}
            meta["game_name"] = game_name
            meta["summary_json"] = summary
            self._collection.add(
                ids=[doc_id],
                documents=[game_name],
                metadatas=[meta]
            )
        except Exception as e:
            print(f"添加记忆失败: {e}")

    def search_similar(self, query: str, n_results: int = 3) -> List[dict]:
        if self._collection is None:
            return []
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            items = []
            if results["ids"] and results["ids"][0]:
                for i in range(len(results["ids"][0])):
                    meta = results["metadatas"][0][i] if results["metadatas"] else {}
                    items.append({
                        "id": results["ids"][0][i],
                        "game_name": results["documents"][0][i],
                        "summary": meta.get("summary_json", ""),
                        "metadata": meta,
                        "distance": results["distances"][0][i] if results["distances"] else 1.0
                    })
            return items
        except Exception as e:
            print(f"搜索记忆失败: {e}")
            return []

    def get_all_game_names(self) -> List[dict]:
        if self._collection is None:
            return []
        try:
            results = self._collection.get()
            items = []
            if results["ids"]:
                for i in range(len(results["ids"])):
                    meta = results["metadatas"][i] if results["metadatas"] else {}
                    items.append({
                        "id": results["ids"][i],
                        "game_name": meta.get("game_name", "未知"),
                        "game_type": meta.get("game_type", ""),
                        "created_at": meta.get("created_at", "")
                    })
            return items
        except Exception as e:
            print(f"获取游戏列表失败: {e}")
            return []

    def clear(self):
        if self._collection is None:
            return
        try:
            existing = self._collection.get()
            if existing["ids"]:
                self._collection.delete(ids=existing["ids"])
        except Exception:
            pass


vector_store = VectorStore()

# ============ 对话管理 ============

chat_history: List[dict] = []
current_game_name: Optional[str] = None

system_prompt = (
    "生成完整HTML5小游戏,具备基本功能,尺寸正确的游戏,代码简洁紧凑,只能生成html代码,直接输出代码,记住上一次游戏内容,支持修改、优化、微调游戏，不要多余解释文字。"
)

# ============ Agent：判断意图 ============

analysis_prompt = (
    "# 角色"
    "你是一个专业的游戏需求分析器。你的任务是根据用户输入，判断用户是想生成一个全新的游戏，还是对当前游戏添加功能或修改。"
    "# 分类标准"
    "## game（生成新游戏）"
    "用户明确提出了一个具体的游戏类型、玩法机制或游戏名称，意图是创建一个全新的游戏。"
    "典型特征："
    "- 包含具体的游戏类型词（射击、赛车、格斗、益智、策略、模拟、RPG、动作、休闲等）"
    "- 包含具体的游戏名称（五子棋、俄罗斯方块、贪吃蛇、扫雷、2048、Flappy Bird等）"
    "- 包含创建性动词（做一个、生成、创建、开发、写一个、来一个、帮我做个等）"
    "- 描述了一个完整的游戏玩法或规则"
    "## feature（添加功能/修改）"
    "用户在当前游戏基础上要求增加功能、修改玩法、调整参数、美化界面或改变风格。"
    "典型特征："
    "- 只包含风格/主题/颜色词（科技感、复古风、暗黑模式、红色主题、简约风格等）"
    "- 只包含功能词（增加计分、添加音效、优化性能、修复bug、调整速度等）"
    "- 只包含修改词（改一下、换个、调整、优化、改进、美化、继续等）"
    "- 只包含界面词（布局、按钮、颜色、字体、大小、位置等）"
    "# 判断规则（按优先级从高到低）"
    "1. 如果输入中包含具体的游戏类型或游戏名称 → game"
    "2. 如果输入中只有风格/主题/颜色/特效等修饰词，没有具体游戏类型 → feature"
    "3. 如果输入中只有功能/修改/优化相关词 → feature"
    "4. 如果输入模糊不清，无法确定 → feature"
    "# 示例"
    "输入：'做一个射击游戏' → game"
    "输入：'来一个五子棋' → game"
    "输入：'生成俄罗斯方块' → game"
    "输入：'帮我做个赛车游戏' → game"
    "输入：'贪吃蛇' → game"
    "输入：'2048' → game"
    "输入：'科技感风格' → feature"
    "输入：'改成红色主题' → feature"
    "输入：'增加计分功能' → feature"
    "输入：'优化性能' → feature"
    "输入：'换个颜色' → feature"
    "输入：'加个计时器' → feature"
    "输入：'背景改成星空' → feature"
    "输入：'继续' → feature"
    "输入：'改一下' → feature"
    "# 输出"
    "只返回一个词：game 或 feature，不要返回其他任何内容"
)


def judge_intent(user_input: str) -> str:
    try:
        response = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[
                {"role": "system", "content": analysis_prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=0.1,
            max_tokens=10,
            stream=False
        )
        result = response.choices[0].message.content.strip().lower()
        return "game" if "game" in result else "feature"
    except Exception:
        return "feature"


# ============ Agent：压缩游戏摘要 ============

summary_prompt = (
    "你是一个html游戏分析专家。分析以下游戏对话历史，生成一份精简的游戏摘要。"
    "摘要必须包含以下信息，以JSON格式返回（只返回JSON，不要其他文字）："
    "{"
    '  "game_name": "游戏名称（简短，如 太空射击）",'
    '  "game_type": "游戏类型（如射击、休闲、策略等）",'
    '  "features": ["功能1", "功能2", ...],（列出核心功能）'
    '  "customization": "个性化设置描述（如难度、颜色、速度等）",'
    '  "tech_stack": "使用的技术（Canvas/DOM/CSS等）",'
    '  "summary": "一句话概括这个游戏（不超过50字）"'
    "}"
)


def compress_game_summary(history: List[dict]) -> Optional[dict]:
    if not history:
        return None
    try:
        history_text = "".join(
            f"{m['role']}: {m['content'][:500]}" for m in history
        )
        response = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[
                {"role": "system", "content": summary_prompt},
                {"role": "user", "content": f"请分析以下游戏对话历史，生成摘要：\n\n{history_text}"}
            ],
            temperature=0.1,
            stream=False
        )
        result = response.choices[0].message.content.strip()
        if result.startswith("```json"):
            result = result[7:]
        if result.endswith("```"):
            result = result[:-3]
        return json.loads(result.strip())
    except Exception as e:
        print(f"压缩摘要失败: {e}")
        return None


# ============ 构建上下文 ============

def build_context(recalled_summary: Optional[str] = None) -> List[dict]:
    if recalled_summary:
        messages = [{
            "role": "system",
            "content": f"你是专业HTML5游戏工程师。根据以下历史游戏摘要，重新生成该游戏的完整可运行HTML5代码。代码必须紧凑、功能完整、界面美观、可直接运行。\n只输出HTML代码，不要多余解释文字。\n\n历史游戏摘要：\n{recalled_summary}"
        }]
    else:
        messages = [{"role": "system", "content": system_prompt}]
    messages.extend(chat_history)
    return messages


# ============ 路由 ============

@app.route("/api/generate-game", methods=["POST"])
def generate_game():
    global current_game_name

    data = request.get_json()
    prompt = data.get("prompt", "")
    if not prompt:
        return {"error": "请输入游戏描述"}, 400

    # 判断意图
    intent = judge_intent(prompt)

    recalled_summary = None

    if intent == "game":
        if chat_history:
            summary_data = compress_game_summary(chat_history)
            if summary_data:
                game_name = summary_data.get("game_name", "未命名游戏")
                summary_text = json.dumps(summary_data, ensure_ascii=False)
                vector_store.add_game_summary(
                    game_name=game_name,
                    summary=summary_text,
                    metadata={
                        "game_name": game_name,
                        "game_type": summary_data.get("game_type", "")
                    }
                )
                print(f"已存档游戏: {game_name}")

            chat_history.clear()
            current_game_name = None

        similar = vector_store.search_similar(prompt, n_results=1)
        if similar:
            distance = similar[0].get("distance", 1.0)
            cosine_similarity = 1 - distance
            matched_name = similar[0].get("game_name", "未知")
            if cosine_similarity > 0.8:
                recalled_summary = similar[0].get("summary", "")
                print(f"召回历史游戏: {matched_name} (名称相似度: {cosine_similarity:.2f})")
            else:
                print(f"无相似游戏(名称相似度: {cosine_similarity:.2f})，视为新游戏")

    # 添加用户输入到对话
    chat_history.append({"role": "user", "content": prompt})

    def stream():
        nonlocal recalled_summary

        # 构建消息
        messages = build_context(recalled_summary=recalled_summary)

        response = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=messages,
            temperature=0.2,
            stream=True
        )
        full_content = ""
        for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta:
                full_content += delta
                yield delta

        # 保存 AI 回复到对话历史
        chat_history.append({"role": "assistant", "content": full_content})

    return Response(stream(), content_type="text/html; charset=utf-8")


@app.route("/api/clear", methods=["POST"])
def clear():
    chat_history.clear()
    vector_store.clear()
    return {"ok": True}


@app.route("/api/memories", methods=["GET"])
def get_memories():
    """查看所有已存档的游戏记忆（调试用）"""
    try:
        if vector_store._collection is None:
            return {"memories": []}
        results = vector_store._collection.get()
        memories = []
        if results["ids"]:
            for i in range(len(results["ids"])):
                meta = results["metadatas"][i] if results["metadatas"] else {}
                memories.append({
                    "id": results["ids"][i],
                    "game_name": meta.get("game_name", "未知"),
                    "summary": results["documents"][i][:200] + "..." if len(results["documents"][i]) > 200 else results["documents"][i]
                })
        return {"memories": memories}
    except Exception as e:
        return {"memories": [], "error": str(e)}


@app.route("/api/memories/names", methods=["GET"])
def get_memory_names():
    """获取所有已存档的游戏名称列表"""
    try:
        games = vector_store.get_all_game_names()
        return {"games": games}
    except Exception as e:
        return {"games": [], "error": str(e)}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
