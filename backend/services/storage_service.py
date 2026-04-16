"""
storage_service.py — expenses.json 읽기/쓰기 서비스
"""
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path


def _get_data_file() -> Path:
    """환경에 따라 데이터 파일 경로 반환"""
    if os.getenv("VERCEL") == "1":
        return Path("/tmp/expenses.json")
    return Path(os.getenv("DATA_FILE_PATH", "backend/data/expenses.json"))


def _ensure_file(path: Path) -> None:
    """파일이 없으면 빈 배열로 초기화"""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("[]", encoding="utf-8")


def load_expenses() -> list:
    """expenses.json 전체 읽기 → 리스트 반환"""
    path = _get_data_file()
    _ensure_file(path)
    return json.loads(path.read_text(encoding="utf-8"))


def save_expenses(data: list) -> None:
    """리스트 → expenses.json 덮어쓰기"""
    path = _get_data_file()
    _ensure_file(path)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def append_expense(item: dict) -> dict:
    """UUID·타임스탬프 부여 후 expenses.json에 추가 저장 → 저장된 항목 반환"""
    item["id"] = str(uuid.uuid4())
    item["created_at"] = datetime.now(timezone.utc).isoformat()
    expenses = load_expenses()
    expenses.append(item)
    save_expenses(expenses)
    return item
