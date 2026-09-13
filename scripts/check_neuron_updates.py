"""Verify DOM reuse on real streamed neuron readings, without fake telemetry."""

import argparse
import json
from playwright.sync_api import sync_playwright


def check(url: str) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path="/usr/bin/google-chrome-stable",
            headless=True, args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        page = browser.new_page()
        page.goto(f"{url}?renderer=webgl")
        page.wait_for_function("document.querySelectorAll('#active-neurons li').length > 0")
        if page.locator("#running-toggle").inner_text() == "ادامه":
            page.locator("#running-toggle").click()
        page.evaluate("""() => {
            window.initialStep = Number(document.querySelector('#step-value').textContent);
            window.neuronRows = new Map(Array.from(document.querySelectorAll('#active-neurons li'),
                row => [row.querySelector('.neuron-id').textContent, row]));
            window.roleValues = Array.from(document.querySelectorAll('#role-list dd'));
            document.querySelector('#neuron-search').focus();
        }""")
        page.wait_for_function("Number(document.querySelector('#step-value').textContent) >= window.initialStep + 10")
        result = page.evaluate("""() => ({
            received: window.neuronRows.size,
            retained: Array.from(document.querySelectorAll('#active-neurons li')).filter(row =>
                window.neuronRows.get(row.querySelector('.neuron-id').textContent) === row).length,
            rolesRetained: window.roleValues.every(row => row.isConnected),
            focusRetained: document.activeElement === document.querySelector('#neuron-search')
        })""")
        browser.close()
        print(json.dumps(result))
        assert result["received"] == result["retained"], "Live neuron updates replaced existing rows"
        assert result["rolesRetained"], "Live updates rebuilt descending-neuron rows"
        assert result["focusRetained"], "Neuron updates stole search focus"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8001")
    check(parser.parse_args().url)
