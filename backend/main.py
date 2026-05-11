from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from middleware.rate_limit import init_redis, close_redis, rate_limit_middleware
from routes.auth_routes import router as auth_router
from routes.game_routes import router as game_router
from routes.memory_routes import router as memory_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_redis()
    yield
    await close_redis()


app = FastAPI(title="AI Game Generator", version="2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(rate_limit_middleware)

app.include_router(auth_router)
app.include_router(game_router)
app.include_router(memory_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
