# InRem 테스트 가이드 (Testing Workflow)

이 문서는 InRem 플랫폼의 주요 기능을 효율적으로 테스트하기 위한 전략과 스크립트 사용법을 설명합니다.
복잡한 "비활동 감지" 및 "에스컬레이션" 시나리오를 시간을 기다리지 않고 즉시 검증할 수 있는 **Time Travel(시간 조작)** 테스트 방식을 중점으로 합니다.

---

## 🏗 테스트 환경 설정

### 1. 테스트 데이터 생성 스크립트 (`tests/scripts/seed_data.py`)
매번 회원가입을 할 필요 없이, 테스트용 피보호자(Ward)와 보호자(Guardian) 계정을 생성하고 연결합니다.

```bash
# 사용법
docker-compose exec backend python tests/scripts/seed_data.py --ward "ward@test.com" --guardian "guard@test.com"
```
- 피보호자/보호자 계정 생성
- FCM 토큰 더미 데이터 등록
- 보호자 연결 (수락 상태)
- 모니터링 정책 생성 (기본값)

---

## ⚡️ Pulse Engine 테스트 워크플로 (Time Travel)

실제 12시간을 기다릴 수 없으므로, 데이터베이스의 타임스탬프를 조작하여 엔진이 즉시 반응하게 합니다.

### 시나리오 1: 소프트 체크인 (Level 1) 강제 발동
사용자가 마지막으로 활동한 시간을 강제로 과거로 돌립니다.

1. **상태 조작 (`tests/scripts/trigger_soft_check.py`)**
   ```bash
   # ward@test.com의 마지막 활동을 24시간 전으로 설정
   docker-compose exec backend python tests/scripts/trigger_soft_check.py --email "ward@test.com" --hours 24
   ```
2. **검증**
   - 백엔드 로그 확인: `Checking inactivity...` -> `Soft Check triggered`
   - FCM 알림 발송 로그 확인.
   - DB `pulse_events` 테이블에 새로운 이벤트 생성 확인.

### 시나리오 2: 하드 체크인 (Level 2) 및 에스컬레이션
소프트 체크인을 보냈는데 응답이 없는 상황을 시뮬레이션합니다.

1. **상태 조작 (`tests/scripts/trigger_escalation.py`)**
   ```bash
   # 현재 진행 중인 'Soft Check' 이벤트의 발송 시간을 1시간 전으로 조작
   docker-compose exec backend python tests/scripts/trigger_escalation.py --email "ward@test.com"
   ```
2. **검증**
   - 백엔드 로그: `Escalating event...`
   - 보호자(`guard@test.com`)에게 FCM 알림 전송 확인.
   - (FCM 실패 시) 이메일 서비스 호출 로그 확인.

---

## 🧪 자동화 테스트 (Unit/Integration)

CI/CD 파이프라인에서 실행되는 표준 테스트입니다.

```bash
# 전체 테스트 실행
docker-compose exec backend pytest

# 특정 모듈 테스트
docker-compose exec backend pytest tests/services/test_pulse_engine.py
```

---

## 📝 수동 테스트 체크리스트 (UI)

1. **로그인/회원가입**: `seed_data.py`로 생성된 계정(`password: test1234`)으로 로그인 성공 여부.
2. **설정 변경**: 앱 내 `설정` 탭에서 민감도를 '엄격함'으로 변경 후 API 반영 확인.
3. **생존 신고**: 홈 화면의 "잘 지내요" 버튼 클릭 시 `pulse_events`가 `RESOLVED`로 변경되는지 확인.

---

## 📱 UI 테스트 전략 (UI Testing Strategy)

InRem은 **자동화된 컴포넌트 테스트**와 **백엔드 주도 시나리오 테스트**의 투트랙 전략을 사용합니다.

### 1. 자동화된 컴포넌트 테스트 (Unit Tests)
React Native Testing Library를 사용하여 개별 화면의 렌더링과 기본 동작을 검증합니다.

```bash
# 프론트엔드 테스트 실행
cd front
npm test
```

- **주요 검증 대상**:
  - `LoginScreen`: 입력 폼 렌더링, 유효성 검사 로직.
  - `SettingsScreen`: 설정값(정책)이 UI에 올바르게 반영되는지.
  - `AlertBanner`: 푸시 알림 수신 시 배너 노출 여부.

### 2. 시나리오 기반 UI 테스트 (Manual Scenario)
백엔드 스크립트로 상태를 조작하고, 실제 앱(Simulator/Phone)에서의 반응을 확인합니다.

| 시나리오 | 백엔드 조작 (Action) | 프론트엔드 기대 결과 (Expectation) |
| --- | --- | --- |
| **비활동 감지** | `trigger_soft_check.py` 실행 | 앱 포그라운드 시 "잘 지내시나요?" 팝업/배너 노출 |
| **에스컬레이션** | `trigger_escalation.py` 실행 | 보호자 앱에서 "🚨 긴급 알림" 붉은색 카드 노출 |
| **안심 시간** | DB에서 `quiet_hours` 변경 | 비활동 상태여도 알림이 울리지 않음 (Silent) |

