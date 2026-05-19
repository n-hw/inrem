# 출시 전 잔여 작업 체크리스트

> **최종 갱신**: 2026-05-19 · **현재 상태**: v1.0 코드 베이스라인 완성, 출시 직전 단계
>
> 이 문서는 "InRem이 일반 사용자에게 배포되기 전 반드시·가급적·후속으로 처리해야 할 일들"의 단일 진실 공급원입니다.
> 항목 처리 시 체크박스에 표시하고, 새로 발견된 작업이 있으면 적절한 섹션에 추가하세요.

---

## 🚨 출시 차단 (Critical — 일반 배포 전 반드시)

처리되지 않으면 사용자 피해·법적 리스크·서비스 중단으로 직결되는 항목.

### 결제 & 사업 인프라
- [ ] **사업자 등록** (사용자 작업) — 결제·세금·계약 베이스라인
- [ ] **결제 모듈 결정 & 통합**
  - 인앱결제(Apple/Google) vs 외부(토스페이먼츠) 결정 (PRD §11 오픈 이슈)
  - 가족공유 페이월 클릭 KPI(`POST /settings/upsell/click` 로그) 데이터 모인 뒤 결정 권장
- [ ] **개인정보처리방침·이용약관 법무 자문** (후순위로 빼둔 상태)
  - `document/legal/privacy_policy.md`, `terms_of_service.md` 의 `{{TBD}}` 치환
  - 변호사(개인정보보호법 전문) 검토 필수
  - 회원가입·온보딩에 약관 동의 체크박스 + 동의 버전 저장 UI

### 데이터 영구 삭제 (잊혀질 권리 완결)
- [x] ~~**30일 grace 만료 사용자 영구 삭제 cron sweep**~~ ✅ 2026-05-19
  - `account_service.purge_expired_deletions()` + `AccountPurgeScheduler` (24h)
  - `inrem.audit.account` 에 `account_purged` 감사 로그
  - **잔여**: SQLAlchemy cascade 미설정 테이블 점검(보호자 매핑 등) 필요

### 이메일 프로덕션 채널
- [ ] **트랜잭션 이메일 서비스 전환** (현재 Gmail SMTP — dev/alpha 한정)
  - 후보: Resend(추천) / SendGrid / AWS SES
  - 신규 `*Provider` 클래스 추가 + `_build_default_provider()` 분기 한 줄
  - DNS 에 SPF/DKIM/DMARC 레코드 추가 (커스텀 도메인 사용 시)
  - 가이드: `document/operations/email_gmail_setup.md` 마지막 섹션
- [ ] **자동 재시도 + bounce webhook 처리** (안전 알림 도달률 직결)

### 운영 인프라
- [ ] **HTTPS / TLS 종단** (Nginx / Caddy / Traefik 등)
  - 현재 `docker-compose.yml` 만 있고 리버스 프록시 미구성
- [ ] **Fernet 암호화 키 안전 관리**
  - 현재 `.env` 평문. 프로덕션은 AWS KMS / GCP KMS / HashiCorp Vault 로 이관
  - 키 회전 정책 (`ENCRYPTION_KEY_v2` 점진 마이그레이션) 설계
- [ ] **DB 백업·복구 정책**
  - 정기 스냅샷, 보관 기간, 복구 리허설(분기 1회 권장)
- [ ] **Sentry 실제 연동**
  - 코드 측 hook 완성 (`back/app/core/logging.py`)
  - `sentry-sdk` 의존성 추가 + `SENTRY_DSN` 환경변수 설정
  - 프론트 RN 측 Sentry/Crashlytics 별도 통합

---

## 🛡️ 운영 베이스라인 (스케일 직전)

사용자 수가 늘어나면 빠르게 부족해질 항목.

### 멀티 인스턴스 대비
- [ ] `SECRET_REVEAL_LIMITER` Redis 백엔드로 교체
  - 위치: `back/app/core/rate_limit.py`
  - 현재 인메모리 → 다중 워커에서 카운트 누락
- [ ] APScheduler → Celery/RQ 큐 도입
  - 알림 발송·삭제 sweep 등을 워커 풀로 분리

### 분석·모니터링
- [ ] **페이월 클릭 분석 파이프라인**
  - 현재 `logger("inrem.upsell")` stdout 출력만
  - 로그 수집 → BigQuery / Loki / CloudWatch Insights 로 집계
  - PRD §7.2 KPI ("유료 옵션 클릭률 ≥ 8%") 검증 가능 상태로
- [ ] **알림 도달률·실패율 대시보드**
  - 푸시 발송 결과 + 이메일 발송 결과 누적 집계
- [ ] **API 응답 시간 / 에러율 모니터링**
  - PRD §6 NFR: "API p95 < 500ms" 측정 수단 필요

### 보안 보강
- [ ] **JWT 토큰 회전 / refresh token** (현재 30일 단일 토큰)
- [x] ~~**로그인 시도 rate-limit**~~ ✅ 2026-05-19 — `LOGIN_LIMITER` (5회/분, email+IP 키)
- [x] ~~**CORS 정책 명시화**~~ ✅ 2026-05-19 — `CORSMiddleware`, `CORS_ALLOW_ORIGINS` env
- [ ] **민감 정보(시크릿) 입력 폼 — 클립보드 자동 클리어** (프론트)

---

## ⚠️ 알려진 한계 (워크어라운드 있음)

수정하면 좋지만 임시 회피 가능.

### 테스트 인프라
- [ ] **Jest 환경 완전 복구**
  - 잔여 이슈: Expo winter runtime(`import.meta`) + Node 25 호환성
  - 옵션: Node 24 다운그레이드 / Jest 29 핀 / 커스텀 testEnvironment
  - 영향: `LoginScreen.test.tsx` 한 개 못 돌림. 사용자 동선 검증은 수동.
- [ ] **E2E 통합 테스트**
  - 시나리오: 비활동 감지 → 소프트 체크인 → 푸시 실패 → 이메일 fallback → 보호자 알림
  - Detox 또는 Playwright + Expo Web

### 기능 폴리싱
- [x] ~~**HomeScreen 폴링**~~ ✅ 2026-05-19 — 60초 주기 `signalApi.getStatus()`
- [x] ~~**HomeScreen에 last_active_at 전용 엔드포인트**~~ ✅ 2026-05-19 — `GET /api/v1/signal/status` (부수효과 없음)
- [ ] **에러 메시지 다양화**
  - 401 / 5xx / 네트워크 단절 별로 다른 UX

### PRD v1.0 검증 잔여
- [ ] **보호자(N:M) 권한 분리 모델 완성도 감사** (PRD §2.1 Goal 3)
  - `back/app/api/v1/guardian.py` 의 권한 매트릭스 점검
- [ ] **빈 상태 추천 자산 5종 실제 동작 검증** (수동 QA)

---

## 📱 출시 직전 — 앱 스토어 자산

- [ ] **앱 아이콘** (1024x1024, 라운드/스퀘어)
- [ ] **스플래시 스크린**
- [ ] **스크린샷** (iOS: 6.7" / 6.5" / 5.5"; Android: 폰 / 태블릿)
- [ ] **앱 소개 문구**
  - 한 줄 소개 (30자) · 짧은 소개 (80자) · 긴 소개 (4000자)
- [ ] **개인정보 처리 요약** (Apple Privacy Nutrition Labels / Google Data Safety)
- [ ] **연령 등급 심사** (4+/12+ 등)
- [ ] **TestFlight / Play Internal Testing** 배포 → 사내 베타 10명 검증
- [ ] **앱 심사 가이드 대응**
  - Apple: "안부 체크"가 의료/응급 기능으로 분류되지 않도록 문구 조정
  - Google: 위치·연락처 권한 사용 사유 명시
- [ ] **고객 지원 채널** (이메일·FAQ 페이지)

---

## 🔮 v1.x 후속 기능 (PRD 명시)

v1.0 GA 이후 단계적으로.

- [ ] **End Note (엔딩노트)** — PRD Epic C
  - 장례 방식·연락처·예산 표준 템플릿
  - 자동저장·재개 (PRD C2)
- [ ] **Heritage Box executor 권한 부여** — 자산별 지정인 UX (PRD §11 오픈 이슈 1)
  - 자산 보기 권한 → 사망 확인 후 처리 권한 단계화
- [ ] **보호자 인벤토리 요약 열람** (PRD B5)
  - 사용자가 권한 부여한 경우만, 민감 정보는 제외
- [ ] **이메일 백업 잠금 풀기** — End Note PDF 자동 첨부

---

## 🚫 명시적 v1.0 범위 밖 (Phase 5+)

PRD §2.2 비목표 명시. v1.0 GA 이후 별도 마일스톤.

- [ ] **AI 보이스 콜 (VAPI.ai)** — 푸시·이메일 무응답 시 자동 전화
- [ ] **생활 패턴 분석 (Bio-rhythm)** — `ActivitySignal` ML 기반 이상 감지
- [ ] **119 / 경찰서 시스템 연동**
- [ ] **관리자 대시보드** (DAU 분석·시스템 모니터링·사용자 관리)
- [ ] **커뮤니티 게시판** (보호자 간 정보 공유)
- [ ] **SMS Fallback (Twilio / CoolSMS)** — 이메일도 실패할 경우 3중 안전망
- [ ] **AI 추모관 (Eternal Link)** — 윤리·삭제권·민감 모드 정책 동반

---

## 📚 참고 문서

- 제품: [`PRD.md`](PRD.md) · [`proposal_v1.md`](proposal_v1.md)
- 페르소나·여정: [`personas.md`](personas.md) · [`user_journey_map.md`](user_journey_map.md)
- 디자인: [`design_system.md`](design_system.md) · [`ui_guide.md`](ui_guide.md)
- 코드 규약: [`coding_convention.md`](coding_convention.md)
- 운영: [`operations/email_gmail_setup.md`](operations/email_gmail_setup.md)
- 법무: [`legal/README.md`](legal/README.md)
- 변경 이력: [`../CHANGELOG.md`](../CHANGELOG.md)
- 기능 로드맵: [`../todo.md`](../todo.md)
