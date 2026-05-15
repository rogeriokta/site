import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import init_db
from app.routers import auth, correction

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(correction.router)

Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
Path(settings.processed_dir).mkdir(parents=True, exist_ok=True)
Path("data").mkdir(parents=True, exist_ok=True)

if Path(settings.upload_dir).exists():
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")
if Path(settings.processed_dir).exists():
    app.mount("/processed", StaticFiles(directory=settings.processed_dir), name="processed")


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
