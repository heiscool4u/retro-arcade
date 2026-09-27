"""배포 전후 공통 점검: JS 오류, 가로 넘침, 폰 화면 안에 들어가는지. 스크린샷은 tools/out/에 남긴다.

사용: python3 tools/smoke.py <게임 URL>
"""
import os, sys
from playwright.sync_api import sync_playwright

url = sys.argv[1]
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(out, exist_ok=True)
fails = []

with sync_playwright() as pw:
    b = pw.chromium.launch()
    for name, vw, vh, mobile in [("pc", 1280, 800, False), ("iphone", 390, 664, True), ("galaxy", 360, 640, True)]:
        ctx = b.new_context(viewport={"width": vw, "height": vh}, is_mobile=mobile, has_touch=mobile,
                            device_scale_factor=2 if mobile else 1)
        page = ctx.new_page()
        errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))
        page.on("console", lambda m: m.type == "error" and errs.append(m.text))
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(500)
        box = page.evaluate("""(() => { let bottom = 0;
            for (const el of document.querySelectorAll('#app > *')) bottom = Math.max(bottom, el.getBoundingClientRect().bottom);
            return { sw: document.documentElement.scrollWidth, bottom }; })()""")
        if errs: fails.append(f"{name}: JS 오류 {errs}")
        if box["sw"] > vw: fails.append(f"{name}: 가로 넘침 {box['sw']}px > {vw}px")
        if box["bottom"] > vh: fails.append(f"{name}: 세로 넘침 {box['bottom']:.0f}px > {vh}px")
        page.screenshot(path=f"{out}/{name}.png")
        ctx.close()
    b.close()

print("\n".join(fails) if fails else "OK: JS 오류 0, 넘침 없음 (pc/iphone/galaxy)")
sys.exit(1 if fails else 0)
