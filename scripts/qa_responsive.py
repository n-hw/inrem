#!/usr/bin/env python3
"""
Responsive viewport QA.

같은 빌드를 5개 viewport 에서 회원가입 → 홈 진입까지 자동 시나리오로
띄우고, 각 화면에서 스크린샷 캡처. 모바일 디자인이 모든 viewport 에서
일관되게 표시되는지 시각으로 확인.

Viewport 매트릭스:
    phone-small   (320x568)   iPhone SE 1세대
    phone         (414x896)   iPhone 14 Pro Max
    tablet        (768x1024)  iPad
    desktop       (1280x900)  일반 데스크톱
    desktop-xl    (1920x1080) FHD 모니터
"""
from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

from playwright.async_api import async_playwright

WEB = "http://localhost:8090"
SHOT = Path("/tmp/inrem-qa-screenshots")
SHOT.mkdir(parents=True, exist_ok=True)

VIEWPORTS = [
    ("phone-small", 320, 568),
    ("phone", 414, 896),
    ("tablet", 768, 1024),
    ("desktop", 1280, 900),
    ("desktop-xl", 1920, 1080),
]


async def signup_and_capture(p, label: str, w: int, h: int) -> tuple[str, bool, str]:
    browser = await p.chromium.launch(headless=True)
    ctx = await browser.new_context(viewport={"width": w, "height": h})
    page = await ctx.new_page()
    detail = ""
    ok = True

    try:
        await page.goto(WEB, wait_until="networkidle", timeout=20_000)
        await page.wait_for_timeout(1000)

        # 1. Login 화면 스크린샷
        await page.screenshot(path=str(SHOT / f"resp-{label}-1-login.png"), full_page=False)

        # 2. 회원가입 → 홈 진입
        await page.get_by_text("회원가입", exact=False).first.click()
        await page.wait_for_timeout(700)
        inputs = page.locator("input")
        n = await inputs.count()
        email = f"qa-resp-{label}-{int(time.time())}@example.com"
        for i in range(n):
            await inputs.nth(i).fill(email if i == 0 else "passw0rd!1234")
        await page.get_by_text("가입하기", exact=True).first.click()
        await page.wait_for_timeout(3500)

        # 3. 홈 화면 스크린샷
        await page.screenshot(path=str(SHOT / f"resp-{label}-2-home.png"), full_page=False)

        # 4. 유산함 탭
        try:
            await page.get_by_text("유산함", exact=True).first.click(timeout=3000)
            await page.wait_for_timeout(1500)
            await page.screenshot(path=str(SHOT / f"resp-{label}-3-heritage.png"), full_page=False)
        except Exception as e:
            ok = False
            detail = f"heritage tab: {str(e)[:80]}"

        # 5. 모바일 폭(MAX_CONTENT_WIDTH=480)이 정확히 적용됐는지 검증
        # ResponsiveShell의 inner 컨테이너 width를 측정
        inner_box = await page.evaluate("""
            () => {
                // 가장 먼저 maxWidth 가 480 으로 잡힌 element 를 찾음
                const all = document.querySelectorAll('*');
                for (const el of all) {
                    const cs = getComputedStyle(el);
                    if (cs.maxWidth === '480px') {
                        const r = el.getBoundingClientRect();
                        return { width: r.width, found: true };
                    }
                }
                return { found: false };
            }
        """)
        if not inner_box["found"]:
            ok = False
            detail = "ResponsiveShell inner 컨테이너 미발견"
        else:
            measured = inner_box["width"]
            expected = min(w, 480)
            if abs(measured - expected) > 2:
                ok = False
                detail = f"inner width {measured}, expected {expected}"

    except Exception as e:
        ok = False
        detail = f"setup failed: {str(e)[:120]}"
    finally:
        await browser.close()

    return label, ok, detail


async def main() -> int:
    print(f"\n▶ Responsive QA — {len(VIEWPORTS)} viewports\n")
    rows: list[tuple[str, bool, str]] = []
    async with async_playwright() as p:
        for label, w, h in VIEWPORTS:
            print(f"  [{label}] {w}×{h} …")
            r = await signup_and_capture(p, label, w, h)
            rows.append(r)
            mark = "✅" if r[1] else "❌"
            tail = f"  ({r[2]})" if r[2] else ""
            print(f"  {mark} {label}{tail}")

    print("\n" + "━" * 60)
    fails = [r for r in rows if not r[1]]
    print(f"RESULTS: {len(rows) - len(fails)}/{len(rows)}")
    if fails:
        for label, _, detail in fails:
            print(f"  - {label}: {detail}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
