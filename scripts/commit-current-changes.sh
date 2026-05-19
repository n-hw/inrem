#!/usr/bin/env bash
#
# commit-current-changes.sh
# ──────────────────────────────────────────────────────────────────────
# 2026-05-19 작업분(문서 4종 + Heritage Box 백엔드/프론트 + CHANGELOG)을
# 의미 단위로 4개 커밋으로 나눠 저장합니다.
#
# 사용:
#   cd ~/Desktop/project/InRem
#   bash scripts/commit-current-changes.sh
#
# 사전 조건:
#   - git user.name / user.email 이 설정되어 있어야 함
#     (없으면 아래 GIT_USER_NAME / GIT_USER_EMAIL 환경변수로 한 번만 주입 가능)
# ──────────────────────────────────────────────────────────────────────

set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

# ── 0) git identity 확인 / 주입 ──────────────────────────────────────
if ! git config user.email > /dev/null; then
  if [[ -n "${GIT_USER_EMAIL:-}" ]]; then
    git config user.email "$GIT_USER_EMAIL"
  else
    echo "❌  git user.email 이 설정되어 있지 않습니다."
    echo "    git config user.email \"hanjung1579@gmail.com\""
    echo "    git config user.name  \"hw\""
    echo "    또는 GIT_USER_EMAIL=... GIT_USER_NAME=... 환경변수로 다시 실행하세요."
    exit 1
  fi
fi
if ! git config user.name > /dev/null; then
  git config user.name "${GIT_USER_NAME:-hw}"
fi

echo "👤  $(git config user.name) <$(git config user.email)>"
echo "📂  $(pwd)"
echo

# ── 1) 문서 커밋 ─────────────────────────────────────────────────────
echo "── 1/4: 문서 4종 + CHANGELOG ─────────────────────────────────"
git add \
  document/personas.md \
  document/user_journey_map.md \
  document/PRD.md \
  document/design_system.md \
  CHANGELOG.md \
  scripts/commit-current-changes.sh
if ! git diff --cached --quiet; then
  git commit -m "docs: add personas, journey map, PRD, design system, CHANGELOG

- document/personas.md: 1차/2차/3차 페르소나 정의 및 안티-페르소나
- document/user_journey_map.md: 5단계 여정, 감정 곡선, Moments of Truth
- document/PRD.md: v1.0 — Stage 1 완성 + Stage 2 Heritage Box MVP
- document/design_system.md: \"Warm Serenity\" 디자인 토큰
- CHANGELOG.md: 변경 이력 추적 시작
- scripts/commit-current-changes.sh: 단위별 커밋 헬퍼"
else
  echo "  (스테이지된 변경 없음 — 건너뜀)"
fi
echo

# ── 2) 백엔드: Heritage Box ───────────────────────────────────────
echo "── 2/4: 백엔드 — Heritage Box ────────────────────────────────"
git add \
  back/app/models/asset.py \
  back/app/models/__init__.py \
  back/app/schemas/asset.py \
  back/app/schemas/__init__.py \
  back/app/repositories/asset_repository.py \
  back/app/repositories/__init__.py \
  back/app/services/asset_service.py \
  back/app/services/__init__.py \
  back/app/api/v1/heritage.py \
  back/app/api/v1/__init__.py \
  back/alembic/versions/c1a2b3d4e5f6_expand_assets_for_heritage_box.py \
  back/tests/test_heritage.py
if ! git diff --cached --quiet; then
  git commit -m "feat(heritage): add Heritage Box backend (Stage 2)

디지털 유산 인벤토리(Stage 2)의 백엔드 골격을 추가합니다.

- model: Asset 테이블 확장 — name/type/identifier/encrypted_payload/
  action_on_death/designated_executor_id/note/timestamps
- alembic: c1a2b3d4e5f6 마이그레이션 (기존 assets 호환 backfill 포함)
- service: Fernet 자동 암복호화, 소유자 격리
- repo: list/get/create/update/delete + 그룹별 집계
- api: GET/POST/PATCH/DELETE /api/v1/heritage/assets, /summary, /:id/secret
- tests: 단위 + API 6종 (pytest 통과)"
else
  echo "  (스테이지된 변경 없음 — 건너뜀)"
fi
echo

# ── 3) 프론트엔드: Heritage Box + Tabs ──────────────────────────
echo "── 3/4: 프론트엔드 — Heritage Box + 하단 탭 ────────────────"
git add \
  front/App.tsx \
  front/src/api/client.ts \
  front/src/theme/colors.ts \
  front/src/theme/spacing.ts \
  front/src/components/BottomTabBar.tsx \
  front/src/screens/MainTabsScreen.tsx \
  front/src/screens/HeritageBoxScreen.tsx \
  front/src/screens/AssetFormScreen.tsx \
  'front/src/features/*'
if ! git diff --cached --quiet; then
  git commit -m "feat(heritage): Heritage Box screens + bottom tab navigation

- screens/MainTabsScreen: 홈/유산함/설정 3탭 (외부 의존성 없이 자체 구현)
- components/BottomTabBar: SafeArea-aware 하단 탭 바
- screens/HeritageBoxScreen: 목록·요약·빈상태 추천 5종·FAB
- screens/AssetFormScreen: 자산 추가/수정 폼, 암호화 시각 신호
- features/heritage/: metadata, AssetListItem, SegmentedControl,
  useAssets 훅 (MVVM, 코딩 컨벤션 §4.1)
- api/client: heritageApi + 타입 (Asset, AssetType, ActionOnDeath…)
- theme/spacing: 8pt 그리드, radius 토큰
- theme/colors: success/warning/overlay 토큰 추가
- App.tsx: 인증 후 HomeScreen → MainTabsScreen"
else
  echo "  (스테이지된 변경 없음 — 건너뜀)"
fi
echo

# ── 4) 나머지 자잘한 변경 ───────────────────────────────────────────
echo "── 4/4: 잔여 변경 (있으면) ─────────────────────────────────────"
if [[ -n "$(git status --porcelain)" ]]; then
  git add -A
  git commit -m "chore: misc updates from 2026-05-19 working session"
else
  echo "  (잔여 변경 없음)"
fi
echo

echo "✅  완료. 최근 커밋 5개:"
git log --oneline -5
