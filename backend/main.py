import os
import sys
from pathlib import Path

# uvicorn backend.main:app 으로 실행 시 backend/ 를 모듈 검색 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

load_dotenv()

app = FastAPI(title="Receipt Expense Tracker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 업로드 디렉토리 자동 생성
UPLOADS_DIR = Path(__file__).parent / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

# expenses.json 초기화
DATA_FILE = Path(os.getenv("DATA_FILE_PATH", "backend/data/expenses.json"))
if not DATA_FILE.exists():
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text("[]", encoding="utf-8")

# 라우터 등록
from routers import upload, expenses, summary

app.include_router(upload.router, prefix="/api")
app.include_router(expenses.router, prefix="/api")
app.include_router(summary.router, prefix="/api")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Receipt Expense Tracker API is running"}
