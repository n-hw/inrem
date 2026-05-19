# Gmail SMTP 셋업 가이드

InRem 의 알림 이메일은 `EmailProvider` Protocol 위에 동작하며, 현재
dev/alpha 단계에서는 **Gmail SMTP** 를 사용한다.

## ⚠️ 적용 범위

| 단계 | 적합? | 이유 |
| --- | --- | --- |
| 개발 / 스테이징 / 알파(<10명) | ✅ | 빠른 셋업, 무료 |
| Public Beta (수십~수백) | ⚠️ 한도 임박 | 일 500통 / 스팸 분류 위험 |
| 정식 출시 | ❌ | ToS 위반·계정 정지 위험, deliverability 보장 X |

출시 전 [Resend](https://resend.com) · SendGrid · AWS SES 중 하나로 갈아탈 것. 코드 변경은 `back/app/services/email_service.py` 에 새 `*Provider` 클래스 추가 + `_build_default_provider()` 분기 한 줄.

---

## 사용자 셋업 절차 (1회)

### 1) Gmail 계정 준비
- 이미 있는 개인 계정도 가능하나 **전용 계정 생성 권장** (예: `inrem.alerts@gmail.com`).
- 운영 계정 정지 시 InRem 알림이 다운된다는 점만 인지.

### 2) 2단계 인증 활성화
1. [https://myaccount.google.com/security](https://myaccount.google.com/security) 접속.
2. "Google에 로그인하는 방법" 섹션 → **2단계 인증** → **사용** 클릭.
3. 휴대전화 번호로 SMS 인증 완료.

### 3) 앱 비밀번호 생성
1. 같은 보안 페이지에서 검색창에 "앱 비밀번호" 입력 또는 [직접 이동](https://myaccount.google.com/apppasswords).
2. **앱 이름**: `InRem` (자유 입력).
3. **생성** 클릭 → 노란 박스에 **공백 포함 16자리** 표시.
4. **공백 제거**한 16자리 문자열을 안전한 곳에 복사. 다시는 못 본다.

### 4) `.env` 입력
프로젝트 루트 `.env` 파일에:

```bash
GMAIL_USERNAME=your-account@gmail.com
GMAIL_APP_PASSWORD=xxxxxxxxxxxxxxxx        # 공백 제거 16자리
GMAIL_FROM_NAME=InRem                       # 발신자 표시 이름
```

`.env` 는 `.gitignore` 되어 있어 커밋되지 않음. **공유 금지**.

### 5) 서버 재시작
서버 부팅 로그에서 다음 라인을 확인:

```json
{"event":"email_provider_init","provider":"GmailSMTPProvider","from":"your-account@gmail.com",...}
```

`MockEmailProvider` 가 뜨면 환경 변수가 인식되지 않은 것. `.env` 위치 및 변수명 재확인.

### 6) 발송 테스트

```bash
cd back
poetry run python - <<'PY'
import asyncio
from app.services.email_service import send_soft_checkin_email
from uuid import uuid4

asyncio.run(send_soft_checkin_email("your-personal@gmail.com", uuid4()))
PY
```

자신의 다른 이메일로 메일 도착 확인. 받은편지함에 안 보이면 **스팸함** 도 확인.

---

## 운영 시 유의사항

### 발송 한도
- **개인 Gmail**: ~500 emails/day. 24시간 롤링 윈도우 기준.
- **Workspace**: ~2,000/day.
- 한도 초과 시 24시간 차단.

### 스팸 분류 줄이기
1. **제목에 과한 키워드 자제** ("긴급" "확인" "응답 요망" 반복 시 위험).
2. 본문 HTML 의 링크/이미지 최소화.
3. 동일 본문을 대량 발송하면 패턴 검출됨 — 사용자/이벤트별 약간씩 다른 본문 유지.
4. SPF/DKIM 은 Gmail 측에서 자동 처리되지만, **From 도메인**이 `@gmail.com` 인 점은 변경 불가 (커스텀 도메인 필요 시 SES/SendGrid).

### 모니터링
- 발송 실패는 `inrem.audit` 카테고리가 아닌 일반 logger `app.services.email_service` 에 ERROR 로 기록 (`event=gmail_send_failed`).
- Sentry 연동 시 (`SENTRY_DSN` 설정) 실패가 자동 트래킹됨.

### 계정 보호
- 앱 비밀번호는 **이메일 발송 전용** — 다른 용도로 재사용 금지.
- 의심 활동 감지 시 Google 이 차단. 정기적으로 [Google 활동 로그](https://myaccount.google.com/notifications) 확인.

---

## 프로덕션 마이그레이션 체크리스트

출시 전 다음을 수행:

- [ ] 트랜잭션 메일 서비스 계정 발급 (Resend/SendGrid/SES 등).
- [ ] 도메인 (`@inrem.app` 등) 의 SPF/DKIM/DMARC DNS 레코드 추가.
- [ ] `*Provider` 클래스 추가 (예: `ResendEmailProvider`).
- [ ] `_build_default_provider()` 에 우선순위 분기 (`RESEND_API_KEY` 있으면 Resend, 없으면 Gmail).
- [ ] 발송 실패 시 자동 재시도 + bounce 처리 (서비스가 제공하는 webhook 연결).
- [ ] 로드 테스트로 일별 한도 시뮬레이션.
