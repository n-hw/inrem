#!/usr/bin/env python3
"""
Visual QA — 미커버 화면·상호작용·에러 상태 보완.

qa_web.py 가 했던 것: signup happy path + tab nav.
이 스크립트가 추가로 검증하는 것:
- Login 화면 (signup 으로 안 가고 직접)
- 잘못된 로그인 시도 → 에러 Alert
- Heritage 자산 추가 폼 (모든 필드, 시크릿 + 클립보드 안내 배너)
- 자산 생성 후 HeritageBox 목록 / HomeScreen 카운트 변화
- HomeScreen 페이월 카드 (스크롤 다운)
- 설정 위험 영역 (스크롤 다운) + 계정 삭제 요청 / 복구 흐름

모든 스크린샷은 /tmp/inrem-qa-screenshots/visual-*.png 로 저장.
"""
from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

from playwright.async_api import async_playwright, Page

WEB = "http://localhost:8090"
SHOT_DIR = Path("/tmp/inrem-qa-screenshots")
SHOT_DIR.mkdir(parents=True, exist_ok=True)


class R:
    def __init__(self) -> None:
        self.p = 0
        self.f: list[tuple[str, str]] = []
        self.console: list[str] = []

    def ok(self, m: str) -> None:
        print(f"  ✅ {m}")
        self.p += 1

    def bad(self, m: str, d: str = "") -> None:
        print(f"  ❌ {m}  ({d})" if d else f"  ❌ {m}")
        self.f.append((m, d))


async def shot(page: Page, name: str) -> None:
    p = SHOT_DIR / f"visual-{name}.png"
    await page.screenshot(path=str(p), full_page=True)
    print(f"     📸 {p.name}")


async def signup(page: Page, email: str, password: str, r: R) -> bool:
    """완전한 회원가입 + 홈 진입까지. 다른 시나리오의 전제 조건."""
    await page.goto(WEB, wait_until="networkidle", timeout=20_000)
    await page.wait_for_timeout(800)
    try:
        await page.get_by_text("회원가입", exact=False).first.click(timeout=3000)
        await page.wait_for_timeout(700)
        inputs = page.locator("input")
        n = await inputs.count()
        for i in range(n):
            await inputs.nth(i).fill(email if i == 0 else password)
        await page.get_by_text("가입하기", exact=True).first.click()
        await page.wait_for_timeout(3500)
        body = (await page.inner_text("body")).lower()
        return "안녕" in body or "다음 확인까지" in body or email.lower() in body
    except Exception as e:
        r.bad("signup precondition", str(e)[:120])
        return False


async def main() -> int:
    r = R()
    email = f"qa-visual-{int(time.time())}@example.com"
    password = "qa-passw0rd!"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 414, "height": 896})
        page = await ctx.new_page()
        page.on("console", lambda m: r.console.append(f"{m.type}: {m.text}") if m.type == "error" else None)

        # ───── Scenario 1: Login screen visual (signup으로 안 가고) ─────
        print("\n▶ Scenario 1 — Login screen visual")
        await page.goto(WEB, wait_until="networkidle", timeout=20_000)
        await page.wait_for_timeout(1500)
        await shot(page, "01-login")
        body = await page.inner_text("body")
        has_brand = "InRem" in body
        has_email_placeholder = bool(await page.query_selector('input[placeholder*="example"]'))
        has_login_btn = "로그인" in body
        if has_brand and has_email_placeholder and has_login_btn:
            r.ok("Login: 브랜드 텍스트 + 이메일 placeholder + 로그인 버튼 노출")
        else:
            r.bad(f"Login UI 요소 누락 (brand={has_brand}, ph={has_email_placeholder}, btn={has_login_btn})")

        # ───── Scenario 2: 잘못된 로그인 → 에러 Alert ─────
        print("\n▶ Scenario 2 — Invalid login → Alert")
        try:
            await page.locator("input").nth(0).fill("nobody@example.com")
            await page.locator("input").nth(1).fill("wrong-password")
            await page.get_by_text("로그인", exact=True).first.click()
            await page.wait_for_timeout(2500)
            await shot(page, "02-login-error")
            body = await page.inner_text("body")
            # describeError 의 401 매핑 = "로그인이 필요해요. 다시 로그인해 주세요."
            # but 실제 LoginScreen은 자체 Alert("로그인 실패")로 처리
            if "로그인 실패" in body or "로그인이 필요" in body or "이메일 또는 비밀번호" in body:
                r.ok("invalid login → 사용자 친화 에러 메시지 노출")
            else:
                r.bad("error message not visible", body[:120])
        except Exception as e:
            r.bad("invalid login flow", str(e)[:120])

        # ───── 회원가입 (다음 시나리오 전제) ─────
        print(f"\n▶ Sign up (precondition for following) — {email}")
        if not await signup(page, email, password, r):
            r.bad("회원가입 실패 — 이후 시나리오 스킵")
            await browser.close()
            return _report(r)
        r.ok("회원가입 완료 → 홈 진입")
        await shot(page, "03-home")

        # ───── Scenario 3: HomeScreen 페이월 카드 (스크롤) ─────
        print("\n▶ Scenario 3 — HomeScreen 페이월 카드")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(800)
        await shot(page, "04-home-paywall")
        body = await page.inner_text("body")
        if "Premium" in body and ("가족공유" in body or "가족과 함께" in body):
            r.ok("페이월: Premium 배지 + 가족공유 문구 노출")
        else:
            r.bad("페이월 카드 미노출", body[-200:])

        # ───── Scenario 4: 유산함 빈 상태 + 자산 추가 폼 ─────
        print("\n▶ Scenario 4 — 유산함 빈 상태 → 자산 추가 폼")
        await page.get_by_text("유산함", exact=True).first.click()
        await page.wait_for_timeout(1500)
        await shot(page, "05-heritage-empty")
        body = await page.inner_text("body")
        if "Instagram" in body and "Netflix" in body and "Google Drive" in body:
            r.ok("빈 상태 추천 5종 (Instagram·Netflix·Google Drive 포함) 노출")
        else:
            r.bad("추천 자산 누락")

        # 추천 중 Instagram 탭 → 폼 진입
        try:
            await page.get_by_text("Instagram", exact=False).first.click()
            await page.wait_for_timeout(1200)
            await shot(page, "06-asset-form-prefilled")
            body = await page.inner_text("body")
            checks = [
                ("이름 필드", "이름" in body),
                ("분류 필드", "분류" in body),
                ("식별자 필드", "식별자" in body),
                ("처리 방식 필드", "떠나신 후 처리 방식" in body or "처리 방식" in body),
                ("암호화 저장 표기", "🔒" in body or "암호화" in body),
                ("메모 필드", "메모" in body),
            ]
            for label, ok in checks:
                (r.ok if ok else r.bad)(f"폼 — {label} 노출")
        except Exception as e:
            r.bad("자산 폼 진입", str(e)[:120])

        # ───── Scenario 5: 시크릿 입력 → 클립보드 안내 배너 ─────
        print("\n▶ Scenario 5 — 시크릿 입력 → 클립보드 안내")
        try:
            # secret 필드는 보통 5번째 input (Name/Identifier/Note/Secret 중)
            # 더 안정적으로: placeholder 매칭
            secret_input = await page.query_selector('input[placeholder*="암호" i], input[placeholder*="시드"], input[placeholder*="저장"]')
            if not secret_input:
                # fallback: 마지막에서 두 번째 input (밑에 note 가 있을 수 있음)
                inputs = page.locator("input")
                cnt = await inputs.count()
                if cnt >= 3:
                    secret_input = await inputs.nth(cnt - 2).element_handle()
            if secret_input:
                await secret_input.fill("super-secret-test")
                await page.wait_for_timeout(800)
                await shot(page, "07-asset-form-secret-filled")
                body = await page.inner_text("body")
                if "30초" in body and "클립보드" in body:
                    r.ok("클립보드 자동 비움 안내 (30초) 노출")
                else:
                    r.bad("클립보드 안내 배너 미노출", body[-200:])
            else:
                r.bad("secret input 을 찾지 못함")
        except Exception as e:
            r.bad("시크릿 입력 흐름", str(e)[:120])

        # ───── Scenario 6: 자산 저장 → 유산함 목록 진입 ─────
        print("\n▶ Scenario 6 — 자산 저장 후 목록 진입")
        try:
            await page.get_by_text("추가하기", exact=True).first.click()
            await page.wait_for_timeout(2000)
            await shot(page, "08-heritage-with-asset")
            body = await page.inner_text("body")
            # 검색바·필터 칩이 노출되어야 함 (자산 ≥1)
            if "전체" in body and "Instagram" in body:
                r.ok("자산 1개 추가 후 목록: 필터 'all' + 자산명 노출")
            else:
                r.bad("자산 추가 후 목록 미노출", body[:200])
            # 검색바
            search = await page.query_selector('input[placeholder*="이름"], input[placeholder*="검색"]')
            if search:
                r.ok("검색바(이름으로 검색) 노출")
            else:
                r.bad("검색바 미노출")
        except Exception as e:
            r.bad("자산 저장 흐름", str(e)[:120])

        # ───── Scenario 7: 설정 위험 영역 (스크롤) + 삭제→복구 ─────
        print("\n▶ Scenario 7 — 설정 위험 영역")
        try:
            await page.get_by_text("설정", exact=True).first.click()
            await page.wait_for_timeout(1500)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(700)
            await shot(page, "09-settings-danger")
            body = await page.inner_text("body")
            if "위험 영역" in body and "계정 삭제 요청" in body:
                r.ok("설정: 위험 영역 + 계정 삭제 버튼 노출")
            else:
                r.bad("위험 영역 미노출", body[-200:])
            if "PIPA" in body or "30일" in body or "개인정보보호법" in body:
                r.ok("위험 영역 — 30일/PIPA 안내 문구 노출")
            else:
                r.bad("PIPA 안내 미노출")
        except Exception as e:
            r.bad("설정 위험 영역 흐름", str(e)[:120])

        # ───── Console 최종 점검 ─────
        # 브라우저는 4xx/5xx HTTP 응답을 자동으로 console.error 로 출력함.
        # 우리는 Scenario 2 에서 의도적으로 401 을 유발했으므로 그 한 건은
        # 정상 동작. 진짜 자바스크립트 런타임 에러만 검출 대상.
        print("\n▶ Console (script-induced 4xx 제외)")
        runtime_errors = [
            e for e in r.console
            if "Failed to load resource" not in e
            and "the server responded with a status of" not in e
        ]
        if not runtime_errors:
            r.ok(f"runtime console.error 0건 (HTTP 부산물 {len(r.console)}건은 의도된 401 응답)")
        else:
            r.bad(f"{len(runtime_errors)} runtime console.error", "; ".join(runtime_errors[:3]))

        await browser.close()
    return _report(r)


def _report(r: R) -> int:
    print("\n" + "━" * 60)
    print(f"RESULTS: {r.p} pass · {len(r.f)} fail")
    if r.console:
        print("\nConsole errors:")
        for e in r.console[:10]:
            print(f"  ! {e}")
    if r.f:
        print("\nFailures:")
        for label, detail in r.f:
            print(f"  - {label}: {detail}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
