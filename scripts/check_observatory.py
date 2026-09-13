"""Optional real-browser checks; run against an already running local observatory.

Requires Playwright in a separate development environment and Chromium/Chrome.
No browser tooling is needed by the simulation at runtime.
"""

import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright


def check(url: str, browser_path: str, output: Path, webgpu: bool) -> None:
    output.mkdir(parents=True, exist_ok=True)
    flags = ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
    if webgpu:
        # Test actual browser support; do not bypass the GPU driver's blocklist.
        flags = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=browser_path, headless=True, args=flags)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        errors = []
        warnings = []
        observed = {}
        commands = []
        page.on("websocket", lambda socket: watch_telemetry(socket, observed, commands))
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        page.on("console", lambda message: warnings.append(message.text) if message.type == "warning" else None)
        page.goto(url if webgpu else f"{url}?renderer=webgl")
        page.wait_for_load_state("networkidle")
        page.wait_for_function("document.querySelector('#scene').dataset.model === 'authored-rig'", timeout=60000)
        page.wait_for_function("document.querySelector('#neuron-map').dataset.anatomy === 'ready'", timeout=60000)
        page.wait_for_function("Number(document.querySelector('#step-value').textContent) > 2")
        backend = page.locator("#graphics-backend").inner_text()
        if webgpu and backend != "WebGPU":
            print(json.dumps({"warnings": warnings, "errors": errors}))
        assert backend == ("WebGPU" if webgpu else "WebGL2"), backend
        assert page.locator("#scene canvas").count() == 1
        assert page.locator("#scene-loading").is_hidden()
        assert page.locator("#population-form").is_hidden(), "Expected Experiment 1"
        scene_height = page.locator("#scene").bounding_box()["height"]
        chamber_height = page.locator(".chamber").bounding_box()["height"]
        assert scene_height > chamber_height / 2, f"Experiment 1 scene occupies only {scene_height}px of its {chamber_height}px chamber"
        page.wait_for_function("document.querySelector('#food-state').textContent === 'غذا در محیط'", timeout=30000)
        food_step = int(page.locator("#step-value").inner_text())
        page.wait_for_function(f"Number(document.querySelector('#step-value').textContent) > {food_step + 3}")
        page.get_by_role("button", name="توقف", exact=True).click()
        page.get_by_role("button", name="ادامه", exact=True).wait_for()
        paused = page.locator("#step-value").inner_text()
        page.wait_for_timeout(300)
        assert page.locator("#step-value").inner_text() == paused
        page.reload()
        page.wait_for_function("document.querySelector('#scene').dataset.model === 'authored-rig'")
        page.wait_for_function("document.querySelector('#neuron-map').dataset.anatomy === 'ready'", timeout=60000)
        page.get_by_role("button", name="ادامه", exact=True).wait_for()
        assert page.locator("#step-value").inner_text() == paused
        inspector_commands = len(commands)
        check_neuron_inspector(page, observed["frame"])
        assert len(commands) == inspector_commands, "Neuron search sent simulation commands"
        page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
        page.screenshot(path=str(output / "world.png"), full_page=True)
        page.get_by_role("button", name="دنبال کردن مگس", exact=True).click()
        page.wait_for_timeout(400)
        page.screenshot(path=str(output / "fly.png"), full_page=True)
        command_count = len(commands)
        page.locator("#view-eye").click()
        assert page.locator("#view-eye").get_attribute("aria-pressed") == "true"
        assert page.locator("#view-fly").get_attribute("aria-pressed") == "false"
        assert page.locator("#camera-approximation").is_visible()
        assert page.locator("#scene").get_attribute("aria-describedby") == "camera-approximation"
        assert page.locator("#scene canvas").get_attribute("tabindex") == "-1"
        assert "تقریبی" in page.locator("#scene canvas").get_attribute("aria-label")
        page.wait_for_timeout(400)
        page.screenshot(path=str(output / "eye.png"), full_page=True)
        page.locator("#scene canvas").focus()
        page.keyboard.press("+")
        page.keyboard.press("ArrowLeft")
        assert page.locator("#step-value").inner_text() == paused
        page.locator("#view-fly").click()
        assert page.locator("#view-eye").get_attribute("aria-pressed") == "false"
        assert page.locator("#scene").get_attribute("aria-describedby") == "camera-instructions"
        assert page.locator("#scene canvas").get_attribute("tabindex") == "0"
        assert "بزرگ‌نمایی" in page.locator("#scene canvas").get_attribute("aria-label")
        assert len(commands) == command_count, "Observer controls sent simulation commands"
        canvas = page.locator("#scene canvas")
        canvas.focus()
        page.keyboard.press("+")
        bounds = canvas.bounding_box()
        page.mouse.move(bounds["x"] + bounds["width"] / 2, bounds["y"] + bounds["height"] / 2)
        page.mouse.down()
        page.mouse.move(bounds["x"] + bounds["width"] / 2 + 100, bounds["y"] + bounds["height"] / 2 + 20, steps=8)
        page.mouse.up()
        page.get_by_role("button", name="نمای محیط", exact=True).click()
        page.get_by_role("button", name="ادامه", exact=True).click()
        page.wait_for_function(f"Number(document.querySelector('#step-value').textContent) > {paused}")
        search = page.locator("#neuron-search")
        search.fill("orn")
        before_search = int(page.locator("#step-value").inner_text())
        page.wait_for_function(f"Number(document.querySelector('#step-value').textContent) > {before_search + 3}")
        assert search.input_value() == "orn"
        assert search.evaluate("element => element === document.activeElement"), "Live frames stole search focus"
        search.fill("")
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(400)
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.get_by_role("button", name="دنبال کردن مگس", exact=True).click()
        page.wait_for_timeout(300)
        page.screenshot(path=str(output / "mobile.png"), full_page=True)
        page.locator("#view-eye").click()
        page.wait_for_timeout(300)
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path=str(output / "mobile-eye.png"), full_page=True)
        page.set_viewport_size({"width": 320, "height": 740})
        page.wait_for_timeout(200)
        scene_bounds = page.locator("#scene").bounding_box()
        for button in page.locator(".scene-controls button").all():
            bounds = button.bounding_box()
            assert bounds["x"] >= scene_bounds["x"], "Camera control clipped on a narrow screen"
            assert bounds["x"] + bounds["width"] <= scene_bounds["x"] + scene_bounds["width"], "Camera control clipped on a narrow screen"
        assert not errors, errors
        # A missing real asset must not stop telemetry or show a substitute fly.
        failed_page = browser.new_page()
        failed_page.route("**/*.glb", lambda route: route.abort())
        failed_page.goto(f"{url}?renderer=webgl")
        failed_page.wait_for_function("document.querySelector('#scene-loading').textContent.includes('بارگذاری نشد')")
        failed_step = int(failed_page.locator("#step-value").inner_text())
        failed_page.wait_for_function(f"Number(document.querySelector('#step-value').textContent) > {failed_step}")
        assert failed_page.locator("#view-fly").is_disabled()
        assert failed_page.locator("#view-eye").is_disabled()
        assert failed_page.locator("#scene-loading").is_visible()
        assert failed_page.locator("#neuron-search").is_enabled()
        assert failed_page.locator("#active-neurons li").count() > 0
        failed_page.close()
        check_context_loss(browser, url, during_load=True)
        check_context_loss(browser, url, during_load=False)
        print(json.dumps({"backend": backend, "errors": errors, "model": "authored-rig", "pause_resume": True, "paused_reload": True, "eye_view": True, "neuron_search": True, "observer_only": True, "mobile_overflow": False, "asset_failure_preserves_telemetry": True}))
        browser.close()


def watch_telemetry(socket, observed: dict, commands: list) -> None:
    """Capture actual traffic without replacing the simulation or its messages."""
    def receive(payload):
        message = json.loads(payload)
        if message.get("type") == "frame":
            observed["frame"] = message

    socket.on("framereceived", receive)
    socket.on("framesent", lambda payload: commands.append(json.loads(payload)))


def check_neuron_inspector(page, frame: dict) -> None:
    """Match rendered records and filtering to a real paused backend frame."""
    readings = frame["neural"]["active"]
    page.locator(".neuron-details").evaluate("element => { element.open = true; }")
    assert readings, "Expected actual compact-circuit telemetry"
    search = page.locator("#neuron-search")
    rows = page.locator("#active-neurons li")
    search.fill("")
    assert rows.count() == len(readings), "Inspector omitted received neurons"
    positive = sum(item["activity"] > 0 for item in readings)
    assert page.locator("#active-count").inner_text() == f"{positive} فعال از {len(readings)} دریافتی"
    for row, reading in zip(rows.all(), readings, strict=True):
        assert row.locator(".neuron-id").inner_text() == str(reading["body_id"])
        assert row.locator(".neuron-identity").inner_text() == reading["label"]
        assert float(row.locator(".neuron-activity-value").inner_text()) == reading["activity"]
        assert row.locator("meter").evaluate("element => element.value") == min(1, max(0, reading["activity"]))
    first = readings[0]
    search.fill(str(first["body_id"]))
    matches = [item for item in readings if str(first["body_id"]) in str(item["body_id"]) or str(first["body_id"]) in item["label"]]
    assert rows.count() == len(matches)
    assert str(first["body_id"]) in rows.first.inner_text()
    search.fill(first["label"].swapcase())
    matches = [item for item in readings if first["label"].lower() in item["label"].lower()]
    assert rows.count() == len(matches)
    search.fill("NO_SUCH_MALECNS_LABEL")
    assert rows.count() == 0
    search.fill("")
    assert rows.count() == len(readings)


def check_context_loss(browser, url: str, *, during_load: bool) -> None:
    """Lose a real WebGL context, including while its real GLB request is delayed."""
    page = browser.new_page()
    page.add_init_script("""(() => {
      const getContext = HTMLCanvasElement.prototype.getContext;
      HTMLCanvasElement.prototype.getContext = function(...args) {
        const context = getContext.apply(this, args);
        if (args[0] === 'webgl2' && context) {
          window.__testGlContexts ??= [];
          if (!window.__testGlContexts.includes(context)) window.__testGlContexts.push(context);
          this.addEventListener('webglcontextlost', () => { window.__testContextLost = true; });
        }
        return context;
      };
    })()""")
    pending = []
    if during_load:
        page.route("**/*.glb", lambda route: pending.append(route))
    page.goto(f"{url}?renderer=webgl", wait_until="domcontentloaded")
    page.wait_for_function("window.__testGlContexts?.length > 0")
    if during_load:
        # Let the request handler run without fulfilling the delayed asset.
        for _ in range(100):
            if pending:
                break
            page.wait_for_timeout(20)
        assert pending, "The GLB request was not intercepted"
    else:
        page.wait_for_function("document.querySelector('#scene').dataset.model === 'authored-rig'")
    # The anatomical viewer has its own context. Lose only the world renderer,
    # whose canvas is detached until the delayed body asset finishes loading.
    page.evaluate("""() => {
      const world = window.__testGlContexts.find(context =>
        !context.canvas.closest('#neuron-map'));
      if (!world) throw new Error('World context not found');
      world.getExtension('WEBGL_lose_context').loseContext();
    }""")
    page.wait_for_function("window.__testContextLost === true")
    if during_load:
        pending[0].continue_()
    page.wait_for_function("document.querySelector('#scene-loading').textContent.includes('بارگذاری نشد')", timeout=5000)
    step = int(page.locator("#step-value").inner_text())
    page.wait_for_function(f"Number(document.querySelector('#step-value').textContent) > {step + 3}")
    assert page.locator("#view-fly").is_disabled()
    assert page.locator("#scene-loading").is_visible()
    assert page.locator("#graphics-backend").inner_text() == "نمای سه‌بعدی قطع است"
    page.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--browser", default="/usr/bin/google-chrome-stable")
    parser.add_argument("--output", type=Path, default=Path(".impeccable/review/webgpu"))
    parser.add_argument("--webgpu", action="store_true")
    options = parser.parse_args()
    check(options.url, options.browser, options.output, options.webgpu)
