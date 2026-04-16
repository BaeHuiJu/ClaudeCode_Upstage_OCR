"""
upload.py — POST /api/upload 라우터

파일 검증 → OCR 파싱 → expenses.json 저장 → 파싱된 항목 반환
"""
from fastapi import APIRouter, HTTPException, UploadFile, File

from services.ocr_service import parse_receipt
from services.storage_service import append_expense

router = APIRouter()

# 허용 MIME 타입
ALLOWED_MIME = {"image/jpeg", "image/png", "application/pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/upload")
async def upload_receipt(file: UploadFile = File(...)):
    """영수증 이미지/PDF 업로드 → OCR 파싱 → 저장 → 결과 반환

    Returns:
        저장된 지출 항목 JSON (id, created_at 포함)
    """
    # ── 1. 파일 형식 검증 ───────────────────────────────────────────────────
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식입니다. 허용 형식: JPG, PNG, PDF (현재: {file.content_type})",
        )

    # ── 2. 파일 크기 검증 ───────────────────────────────────────────────────
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"파일 크기가 10MB를 초과합니다. (현재: {len(file_bytes) / 1024 / 1024:.1f}MB)",
        )
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="빈 파일은 업로드할 수 없습니다.")

    # ── 3. OCR 파싱 ─────────────────────────────────────────────────────────
    try:
        parsed = parse_receipt(file_bytes, file.content_type)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"OCR 파싱 실패: {e}")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"영수증 분석 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요. ({type(e).__name__})",
        )

    # ── 4. 파일 경로 기록 ───────────────────────────────────────────────────
    parsed["raw_image_path"] = f"uploads/{file.filename}"

    # ── 5. 저장 → UUID·타임스탬프 부여된 항목 반환 ──────────────────────────
    saved = append_expense(parsed)
    return saved
