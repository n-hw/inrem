#!/usr/bin/env python3
"""
Render InRem brand SVGs into the PNG sizes Expo / iOS / Android stores expect.

Sources: ``front/assets/brand/*.svg``
Targets: ``front/assets/*.png``

Run from project root:
    python3 scripts/build_brand_assets.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import cairosvg
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
BRAND = ROOT / "front" / "assets" / "brand"
OUT = ROOT / "front" / "assets"


def render_svg(svg_path: Path, png_path: Path, size: int | tuple[int, int]) -> None:
    """Rasterize an SVG to PNG at the given size (px)."""
    if isinstance(size, tuple):
        w, h = size
    else:
        w = h = size
    cairosvg.svg2png(
        url=str(svg_path),
        write_to=str(png_path),
        output_width=w,
        output_height=h,
    )
    print(f"  → {png_path.relative_to(ROOT)}  ({w}×{h})")


def main() -> int:
    if not BRAND.exists():
        print(f"❌  source folder missing: {BRAND}")
        return 1

    print("🎨  Rendering InRem brand assets…\n")

    print("• App icon (iOS + fallback)")
    render_svg(BRAND / "icon.svg", OUT / "icon.png", 1024)
    render_svg(BRAND / "icon.svg", OUT / "logo.png", 1024)
    render_svg(
        BRAND / "icon.svg",
        OUT / "logo_with_background.png",
        1024,
    )

    print("\n• Android adaptive icon (foreground)")
    render_svg(BRAND / "adaptive-foreground.svg", OUT / "adaptive-icon.png", 1024)

    print("\n• Splash screen")
    # Expo splash 는 정사각형 PNG + backgroundColor 조합이 가장 잘 동작.
    # 다만 splash-icon 은 중앙 정렬용이라 정사각으로 자른 버전을 사용.
    render_svg(BRAND / "splash.svg", OUT / "splash.png", (1242, 2688))
    # Center crop the splash for splash-icon (Expo 가 cover 모드로 확장).
    render_svg(BRAND / "icon.svg", OUT / "splash-icon.png", 1024)

    print("\n• Favicon (web)")
    render_svg(BRAND / "icon.svg", OUT / "favicon.png", 48)

    print("\n✅  Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
