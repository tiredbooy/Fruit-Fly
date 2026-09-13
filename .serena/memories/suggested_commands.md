# Commands
- `make run`: animated Experiment 1 using persistent memory.
- `make run-fresh`: archive existing memory to .bak and start clean.
- `make test`: complete unittest suite.
- `make data-status`: checksum and semantic validation against the full official MaleCNS assets.
- `make help`: concise command list.
- Direct finite smoke: `.venv/bin/python -B main.py run --steps 600 --fps 30 --memory-file /tmp/flybrain-memory.json`.
- Default memory path: data/runs/experiment-001-memory.json.