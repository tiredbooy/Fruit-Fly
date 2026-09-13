# Completion gates
Run from repository root:
1. `make test` must report zero failures.
2. `make data-status` must end with "Status: data is valid and ready".
3. Full-engine work must also run `make brain-status`, `make brain-benchmark`, and a finite `main.py run --brain full` smoke.
4. `make help` must list run, run-fresh, run-full, tests, and data/brain management.
5. `git diff --check` must exit 0.
6. Non-ASCII Python content is allowed only for the explicit fly emoji in frontend/console.py and its test; inspect any other match.
7. Inspect brain/ and world/ imports: neither package may import the other.
For runtime changes, also run a finite CLI smoke with a temporary --memory-file and inspect the rendered frame/persisted JSON.
