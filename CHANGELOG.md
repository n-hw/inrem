# Changelog

InRem 프로젝트의 주요 변경 이력입니다.
[Keep a Changelog](https://keepachangelog.com/ko/1.1.0/) 규칙을 따릅니다.

## [Unreleased] - 2026-05-19

### Added (신규)
- **문서 4종**
  - `document/personas.md` — 페르소나·핵심 타겟 정의 (P1 1인 가구 중년, P2 보호자, P3 시니어)
  - `document/user_journey_map.md` — 5단계 사용자 여정 지도, 감정 곡선, Moments of Truth
  - `document/PRD.md` — v1.0 PRD (Stage 1 완성 + Stage 2 Heritage Box MVP)
  - `document/design_system.md` — "Warm Serenity" 디자인 시스템 토큰
- **Heritage Box (Stage 2 - 디지털 유산 인벤토리) 백엔드**
  - `back/app/api/v1/heritage.py` — REST 엔드포인트 7종
  - `back/app/services/asset_service.py` — Fernet 자동 암복호화, 소유자 격리
  - `back/app/repositories/asset_repository.py`
  - `back/app/schemas/asset.py`
  - `back/alembic/versions/c1a2b3d4e5f6_expand_assets_for_heritage_box.py` — DB 마이그레이션
  - `back/tests/test_heritage.py` — 단위·API 테스트 6종
- **Heritage Box 프론트엔드**
  - `front/src/screens/HeritageBoxScreen.tsx` — 자산 목록·요약·빈 상태 추천
  - `front/src/screens/AssetFormScreen.tsx` — 자산 추가/수정 폼 (암호화 표시)
  - `front/src/features/heritage/` — 메타데이터, AssetListItem, SegmentedControl, useAssets 훅 (MVVM)
- **네비게이션**
  - `front/src/components/BottomTabBar.tsx` — 외부 의존성 없는 하단 탭
  - `front/src/screens/MainTabsScreen.tsx` — 홈/유산함/설정 3탭
- **디자인 토큰**
  - `front/src/theme/spacing.ts` — 8pt 그리드, radius 토큰

### Changed (변경)
- `back/app/models/asset.py` — Heritage Box용 컬럼 확장 (name, identifier, action_on_death, designated_executor_id, note, timestamps)
- `back/app/api/v1/__init__.py` — heritage 라우터 등록
- `back/app/models/__init__.py`, `repositories/__init__.py`, `services/__init__.py`, `schemas/__init__.py` — Heritage 모듈 export
- `front/App.tsx` — 인증 후 진입을 HomeScreen → MainTabsScreen
- `front/src/api/client.ts` — `heritageApi` 추가, 타입(`Asset`, `AssetType`, `ActionOnDeath` 등) 추가
- `front/src/theme/colors.ts` — `success`, `warning`, `overlay` 토큰 추가

### Verified (검증)
- 백엔드: pytest 8/8 통과 (Heritage 6 + Timer 2)
- 프론트엔드: `tsc --noEmit` exit 0
- FastAPI: `/api/v1/heritage/*` 7개 라우트 정상 등록 확인

---

## [기존 커밋 이력 — git log]

- `91551d9` test: add testing infrastructure, scripts and guidelines
- `2f32335` feat: implement monitoring policy settings, email fallback service, and update documentation
- `b7db56a` Initial commit
