# 앱 스토어 메타데이터 & 심사 대응

> **상태**: 출시 전 베이스라인. 디자이너·법무 검토 후 최종화.

---

## 1. 기본 정보

| 항목 | 값 | 비고 |
| --- | --- | --- |
| 앱 이름 (App Name) | **InRem** | iOS/Android 공통 |
| 한글 이름 | **인렘** | Android Play Console / 한국 App Store |
| 번들 ID (iOS) | `com.inrem.app` | 이미 설정됨 |
| 패키지 (Android) | `com.inrem.app` | 이미 설정됨 |
| 카테고리 (1차) | **생산성 (Productivity)** | "라이프스타일" 보다 안전 |
| 카테고리 (2차) | **라이프스타일 (Lifestyle)** | |
| 연령 등급 | **만 4세 이상 / Everyone** | 의료적 내용 없음, 광고 없음 |
| 가격 | **무료** (인앱 결제 v1.x 이후) | |
| 지원 언어 | **한국어** (1차), **English** (2차) | |

---

## 2. 스토어 카피 (한국어)

### 한 줄 소개 (30자 이내)
> **혼자 사는 당신을 조용히 지켜드릴게요.**

(28자)

### 부제 / Subtitle (30자 이내, iOS만)
> **안부 체크 · 디지털 유산 정리**

(16자)

### 짧은 소개 (Google Play Short Description — 80자 이내)
> **앱을 켜는 것만으로 안부 신호. 디지털 유산은 미리 정리. 1인 가구·시니어를 위한 조용한 안전망.**

(74자)

### 키워드 (App Store, 100자 이내, 쉼표 구분)
> `안부체크,1인가구,디지털유산,엔딩노트,웰다잉,혼자살기,비상연락,상속정리,안심,보호자`

### 긴 소개 (App Store / Play 4,000자 이내)

```
InRem은 혼자 사는 분들과 시니어를 위한
"조용한 안전망"입니다.

━━━ 어떻게 작동하나요? ━━━

🌙 안부 체크 (Guardian Pulse)
앱을 켜거나 사용하기만 해도 자동으로
안부 신호가 기록됩니다. 별도로 버튼을
누르거나 메시지를 보낼 필요가 없습니다.

설정한 시간(6/12/24시간) 동안 활동이
감지되지 않으면 본인에게 먼저 알림이
오고, 응답이 없으면 미리 지정한 보호자
에게 자동으로 안부 확인을 요청합니다.

🗂️ 디지털 유산함 (Heritage Box)
SNS 계정, 구독 서비스, 클라우드, 가상자산,
중요 문서 등을 한 곳에 정리하고 "떠난 후"
처리 방법(삭제·추모·승계·비공개)을 미리
체크하세요. 민감 정보는 자동 암호화되어
본인만 열람할 수 있습니다.

🛡️ 안심하고 쓰세요
· 비밀번호·시드 등 민감 정보는 Fernet
  대칭 암호화로 보관. 본인 외 접근 불가.
· 사후 데이터 처리 의사는 사용자가 직접
  지정. 임의 처리 없음.
· 잊혀질 권리: 언제든 계정 삭제 요청 →
  30일 유예 후 영구 삭제.

━━━ 누가 쓰면 좋은가요? ━━━

· 부모님과 떨어져 사는 분
· 혼자 사는 1인 가구 (40~60대)
· 가족이 없거나 짐을 줄이고 싶은 시니어
· 디지털 흔적이 많은 분 (계정·구독·자산)

━━━ 주의사항 ━━━

InRem의 안부 체크 및 보호자 알림 기능은
'보조적 안전망'입니다. 의료·응급 상황에
대한 보장을 제공하지 않으며, 응급 상황
시에는 119에 직접 연락하시기 바랍니다.

━━━ 문의 ━━━

· 이메일: {{TBD@inrem.app}}
· 개인정보처리방침: {{URL}}
· 이용약관: {{URL}}
```

---

## 3. 영문 카피 (글로벌 제출 시)

### Subtitle
> **Quiet safety net for living alone**

### Short Description
> **Activity-based wellness check + digital legacy inventory for people living alone or for seniors.**

### Promotional text
> A quiet companion that watches over you and helps organize what matters — before and after.

---

## 4. 개인정보 라벨 — Apple App Privacy

App Store Connect → App Privacy 섹션 입력 예시.

### Data Used to Track You
**없음** (트래킹 SDK 미사용)

### Data Linked to You

| Data Type | Purpose | Optional? |
| --- | --- | --- |
| **Email Address** | App Functionality | 필수 |
| **User ID** (UUID) | App Functionality | 필수 |
| **Device ID (FCM token)** | App Functionality (푸시 알림) | 선택 |
| **Other User Content** (자산 인벤토리·메모) | App Functionality | 선택 (Heritage Box 사용 시) |
| **Sensitive Info** (Heritage Box 암호화 페이로드) | App Functionality | 선택, **암호화 저장** |
| **Crash Data / Performance Data** | Analytics (Sentry) | 선택, Sentry DSN 설정 시 |

### Data Not Linked to You
- App activity timestamps (Guardian Pulse 신호) — 90일 후 자동 삭제.

---

## 5. 데이터 안전 섹션 — Google Play Data Safety

Play Console → App content → Data safety 입력 예시.

### Data collection & sharing
**Yes** — 위 표와 동일 항목 수집. **제3자 공유 없음** (사용자가 지정한 보호자에게 알림 발송은 사용자 동의 기반).

### Security practices
- ✅ Data is encrypted in transit (HTTPS)
- ✅ Data is encrypted at rest (Fernet for sensitive payloads)
- ✅ You can request that data be deleted (DELETE /auth/me → 30일 유예)
- ✅ Committed to follow the Play Families Policy: N/A (만 4세+)

---

## 6. 심사 우려 사항 & 대응

### Apple — App Review Guidelines

**우려 1 — 1.4.1 Safety / Physical Harm**
> "Apps that are designed for performing dangerous activities" 와 혼동될 수 있음.
>
> **대응**: 앱 소개에 "보조적 안전망입니다. 의료·응급 보장 X. 응급 시 119 연락." 명시.
> 카테고리는 "생산성" 또는 "라이프스타일" — Medical 카테고리 회피.

**우려 2 — 5.1 Privacy / Data Collection**
> 민감 정보(비밀번호·시드) 저장에 대한 검토자 우려 가능.
>
> **대응**: 입력 선택사항이고 Fernet 암호화·본인 전용 열람을 명시. App Privacy 라벨에 "Sensitive Info — Encrypted at rest" 표시.

**우려 3 — 4.5.4 Push Notifications / Critical Alerts**
> 보호자 알림을 Critical Alerts 로 보낼 경우 별도 entitlement 필요.
>
> **대응**: v1.0 에서는 일반 푸시 알림 + 이메일 fallback 만. Critical Alerts entitlement 는 v1.x 이후.

### Google — Play Store

**우려 1 — Sensitive permissions (POST_NOTIFICATIONS, FOREGROUND_SERVICE)**
> Android 13+ 의 POST_NOTIFICATIONS, 백그라운드 활동 감지의 권한 사용 사유 명시 필요.
>
> **대응**: Permission Declaration 에서 "안부 체크 알림" 용도 명시.

**우려 2 — Pre-launch report — Crash on launch**
> 신규 앱 자동 크롤링에서 크래시 발생 시 게시 차단.
>
> **대응**: 출시 전 TestFlight / Internal Testing 으로 5+ 디바이스 검증.

---

## 7. 출시 후 운영 체크리스트

| 항목 | 빈도 | 도구 |
| --- | --- | --- |
| 리뷰·평점 모니터링 | 주 1회 | App Store Connect / Play Console |
| 크래시·ANR 추적 | 매일 | Sentry / Crashlytics |
| 발송 알림 도달률 | 매일 | 자체 로그 집계 |
| 신규 OS 베타 호환성 | 분기 | Expo SDK 업데이트 |
| 개인정보처리방침 갱신 | 변경 시 즉시 | 약관 동의 버전 재수집 |

---

## 8. 마케팅·홍보 자료 우선순위

지금 갖춰진 것:
- ✅ 앱 아이콘 (icon.png 1024×1024)
- ✅ 어댑티브 아이콘 (adaptive-icon.png)
- ✅ 스플래시 (splash.png 1242×2688)
- ✅ 파비콘 (favicon.png 48×48)

추후 필요한 것 (디자이너 / 마케터 필요):
- 스토어 스크린샷 (iOS 6.7" / 6.5" / 5.5", Android 폰)
- 프로모션 비디오 (15초)
- 프레스 키트 (로고 변형·컬러 가이드·1-pager)
- 랜딩 페이지 (inrem.app 도메인)
