"""Observe real bench/curl strokes, paused poses and responsive equipment UI.

Run against a fresh gym server: initial station contact is experimental setup,
not a browser-generated exercise command. Screenshots use actual WebGL2 frames.
"""

import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright


def check(url: str, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path="/usr/bin/google-chrome-stable",
            headless=True, args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        page = browser.new_page(viewport={"width":1440,"height":1000}, locale="en-US")
        errors, commands = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        page.on("websocket", lambda socket: socket.on("framesent", lambda payload: commands.append(json.loads(payload))))
        page.add_init_script("""() => {
            const NativeSocket = window.WebSocket;
            window.WebSocket = class extends NativeSocket {
                constructor(...args) {
                    super(...args);
                    this.addEventListener('message', event => {
                        const message = JSON.parse(event.data);
                        if (message.type === 'gym_frame') window.gymFrame = message;
                        if (message.type === 'hello') window.gymHello = message;
                    });
                }
            };
        }""".removeprefix("() => {").removesuffix("}"))
        page.goto(f"{url}?renderer=webgl", wait_until="domcontentloaded")
        page.wait_for_function("!document.querySelector('#running-toggle').disabled")
        if page.locator("#running-toggle").inner_text() == "توقف":
            page.locator("#running-toggle").click()
        page.wait_for_function("document.body.dataset.running === 'false'")
        page.wait_for_function("document.querySelector('#scene').dataset.model === 'authored-rig'", timeout=60000)
        page.wait_for_function("document.querySelector('#neuron-map').dataset.anatomy === 'ready'", timeout=60000)
        assert page.evaluate("window.gymHello.schema") == 3
        assert page.locator("#backend-label").inner_text() == "GYM · COMPACT"
        assert page.evaluate("window.gymHello.equipment.length") == 10

        # Rendering a paused frame does not advance either the Python stroke or UI.
        before = page.evaluate("JSON.stringify(window.gymFrame)")
        page.wait_for_timeout(250)
        assert page.evaluate("JSON.stringify(window.gymFrame)") == before

        page.locator("#running-toggle").click()
        page.wait_for_function("window.gymFrame.flies[0].exercise.phase === 'lifting' && window.gymFrame.flies[0].exercise.joint_position > .4")
        page.locator("#running-toggle").click()
        page.wait_for_function("document.body.dataset.running === 'false'")
        bench = page.evaluate("window.gymFrame.flies[0].exercise")
        assert bench["kind"] == "bench_press" and bench["joint_position"] > .4
        page.evaluate("new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
        page.screenshot(path=str(output / "desktop.png"), full_page=True)
        sent = len(commands)
        page.locator("#view-fly").click()
        page.wait_for_timeout(400)
        page.screenshot(path=str(output / "bench.png"), full_page=True)
        assert page.locator("#exercise-name").inner_text() == "پرس سینه"
        page.locator('[data-fly="fly-2"]').click()
        page.locator("#view-fly").click()
        page.wait_for_timeout(400)
        assert page.locator("#exercise-name").inner_text() == "جلو بازو"
        page.screenshot(path=str(output / "curl.png"), full_page=True)
        assert len(commands) == sent, "Observation changed physical control"

        page.locator("#running-toggle").click()
        page.wait_for_function("window.gymFrame.flies[0].exercise.repetitions >= 3 && window.gymFrame.flies[1].exercise.repetitions >= 3")
        page.locator("#running-toggle").click()
        page.wait_for_function("document.body.dataset.running === 'false'")
        frame = page.evaluate("window.gymFrame")
        assert all(fly["training"]["sets"] >= 1 for fly in frame["flies"][:2])
        assert int(page.locator("#exercise-reps").inner_text()) == frame["flies"][1]["exercise"]["repetitions"]
        assert page.locator("#exercise-phase").inner_text() == "بازیابی"
        page.locator("#view-overview").click()
        page.set_viewport_size({"width":390,"height":844})
        page.wait_for_timeout(400)
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        assert page.locator(".connection").is_visible()
        page.screenshot(path=str(output / "mobile.png"), full_page=True)
        page.set_viewport_size({"width":320,"height":760})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        browser.close()
        assert not errors, errors
        print(json.dumps({"schema":3,"bench_position":bench["joint_position"],
            "repetitions":[fly["exercise"]["repetitions"] for fly in frame["flies"]],
            "sets":[fly["training"]["sets"] for fly in frame["flies"]],"errors":errors}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8001")
    parser.add_argument("--output", type=Path, default=Path(".impeccable/review/equipment"))
    args = parser.parse_args()
    check(args.url,args.output)
