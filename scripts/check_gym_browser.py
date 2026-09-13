"""Real gym browser acceptance checks; no simulated telemetry or fake fly state."""
import argparse
import json
import re
import subprocess
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


def check_population_validation(page: Page, commands: list[dict]) -> None:
    """Invalid counts stay local and readable in Persian in an English browser."""
    count = page.locator("#fly-count")
    failures = []
    sent = sum(command.get("type") == "set_population" for command in commands)
    for value in ("", "1.5", "0", "11"):
        count.fill(value)
        page.locator("#apply-population").click()
        page.wait_for_timeout(100)
        message = count.evaluate("input => input.validationMessage")
        if not re.search(r"[\u0600-\u06ff]", message) or re.search(r"[A-Za-z]", message):
            failures.append(f"Count {value!r} validation is not Persian: {message!r}")
        if page.locator("#population-status").inner_text() != message:
            failures.append(f"Count {value!r} validation is missing from its accessible status")
        assert count.evaluate("input => !input.validity.valid && input === document.activeElement")
        assert sum(command.get("type") == "set_population" for command in commands) == sent, "Invalid count sent a population command"
    assert not failures, "\n".join(failures)
    count.fill("1")
    assert count.evaluate("input => input.validity.valid && input.validationMessage === ''"), "Valid input retained a stale validation error"
    page.locator("#apply-population").click()
    page.wait_for_function("document.querySelector('#scene').dataset.population === '1' && !document.querySelector('#apply-population').disabled")
    assert sum(command.get("type") == "set_population" for command in commands) == sent + 1


def check_mobile_connection(page: Page, width: int) -> None:
    """The live connection remains visible and fits inside a narrow viewport."""
    connection = page.locator(".connection")
    assert connection.is_visible(), f"Live connection is hidden at {width}px"
    assert connection.get_attribute("aria-live") == "polite"
    assert page.locator("#connection-label").inner_text() == "زنده"
    assert page.locator("#connection-dot").is_visible()
    bounds = connection.bounding_box()
    assert bounds and bounds["x"] >= 0 and bounds["x"] + bounds["width"] <= width
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


def check(url: str, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path="/usr/bin/google-chrome-stable", headless=True,
            args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, locale="en-US")
        errors, commands, observed = [], [], {}
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)

        def watch(socket):
            def receive(payload):
                message = json.loads(payload)
                if message.get("type") == "gym_frame":
                    observed["frame"] = message
            socket.on("framereceived", receive)
            socket.on("framesent", lambda payload: commands.append(json.loads(payload)))

        page.on("websocket", watch)
        page.goto(f"{url}?renderer=webgl")
        page.wait_for_load_state("networkidle")
        page.wait_for_function("document.querySelector('#scene').dataset.model === 'authored-rig'", timeout=60000)
        page.wait_for_function("document.querySelector('#neuron-map').dataset.anatomy === 'ready'", timeout=60000)
        page.wait_for_function("document.querySelector('#connection-label').textContent === 'زنده'")
        assert page.locator("#population-form").is_visible()
        assert page.locator("#graphics-backend").inner_text() == "WebGL2"
        assert page.locator("#scene canvas").count() == 1
        if page.locator("#running-toggle").inner_text() == "توقف":
            page.locator("#running-toggle").click()
        page.get_by_role("button", name="ادامه", exact=True).wait_for()
        check_population_validation(page, commands)
        paused = page.locator("#step-value").inner_text()
        page.locator("#fly-count").fill("10")
        page.locator("#apply-population").click()
        page.wait_for_function("document.querySelector('#scene').dataset.population === '10'")
        assert page.locator("#step-value").inner_text() == paused
        assert page.locator("#fly-picker button").count() == 10
        sent = len(commands)
        page.locator('#fly-picker [data-fly="fly-10"]').click()
        page.wait_for_function("document.querySelector('#training-instrument').dataset.fly === 'fly-10'")
        frame = next(fly["frame"] for fly in observed["frame"]["flies"] if fly["id"] == "fly-10")
        page.locator(".neuron-details summary").click()
        rows = page.locator("#active-neurons li")
        assert rows.count() == len(frame["neural"]["active"])
        by_id = {record["body_id"]: record for record in frame["neural"]["active"]}
        for row in rows.all():
            record = by_id[int(row.locator(".neuron-id").inner_text())]
            assert row.locator(".neuron-identity").inner_text() == record["label"]
            assert float(row.locator(".neuron-activity-value").inner_text()) == record["activity"]
        page.locator("#neuron-search").fill("NO_SUCH_LABEL")
        assert page.locator("#neuron-map").get_attribute("data-observed") == "0"
        page.locator("#neuron-search").fill("")
        assert int(page.locator("#neuron-map").get_attribute("data-observed")) > 0
        page.locator(".neuron-details summary").click()
        page.locator("#view-eye").click()
        assert page.locator("#scene canvas").get_attribute("tabindex") == "-1"
        assert page.locator("#camera-approximation").is_visible()
        page.locator("#view-overview").click()
        assert len(commands) == sent, "Observer controls mutated simulation"
        page.locator("#running-toggle").click()
        page.wait_for_function(f"Number(document.querySelector('#step-value').textContent) > {int(paused) + 5}")
        page.locator("#running-toggle").click()
        page.get_by_role("button", name="ادامه", exact=True).wait_for()
        page.wait_for_timeout(300)
        anatomy_capture = output / "anatomy.png"
        page.locator("#neuron-map canvas").screenshot(path=str(anatomy_capture))
        bright_pixels = subprocess.check_output(["magick", str(anatomy_capture), "-fx",
            "r>0.31 && r>g*1.3 && b>g*1.2?1:0", "-format", "%[fx:mean*w*h]", "info:"], text=True)
        assert float(bright_pixels) > 15, "Actual positive neural activity is not visibly highlighted"
        page.screenshot(path=str(output / "desktop.png"), full_page=True)
        page.locator("#view-fly").click()
        page.wait_for_timeout(300)
        page.screenshot(path=str(output / "fly.png"), full_page=True)
        page.locator("#neuron-map canvas").screenshot(path=str(output / "anatomy-after-camera.png"))
        remaining_pixels = subprocess.check_output(["magick", str(output / "anatomy-after-camera.png"), "-fx",
            "r>0.31 && r>g*1.3 && b>g*1.2?1:0", "-format", "%[fx:mean*w*h]", "info:"], text=True)
        assert float(remaining_pixels) > 15, "Paused neural view disappeared after changing the world camera"
        page.locator("#view-eye").click()
        page.wait_for_timeout(300)
        page.screenshot(path=str(output / "eye.png"), full_page=True)
        pause_step = page.locator("#step-value").inner_text()
        page.reload()
        page.wait_for_load_state("networkidle")
        page.wait_for_function("document.querySelector('#scene').dataset.population === '10'")
        assert page.locator("#step-value").inner_text() == pause_step
        page.locator("#fly-count").fill("1")
        page.locator("#apply-population").click()
        page.wait_for_function("document.querySelector('#scene').dataset.population === '1'")
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(300)
        check_mobile_connection(page, 390)
        page.screenshot(path=str(output / "mobile.png"), full_page=True)
        page.set_viewport_size({"width": 320, "height": 740})
        page.wait_for_timeout(200)
        check_mobile_connection(page, 320)
        for control in page.locator("#population-form input, #population-form button, .scene-controls button").all():
            bounds = control.bounding_box()
            assert bounds["x"] >= 0 and bounds["x"] + bounds["width"] <= 320
        assert not errors, errors
        page.locator("#running-toggle").click()
        failed = browser.new_page()
        failed.route("**/neuron-positions.json", lambda route: route.abort())
        failed.route("**/*.glb", lambda route: route.abort())
        failed.goto(f"{url}?renderer=webgl")
        failed.wait_for_function("document.querySelector('#neuron-map').dataset.anatomy === 'failed'")
        failed.wait_for_function("document.querySelector('#scene-loading').textContent.includes('بارگذاری نشد')")
        before = int(failed.locator("#step-value").inner_text())
        failed.wait_for_function(f"Number(document.querySelector('#step-value').textContent) > {before + 2}")
        assert failed.locator("#active-neurons li").count() > 0
        assert failed.locator("#fly-count").is_enabled()
        assert failed.locator("#view-eye").is_disabled()
        browser.close()
        print(json.dumps({"gym": True, "population_1_10_1": True, "paused_resize": True,
            "persian_population_validation_en_US": True, "mobile_live_connection_320_390": True,
            "selected_fly_exact_neurons": True, "anatomical_map": True, "eye": True,
            "mobile_320_390": True, "asset_failure_preserves_simulation": True, "errors": errors}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8001")
    parser.add_argument("--output", type=Path, default=Path(".impeccable/review/gym"))
    options = parser.parse_args()
    check(options.url, options.output)
