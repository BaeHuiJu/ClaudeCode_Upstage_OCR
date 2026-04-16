#!/bin/bash
# =============================================================================
# PRD 자동 업데이트 PostToolUse Hook
# 트리거: Edit / Write 도구 실행 후
# 동작:   변경된 소스 파일에 대응하는 PRD Phase 태스크에 ✅ 표시
#         requirements.txt 변경 시 PRD 내 코드 블록도 자동 동기화
# =============================================================================

# stdin 에서 hook JSON 읽기
INPUT=$(cat)

# tool_name 추출
TOOL_NAME=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_name', ''))
except Exception:
    print('')
" 2>/dev/null)

# Edit / Write 이외 이벤트는 무시
[[ "$TOOL_NAME" != "Edit" && "$TOOL_NAME" != "Write" ]] && exit 0

# file_path 추출 (Edit: file_path, Write: file_path)
FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    inp = d.get('tool_input', {})
    print(inp.get('file_path', inp.get('path', '')))
except Exception:
    print('')
" 2>/dev/null)

# 파일 경로가 비어 있으면 종료
[[ -z "$FILE_PATH" ]] && exit 0

# PRD 파일 자체가 수정되는 경우는 무시 (무한 루프 방지)
[[ "$FILE_PATH" == *"PRD_"* ]] && exit 0

# 스크립트 위치 기준으로 프로젝트 루트 계산
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

PRD_FILE="$PROJECT_ROOT/PRD_영수증_지출관리앱.md"

[[ ! -f "$PRD_FILE" ]] && exit 0

# Python 스크립트로 실제 PRD 업데이트 수행
python3 "$SCRIPT_DIR/update_prd.py" "$FILE_PATH" "$PRD_FILE" "$PROJECT_ROOT"

exit 0
