# Completion gates
Run from repository root:
1. `make test` must report zero failures.
2. `make data-status` must end with "Status: data is valid and ready".
3. Full-engine work must also run `make brain-status`, `make brain-benchmark`, and a finite `main.py run --brain full` smoke.
4. Frontend work must run `make frontend-build`, `cd frontend/web && bun test`, and a desktop/mobile real-browser check with a clean console.
5. `make help` must list run, web, tests, and data/brain management.
6. `git diff --check` must exit 0.
7. Non-ASCII Python content is allowed only for the explicit fly emoji in frontend/console.py and its test; inspect any other match.
8. Inspect brain/ and world/ imports: neither package may import the other.
For runtime changes, also run a finite CLI smoke with a temporary --memory-file and inspect the rendered frame/persisted JSON.
