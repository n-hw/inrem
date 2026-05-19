# InRem PRD (Product Requirements Document)

> 문서 버전: v1.0 · 최종 업데이트: 2026-05-19  
> 작성: InRem Product Team  
> 관련 문서: `proposal_v1.md` · `personas.md` · `user_journey_map.md` · `design_system.md`

---

## 1. 제품 개요 (Overview)

### 1.1 한 줄 정의
**InRem은 일상의 안부 체크에서 시작해 사후 집행까지 이어지는 통합 데스테크 플랫폼이다.**

### 1.2 비전
초고령·1인 가구 사회에서 "디지털 라이프 어드민(life admin)" 표준을 만든다.

### 1.3 미션
사용자가 살아 있는 동안에는 **안심을**, 떠난 후에는 **존엄과 정리를** 제공한다.

### 1.4 제품 단계 (Stages)
| Stage | 이름 | 핵심 기능 | 비즈니스 목적 |
| --- | --- | --- | --- |
| 1 | Entry — 안심/돌봄 | Guardian Pulse, Life Narrator | DAU·습관 확보 |
| 2 | Growth — 정리/설계 | Heritage Box, End Note, Executor Designation | 유료 전환 |
| 3 | Maturity — 실행/연결 | Legacy Sync, Safe Will, Eternal Link | 시장 지배·진입장벽 |

본 PRD v1.0은 **Stage 1 완성 + Stage 2 진입(Heritage Box MVP)**를 다룬다.

---

## 2. 목표 (Goals) & 비목표 (Non-Goals)

### 2.1 v1.0 목표
1. Guardian Pulse 안정화 (오탐률 ≤ 5%, 응답률 ≥ 85%).
2. **Heritage Box MVP 출시** (디지털 자산 인벤토리 + 사후 처리 의사 입력).
3. 보호자(N:M) 관계 및 권한 분리 모델 완성.
4. 결제 전환 가설 검증을 위한 "가족공유" 유료 플래그 노출.

### 2.2 비목표 (Out of Scope for v1.0)
- Stage 3 Legacy Sync(전문가 매칭) — Phase 6.
- AI 추모관 / 음성 합성 — Phase 7+.
- SMS Fallback / VAPI 음성 콜 — Phase 5.
- 관리자 대시보드 / 커뮤니티 — Phase 6.

---

## 3. 사용자 (Users)
상세 페르소나는 `personas.md` 참조.

| 페르소나 | 우선순위 | 사용 모드 |
| --- | --- | --- |
| P1 김재훈 (1인 가구 중년) | ★★★ | 본인 사용 (Ward) |
| P2 박지영 (보호자 자녀) | ★★★ | 보호자 사용 (Guardian) |
| P3 이정숙 (시니어) | ★★ | 자녀 대리 설정 → 본인 사용 |

---

## 4. 사용자 스토리 (User Stories)

### Epic A. Guardian Pulse (안부 체크)
- **A1** 사용자로서, 앱을 켜는 것만으로 안부 신호가 자동 전송되어 별도 행동을 안 해도 되길 원한다.
- **A2** 사용자로서, X시간 무활동 시 푸시 알림을 받아 1탭으로 응답하고 싶다.
- **A3** 사용자로서, 수면 시간에는 알림이 오지 않도록 안심 시간을 설정하고 싶다.
- **A4** 보호자로서, 피보호자가 응답하지 않으면 자동으로 내게 알림이 와야 한다.
- **A5** 사용자로서, 보호자가 늘어나거나 줄어도 코드 기반으로 쉽게 관리하고 싶다.

### Epic B. Heritage Box (디지털 유산 인벤토리) — **v1.0 핵심**
- **B1** 사용자로서, SNS·구독·클라우드·가상자산·중요 문서를 한 화면에서 목록화하고 싶다.
- **B2** 사용자로서, 각 항목에 대해 사후 처리 의사(삭제/기념/승계/비공개)를 기록하고 싶다.
- **B3** 사용자로서, 비밀번호·계좌번호 등 민감 정보는 **암호화** 저장이 되어야 한다.
- **B4** 사용자로서, 항목을 추가/수정/삭제할 수 있어야 한다.
- **B5** 보호자로서, (사용자가 권한 부여한 경우) 인벤토리 요약을 열람할 수 있어야 한다. *(v1.1 이연)*

### Epic C. End Note (엔딩노트) — *v1.1*
- **C1** 사용자로서, 장례 방식·연락처·예산 등의 표준 템플릿을 따라 답할 수 있어야 한다.
- **C2** 사용자로서, 자동저장·재개가 가능해야 한다.

### Epic D. Settings & Policy
- **D1** 사용자로서, 민감도(느슨함/보통/엄격함)와 안심 시간을 변경할 수 있어야 한다.
- **D2** 사용자로서, 알림 OFF / 모니터링 일시정지가 가능해야 한다.

### Epic E. Onboarding
- **E1** 신규 사용자로서, 3분 이내에 핵심 가치를 이해하고 첫 안부 체크를 받을 수 있어야 한다.

---

## 5. 기능 요구사항 (Functional Requirements)

### 5.1 [v1.0 신규] Heritage Box

#### 5.1.1 데이터 모델
```
Asset
├── id: UUID
├── user_id: UUID (FK → users.id)
├── name: str (예: "Instagram 계정")
├── type: enum {social_account, subscription, cloud_storage, crypto, bank_account, document, etc, custom}
├── identifier: str (이메일·계정 ID 등, 평문 OK)
├── encrypted_payload: bytes (비밀번호·시드 등 민감 정보, Fernet)
├── iv: bytes (encryption IV)
├── action_on_death: enum {delete, memorialize, transfer, keep_private}
├── designated_executor: UUID? (Guardian 중 누가 처리할지)
├── note: text? (자유 메모)
├── created_at, updated_at: datetime
```

#### 5.1.2 API 엔드포인트 (`/api/v1/heritage`)
| Method | Path | 설명 |
| --- | --- | --- |
| GET | `/assets` | 본인 자산 목록 (페이지네이션) |
| POST | `/assets` | 자산 생성 |
| GET | `/assets/{id}` | 자산 상세 |
| PATCH | `/assets/{id}` | 자산 수정 |
| DELETE | `/assets/{id}` | 자산 삭제 |
| GET | `/assets/summary` | 타입별 집계 (개수, 사후 처리 분포) |

#### 5.1.3 권한 & 보안
- 본인 외 조회 불가 (executor 권한은 v1.1).
- `encrypted_payload`는 `EncryptionService.encrypt()` 의무 적용.
- `identifier`는 평문(검색·확인용), `encrypted_payload`는 비밀번호/시드 전용.

#### 5.1.4 UX 요구
- 리스트는 **타입별 그룹핑** + 검색.
- 항목 추가 폼은 **1스크린·5필드 이내** (Name, Type, Identifier, Action on death, Note).
- 민감 필드 입력 시 "🔒 암호화 저장됨" 시각 신호.
- 빈 상태(empty state) 시 "추천 자산 5가지" 가이드 제공 (Instagram·Netflix·Google Drive·KB증권·중요 문서).

### 5.2 [v1.0 강화] Guardian Pulse
- 기존 구현 유지.
- 추가: HomeScreen에 **"오늘 Heritage Box 1항목 정리하기"** 추천 카드.

### 5.3 [v1.0 신규] Tab Navigation
- 하단 탭 3개: `홈(Pulse)` · `유산함(Heritage)` · `설정(Settings)`.

### 5.4 [v1.0 유지] 인증·보호자·정책·디바이스
- 변경 없음.

---

## 6. 비기능 요구사항 (Non-Functional)

| 항목 | 기준 |
| --- | --- |
| 응답 시간 | API p95 < 500ms |
| 가용성 | 99.5% (월 ~3.6시간 다운 허용) |
| 보안 | 민감 PII Fernet 암호화, JWT 30일 만료, HTTPS 강제 |
| 접근성 | 폰트 18pt+ 기본, 색대비 WCAG AA |
| 국제화 | 한국어 우선, i18n 구조 미리 준비 |
| 데이터 보존 | 사용자 삭제 요청 시 30일 grace → 영구 삭제 |

---

## 7. 성공 지표 (Success Metrics)

### 7.1 North Star
**WAU 중 안부 응답 + 자산 1개 이상 등록한 사용자 수.**

### 7.2 보조 KPI
| Stage | KPI | Target (3개월 후) |
| --- | --- | --- |
| Stage 1 | D7 리텐션 | ≥ 50% |
| Stage 1 | 무활동 알림 응답률 | ≥ 85% |
| Stage 1 | 오탐 비율 | ≤ 5% |
| Stage 2 | Heritage Box 1항목 작성률 | ≥ 25% |
| Stage 2 | 자산 평균 입력 수 | ≥ 3개 |
| Stage 2 | 유료 옵션 클릭률 (가족공유) | ≥ 8% |

---

## 8. 마일스톤 (Milestones)

| 마일스톤 | 기간 | 산출물 |
| --- | --- | --- |
| M0 — 문서 확정 | W1 | personas/journey/PRD/design 확정 |
| M1 — Heritage 백엔드 | W2 | DB 마이그레이션, API, 단위 테스트 |
| M2 — Heritage 프론트 | W3 | 리스트/폼/상세, Tab Nav |
| M3 — 내부 베타 | W4 | 사내 사용자 10명, 버그 수렴 |
| M4 — 공개 베타 | W6 | TestFlight·Play Internal |
| M5 — 공개 출시 | W8 | 1.0 GA |

---

## 9. 위험 & 완화 (Risks)

| 리스크 | 영향 | 완화책 |
| --- | --- | --- |
| 민감 정보(비밀번호) 입력 거부감 | High | 입력 선택 사항. "메모만" 가능. 암호화 강조. |
| Stage 2 인지 부담 | High | 1번에 1항목 원칙. 빈 상태 추천 5종. |
| Heritage Box 결제 전환 실패 | Med | 가족공유·리포트 등 명확한 유료 가치 묶음. |
| 알림 오탐으로 이탈 | High | 임계치 보수적 시작, 안심 시간 강제, 패턴 학습 (Phase 5). |
| 사망 확인 절차 신뢰성 | Critical | v1.0 범위 외. Stage 3에서 다중 검증 도입. |

---

## 10. 의존성 (Dependencies)

- 백엔드: FastAPI, SQLAlchemy(Async), Alembic, Cryptography(Fernet).
- 프론트: React Native(Expo), React Navigation(Bottom Tabs 신규 추가).
- 인프라: PostgreSQL 15, Docker Compose, FCM.

신규 패키지:
- 프론트: `@react-navigation/native`, `@react-navigation/bottom-tabs` (이미 안 깔려 있다면 추가 필요).

---

## 11. 오픈 이슈 (Open Questions)

1. Heritage Box `executor`(자산별 지정인) 권한 부여 UX → v1.1로 이연.
2. End Note 템플릿 한국 실정에 맞게 법무사 자문 필요 (Stage 2 후반).
3. 결제 모듈은 인앱결제(Apple/Google) vs 외부(토스페이먼츠)? → 정책팀 검토 필요.

---

## 12. Approvals

| 역할 | 이름 | 승인 |
| --- | --- | --- |
| PM | (TBD) | ☐ |
| Tech Lead | (TBD) | ☐ |
| Design Lead | (TBD) | ☐ |
| Legal | (TBD) | ☐ |
