#!/bin/bash
#
# Git hooks 설치 스크립트
#
# 이 스크립트는 .githooks 디렉토리의 훅을 .git/hooks로 심볼릭 링크합니다.
# UTF-8 인코딩 검증 pre-commit hook을 포함합니다.
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Git Hooks 설치${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Get script directory (project root)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
GIT_HOOKS_DIR="$PROJECT_ROOT/.git/hooks"
CUSTOM_HOOKS_DIR="$PROJECT_ROOT/.githooks"

# Check if .git directory exists
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo "❌ 오류: .git 디렉토리를 찾을 수 없습니다."
    echo "   이 스크립트는 git 저장소 루트에서 실행해야 합니다."
    exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p "$GIT_HOOKS_DIR"

# Install pre-commit hook
echo "📦 pre-commit hook 설치 중..."

# Remove existing hook or symlink
if [ -e "$GIT_HOOKS_DIR/pre-commit" ] || [ -L "$GIT_HOOKS_DIR/pre-commit" ]; then
    echo "   기존 pre-commit hook 제거 중..."
    rm -f "$GIT_HOOKS_DIR/pre-commit"
fi

# Create symlink
ln -s "$CUSTOM_HOOKS_DIR/pre-commit" "$GIT_HOOKS_DIR/pre-commit"
chmod +x "$GIT_HOOKS_DIR/pre-commit"

echo -e "   ${GREEN}✅ pre-commit hook 설치 완료${NC}"
echo ""

# Summary
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}설치 완료!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "설치된 hooks:"
echo "  ✓ pre-commit: UTF-8 인코딩 검증 (T303, FR-115)"
echo ""
echo "이제 git commit 시 자동으로 UTF-8 인코딩을 검증합니다."
echo "한글 텍스트 인코딩 손상을 방지하여 T302와 같은 문제를 예방합니다."
echo ""
