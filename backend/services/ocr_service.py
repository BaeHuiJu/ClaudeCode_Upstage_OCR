"""
ocr_service.py — Upstage OCR + LangChain 기반 영수증 파싱 서비스

파이프라인:
  1. Pillow / pdf2image 로 파일 전처리 → 표준 JPEG 변환
  2. Upstage Document Digitization API (POST /v1/document-digitization) → OCR 텍스트 추출
  3. LangChain: ChatUpstage(solar-pro) + ChatPromptTemplate + JsonOutputParser → 구조화 JSON
"""
import io
import os
import requests
from PIL import Image
from pdf2image import convert_from_bytes
from langchain_upstage import ChatUpstage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# ─────────────────────────────────────────────────────────────────────────────
# 상수
# ─────────────────────────────────────────────────────────────────────────────
UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY", "")
UPSTAGE_OCR_URL = "https://api.upstage.ai/v1/document-digitization"
OCR_TIMEOUT_SEC = 30

SYSTEM_PROMPT = """당신은 영수증 OCR 전문가입니다.
주어진 영수증 텍스트에서 아래 JSON 형식으로만 응답하세요. 다른 텍스트나 마크다운 코드블록은 포함하지 마세요.
추출할 수 없는 값은 null로 설정하세요. 날짜는 YYYY-MM-DD, 시간은 HH:MM 형식으로 표준화하세요.
금액은 숫자(int)만 입력하고 통화 기호·쉼표는 제거하세요.

{
  "store_name": "string",
  "receipt_date": "YYYY-MM-DD",
  "receipt_time": "HH:MM or null",
  "category": "식료품|외식|교통|쇼핑|의료|기타",
  "items": [
    {"name": "string", "quantity": 1, "unit_price": 0, "total_price": 0}
  ],
  "subtotal": 0,
  "discount": 0,
  "tax": 0,
  "total_amount": 0,
  "payment_method": "string or null"
}"""

USER_PROMPT = """다음은 영수증에서 추출한 텍스트입니다. JSON 형식으로 파싱해 주세요:

{ocr_text}"""


# ─────────────────────────────────────────────────────────────────────────────
# 이미지 전처리
# ─────────────────────────────────────────────────────────────────────────────
def _preprocess_to_jpeg(file_bytes: bytes, content_type: str) -> bytes:
    """파일을 JPEG 바이트로 변환 (PDF → 1페이지 이미지, 이미지 → RGB JPEG)"""
    if content_type == "application/pdf":
        images = convert_from_bytes(file_bytes, first_page=1, last_page=1, dpi=150)
        img = images[0]
    else:
        img = Image.open(io.BytesIO(file_bytes))
        if img.mode != "RGB":
            img = img.convert("RGB")

    # 최대 해상도 제한 (OCR 품질 유지하면서 API 전송 크기 최적화)
    MAX_PX = 2048
    if max(img.size) > MAX_PX:
        img.thumbnail((MAX_PX, MAX_PX), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# Upstage Document Digitization OCR
# ─────────────────────────────────────────────────────────────────────────────
def _extract_ocr_text(jpeg_bytes: bytes) -> str:
    """Upstage Document Digitization API로 JPEG → 텍스트 추출"""
    headers = {"Authorization": f"Bearer {UPSTAGE_API_KEY}"}
    files = {"document": ("receipt.jpg", io.BytesIO(jpeg_bytes), "image/jpeg")}
    data = {"model": "ocr"}

    resp = requests.post(
        UPSTAGE_OCR_URL, headers=headers, files=files, data=data,
        timeout=OCR_TIMEOUT_SEC,
    )
    resp.raise_for_status()

    pages = resp.json().get("pages", [])
    text = "\n".join(page.get("text", "") for page in pages).strip()
    return text


# ─────────────────────────────────────────────────────────────────────────────
# LangChain Chain (모듈 로드 시 1회 초기화)
# ─────────────────────────────────────────────────────────────────────────────
def _build_chain():
    llm = ChatUpstage(model="solar-pro")
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", USER_PROMPT),
    ])
    return prompt | llm | JsonOutputParser()

_chain = None  # 지연 초기화 (API 키 로드 후 사용)


def _get_chain():
    global _chain
    if _chain is None:
        _chain = _build_chain()
    return _chain


# ─────────────────────────────────────────────────────────────────────────────
# 공개 인터페이스
# ─────────────────────────────────────────────────────────────────────────────
def parse_receipt(file_bytes: bytes, content_type: str) -> dict:
    """영수증 파일 파싱 → 구조화 JSON dict 반환

    Args:
        file_bytes:   업로드된 파일 원본 바이트
        content_type: MIME 타입 (image/jpeg | image/png | application/pdf)

    Returns:
        구조화된 영수증 dict (store_name, receipt_date, items, total_amount 등)

    Raises:
        ValueError:  OCR 텍스트 추출 실패
        requests.HTTPError: Upstage API 오류
    """
    # 1. 전처리 → JPEG
    jpeg_bytes = _preprocess_to_jpeg(file_bytes, content_type)

    # 2. OCR 텍스트 추출
    ocr_text = _extract_ocr_text(jpeg_bytes)
    if not ocr_text:
        raise ValueError("OCR 텍스트 추출 실패: 빈 결과가 반환되었습니다.")

    # 3. LangChain으로 구조화 JSON 파싱
    result = _get_chain().invoke({"ocr_text": ocr_text})
    return result
