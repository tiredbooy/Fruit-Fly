# Completion gates
Run from repository root:
1. `make test` must report zero failures.
2. `make data-status` must end with "Status: data is valid and ready".
3. `make help` must list run, run-fresh, test, and data-status.
4. `git diff --check` must exit 0.
5. Non-ASCII Python content is allowed only for the explicit fly emoji in frontend/console.py and its test; inspect any other match.
6. Inspect brain/ and world/ imports: neither package may import the other.
For runtime changes, also run a finite CLI smoke with a temporary --memory-file and inspect the rendered frame/persisted JSON.