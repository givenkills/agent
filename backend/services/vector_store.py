import os
from typing import List, Optional
import chromadb
from chromadb.config import Settings

CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".chroma_db")


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
                settings=Settings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_or_create_collection(
                name="game_memories",
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as e:
            print(f"ChromaDB 初始化失败: {e}")
            self._collection = None

    def add_game_summary(self, user_id: str, game_name: str, summary: str, metadata: dict = None):
        if self._collection is None:
            return
        try:
            doc_id = f"user_{user_id}_{game_name}"
            meta = metadata or {}
            meta["user_id"] = user_id
            meta["game_name"] = game_name
            meta["summary_json"] = summary
            self._collection.add(ids=[doc_id], documents=[summary], metadatas=[meta])
        except Exception as e:
            print(f"添加记忆失败: {e}")

    def upsert_game_summary(self, user_id: str, game_name: str, summary: str, metadata: dict = None):
        if self._collection is None:
            return
        try:
            doc_id = f"user_{user_id}_{game_name}"
            meta = metadata or {}
            meta["user_id"] = user_id
            meta["game_name"] = game_name
            meta["summary_json"] = summary
            self._collection.upsert(ids=[doc_id], documents=[summary], metadatas=[meta])
        except Exception as e:
            print(f"更新记忆失败: {e}")

    def search_similar(self, user_id: str, query: str, n_results: int = 3) -> List[dict]:
        if self._collection is None:
            return []
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
                where={"user_id": user_id},
            )
            items = []
            if results["ids"] and results["ids"][0]:
                for i in range(len(results["ids"][0])):
                    meta = results["metadatas"][0][i] if results["metadatas"] else {}
                    items.append(
                        {
                            "id": results["ids"][0][i],
                            "game_name": meta.get("game_name", ""),
                            "summary": meta.get("summary_json", ""),
                            "metadata": meta,
                            "distance": results["distances"][0][i] if results["distances"] else 1.0,
                        }
                    )
            return items
        except Exception as e:
            print(f"搜索记忆失败: {e}")
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

    def clear_user(self, user_id: str):
        if self._collection is None:
            return
        try:
            existing = self._collection.get(where={"user_id": user_id})
            if existing["ids"]:
                self._collection.delete(ids=existing["ids"])
        except Exception:
            pass


vector_store = VectorStore()
