#!/usr/bin/env python3
"""
PRD 자동 업데이트 스크립트 (PostToolUse Hook 보조)

기능:
  1. 소스 파일 경로 → Phase 태스크 ID 매핑 후 해당 행에 ✅ 표시
  2. backend/requirements.txt 변경 시 PRD 내 코드 블록 내용 동기화
  3. PRD 문서 버전/날짜 자동 갱신

사용:
  python3 update_prd.py <changed_file_path> <prd_file_path> <project_root>
"""

import sys
import re
import os
from datetime import date


# ─────────────────────────────────────────────────────────────────────────────
# 파일 경로 → PRD Phase 태스크 ID 매핑 테이블
# 키: 파일의 상대 경로 접미사 (project root 기준)
# 값: PRD 태스크 ID (테이블 첫 번째 열 값)
# ─────────────────────────────────────────────────────────────────────────────
FILE_TASK_MAP = [
    # Phase 1 — 프로젝트 환경 설정
    ('.gitignore',                                '1-1'),
    ('backend/requirements.txt',                  '1-4'),
    ('backend/.env',                              '1-3'),
    ('.env.example',                              '1-3'),
    # Phase 2 — 백엔드 핵심 API (OCR 업로드)
    ('backend/main.py',                           '2-1-1'),
    ('backend/data/expenses.json',                '2-1-2'),
    ('backend/services/storage_service.py',       '2-2-1'),
    ('backend/services/ocr_service.py',           '2-3-1'),
    ('backend/routers/upload.py',                 '2-4-1'),
    # Phase 3 — 백엔드 부가 API
    ('backend/routers/expenses.py',               '3-1-1'),
    ('backend/routers/summary.py',                '3-2-1'),
    # Phase 4 — 프론트엔드 환경 설정
    ('frontend/package.json',                     '4-1'),
    ('frontend/vite.config.js',                   '4-1'),
    ('frontend/tailwind.config.js',               '4-2'),
    ('frontend/postcss.config.js',                '4-2'),
    ('frontend/src/api/axios.js',                 '4-4'),
    ('frontend/src/App.jsx',                      '4-5'),
    ('frontend/index.html',                       '4-6'),
    # Phase 5 — 업로드 화면 구현
    ('frontend/src/components/Header.jsx',        '5-1-1'),
    ('frontend/src/components/Toast.jsx',         '5-1-2'),
    ('frontend/src/components/Badge.jsx',         '5-1-3'),
    ('frontend/src/components/DropZone.jsx',      '5-2-1'),
    ('frontend/src/components/ProgressBar.jsx',   '5-2-2'),
    ('frontend/src/components/ParsePreview.jsx',  '5-2-3'),
    ('frontend/src/pages/UploadPage.jsx',         '5-3-1'),
    # Phase 6 — 대시보드 화면 구현
    ('frontend/src/components/SummaryCard.jsx',   '6-1-1'),
    ('frontend/src/components/FilterBar.jsx',     '6-1-2'),
    ('frontend/src/components/ExpenseCard.jsx',   '6-1-3'),
    ('frontend/src/pages/Dashboard.jsx',          '6-2-1'),
    # Phase 7 — 지출 상세/수정 화면 구현
    ('frontend/src/components/Modal.jsx',         '7-1'),
    ('frontend/src/components/ReceiptImage.jsx',  '7-2'),
    ('frontend/src/components/EditForm.jsx',      '7-3'),
    ('frontend/src/pages/ExpenseDetail.jsx',      '7-4'),
    # Phase 8 — 배포 및 E2E 검증
    ('vercel.json',                               '8-1-1'),
]


def normalize_path(file_path: str, project_root: str) -> str:
    """절대 경로를 프로젝트 루트 기준 상대 경로로 정규화"""
    # 백슬래시 → 슬래시
    norm = file_path.replace('\\', '/')
    root = project_root.replace('\\', '/').rstrip('/')

    # 알려진 루트 접두사 제거
    candidates = [
        root + '/',
        root.lower() + '/',
        '/d/huiju_vibeCoding/claude_ocr_1day/',
        'd:/huiju_vibeCoding/claude_ocr_1day/',
    ]
    for prefix in candidates:
        if norm.lower().startswith(prefix.lower()):
            norm = norm[len(prefix):]
            break

    return norm.lstrip('/')


def update_requirements_block(content: str, project_root: str) -> str:
    """PRD 내 requirements.txt 코드 블록을 실제 파일 내용으로 동기화"""
    req_path = os.path.join(project_root, 'backend', 'requirements.txt')
    if not os.path.exists(req_path):
        return content

    with open(req_path, 'r', encoding='utf-8') as f:
        req_content = f.read().rstrip()

    pattern = r'(#### requirements\.txt\n\n```txt\n)([\s\S]*?)(```)'

    def replacer(m):
        return m.group(1) + req_content + '\n' + m.group(3)

    return re.sub(pattern, replacer, content)


def mark_task_complete(content: str, task_id: str) -> str:
    """PRD 테이블에서 해당 태스크 행의 ID 셀에 ✅ 추가"""
    lines = content.split('\n')
    new_lines = []
    pattern = re.compile(r'^(\|\s*)(' + re.escape(task_id) + r')(\s*\|)')

    for line in lines:
        stripped = line.strip()
        # 테이블 행이고, task_id로 시작하며, 아직 ✅ 없는 경우
        if stripped.startswith('|') and re.match(r'^\|\s*' + re.escape(task_id) + r'\s*\|', stripped):
            if '✅' not in line:
                line = pattern.sub(r'\g<1>\g<2> ✅\g<3>', line)
        new_lines.append(line)

    return '\n'.join(new_lines)


def update_prd_version(content: str) -> str:
    """PRD 상단 문서 개요 테이블의 문서 버전·수정일 자동 갱신"""
    today = date.today().strftime('%Y-%m-%d')

    # 수정일 행 업데이트 (있을 경우)
    content = re.sub(
        r'(\| 수정일\s*\|\s*)([^\|]+)(\|)',
        lambda m: m.group(1) + today + ' ' + m.group(3),
        content
    )
    return content


def main():
    if len(sys.argv) < 3:
        sys.exit(0)

    file_path   = sys.argv[1]
    prd_file    = sys.argv[2]
    project_root = sys.argv[3] if len(sys.argv) >= 4 else os.path.dirname(prd_file)

    rel_path = normalize_path(file_path, project_root)

    with open(prd_file, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # 1. requirements.txt 코드 블록 동기화
    if rel_path in ('backend/requirements.txt', 'requirements.txt'):
        content = update_requirements_block(content, project_root)

    # 2. 파일 → 태스크 ID 매핑 후 ✅ 표시
    task_id = None
    for suffix, tid in FILE_TASK_MAP:
        if rel_path == suffix or rel_path.endswith('/' + suffix):
            task_id = tid
            break

    if task_id:
        content = mark_task_complete(content, task_id)

    # 3. 변경이 있을 때만 파일 저장
    if content != original:
        with open(prd_file, 'w', encoding='utf-8') as f:
            f.write(content)
        msg_parts = [f"[PRD Hook] PRD 업데이트 완료 → {rel_path}"]
        if task_id:
            msg_parts.append(f"태스크 {task_id} ✅ 표시")
        print(' | '.join(msg_parts), file=sys.stderr)
    else:
        print(f"[PRD Hook] 변경 없음 (매핑되지 않은 파일): {rel_path}", file=sys.stderr)


if __name__ == '__main__':
    main()
