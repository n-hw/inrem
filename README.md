# InRem (인램) - 디지털 돌봄 & 모니터링 플랫폼

InRem은 비침습적 활동 감지와 자동화된 안부 확인을 통해 1인 가구 및 시니어의 안녕을 모니터링하기 위해 설계된 디지털 돌봄 플랫폼입니다.

## 🏗 기술 스택 (Technology Stack)

- **백엔드**: FastAPI (Python 3.12), SQLAlchemy (Async), Alembic, Pydantic
- **프론트엔드**: React Native (Expo), TypeScript, React Navigation
- **데이터베이스**: PostgreSQL 15 (Docker)
- **인프라**: Docker, Docker Compose
- **알림**: Firebase Cloud Messaging (FCM)
- **보안**: Fernet 암호화 (Cryptography), JWT 인증

---

## 🚀 구현된 서비스 (현재 상태)

### 1. 핵심 인프라 (Core Infrastructure)
- **컨테이너화**: 백엔드 및 데이터베이스 서비스의 완전한 Docker 지원 (`docker-compose.yml`).
- **데이터베이스 관리**:
    - 비동기(Async) SQLAlchemy 세션 관리.
    - Alembic을 통한 자동 마이그레이션 (`alembic upgrade head`).
- **CI/CD**: GitHub Actions 워크플로우 (`ci.yml`)를 통한 자동화된 테스트 및 린팅.

### 2. 인증 및 보안 (Authentication & Security)
- **JWT 인증**: 액세스 토큰 생성 및 검증 (`/api/v1/auth/login`).
- **보안**:
    - bcrypt를 이용한 비밀번호 해싱.
    - **암호화 서비스**: 민감한 사용자 정보(PII)에 대한 Fernet 필드 레벨 암호화 적용.

### 3. 가디언 펄스 (Guardian Pulse - 활동 모니터링 엔진)
비활동을 감지하고 안부 확인 수명주기를 관리하는 핵심 엔진입니다.

- **하트비트 시스템 (Heartbeat System)**:
    - **API**: `POST /api/v1/signal/heartbeat`
    - **앱 상태 로직**: 앱 포그라운드/백그라운드 진입 및 실행 이벤트를 자동으로 추적합니다.
    - **디바운싱**: 서버 과부하 방지를 위해 1분의 쿨다운 타임을 적용했습니다.
- **펄스 엔진 (`services/pulse_engine.py`)**:
    - **비활동 감지**: 백그라운드 스케줄러가 주기적으로 `last_active_at`을 확인합니다.
    - **안심 시간 (Quiet Hours)**: 사용자가 설정한 수면 시간(예: 23:00 - 07:00)에는 오탐 방지를 위해 알림을 억제합니다.
- **소프트 체크인 (Level 1 알림)**:
    - **트리거**: 비활동 임계치 도달 시 FCM을 통해 "잘 지내시나요?" 푸시 알림을 전송합니다.
    - **응답**: 사용자가 "잘 있어요" 버튼을 누르면 (`POST /api/v1/pulse/respond`) 타이머가 초기화됩니다.
- **하드 체크인 (Level 2 에스컬레이션)**:
    - **에스컬레이션 로직**: 소프트 체크인 후 `escalation_delay` 분 동안 응답이 없을 경우 발동합니다.
    - **보호자 알림**: 등록된 모든 보호자에게 멀티캐스트 FCM 긴급 알림을 전송합니다.
    - **이메일 백업**: **[NEW]** 푸시 알림 전송 실패 시 이메일 알림을 자동으로 발송합니다 (`services/email_service.py`).

### 4. 보호자 관리 시스템 (Guardian Management)
- **관계 모델**: N:M 다대다 관계 지원 (한 피보호자가 여러 보호자를, 한 보호자가 여러 피보호자를 가질 수 있음).
- **초대 흐름**:
    - **코드 생성**: `POST /api/v1/guardian/invite` (6자리 숫자 코드 반환, 24시간 유효).
    - **코드 수락**: `POST /api/v1/guardian/accept` (보호자와 피보호자 연결).
- **관리**: 보호자/피보호자 목록 조회 및 연결 해제 API.

### 5. 알림 시스템 (Notification System)
- **FCM 인프라**:
    - 토큰 등록 및 관리 (`/api/v1/device/register`).
    - 멀티캐스트 메시징 지원 (여러 보호자 기기에 동시 전송).
- **백업 메커니즘 (Fallback)**:
    - FCM 전송 실패를 감지합니다.
    - 긴급 알림의 경우 자동으로 이메일 서비스(현재 Mock 구조 구현됨)로 우회 처리합니다.

### 6. 사용자 설정 및 정책 (Settings & Policy)
- **모니터링 정책**:
    - **API**: `GET/PATCH /api/v1/settings/policy`
    - **설정 가능한 옵션**:
        - **민감도**: 느슨함 (24h) / 보통 (12h) / 엄격함 (6h).
        - **안심 시간**: 알림을 받지 않을 시작/종료 시간 설정.
        - **에스컬레이션**: 보호자 알림 활성화/비활성화.
        - **모니터링**: 전체 기능 켜기/끄기.