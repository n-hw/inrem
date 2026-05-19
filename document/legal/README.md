# InRem Legal Documents — 작업 가이드

이 디렉토리는 출시 전 **법무 검토가 필요한 문서의 스켈레톤** 입니다.

## 🚨 상태: 초안 (법적 효력 없음)

본 문서들은 개발팀이 변호사 자문 전에 작성한 **개발용 베이스라인**입니다. 출시 전 반드시 다음을 수행하세요:

1. **법무 자문**: 한국 변호사(개인정보보호법 전문) 검토 필수.
2. **`{{TBD}}` 치환**: 회사명·대표자·주소·연락처·DPO 등 placeholders 채우기.
3. **버전·날짜 기재**: 발효일, 개정 이력 표기.
4. **이용자 동의 흐름**: 가입·온보딩 화면에서 약관·정책 동의 체크박스 + 버전 저장.

## 파일

- `privacy_policy.md` — 개인정보처리방침 (PIPA 기반)
- `terms_of_service.md` — 서비스 이용약관

## 관련 코드

- 계정 삭제 (잊혀질 권리): `back/app/services/account_service.py`, `back/app/api/v1/auth.py` (`DELETE /auth/me`, `POST /auth/me/restore`)
- 30일 grace 후 영구 삭제 cron: **미구현 (TODO)** — `back/app/services/scheduler.py` 에 sweep job 추가 필요.
- 민감정보 암호화: `back/app/services/asset_service.py` (Fernet)
- 시크릿 reveal 감사 로그: logger `inrem.audit.heritage`
- 계정 삭제 감사 로그: logger `inrem.audit.account`
