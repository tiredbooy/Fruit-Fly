# Completion gates
Run from repository root:
1. `make test` must report zero failures.
2. `make data-status` must end with "Status: data is valid and ready".
3. Full-engine work must also run `make brain-status`, `make brain-benchmark`, and a finite `main.py run --brain full` smoke.
4. Frontend work must run `make frontend-build`, `make frontend-test`, and a desktop/mobile real-browser check with a clean console. Test asset-load failure and paused reload; inspect real screenshots, not just a backend label. Report unverified native WebGPU explicitly when no adapter is available.
5. `make help` must list run, web, tests, and data/brain management.
6. `git diff --check` must exit 0.
7. Terminal-visible text stays English/ASCII except the explicit fly emoji. Browser regression scripts may contain the real Persian UI labels they verify.
8. Inspect brain/ and world/ imports: neither package may import the other.
For runtime changes, also run a finite CLI smoke with a temporary --memory-file and inspect the rendered frame/persisted JSON.
Gym work uses --memory-dir in a temporary path and compares learning on/off.
Check real population1-10-1, selected-fly readings, anatomical pixels, no observer
commands, missing assets and narrow Persian controls via scripts/check_gym_browser.py.
