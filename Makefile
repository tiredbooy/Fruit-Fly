PYTHON ?= .venv/bin/python
FLIES ?= 1

.PHONY: gym gym-run gym-build run run-fresh run-full web web-full frontend-install frontend-build frontend-test test data-status brain-build brain-status brain-benchmark help

gym: frontend-build
	$(PYTHON) -B main.py gym-web --flies $(FLIES)

gym-run:
	$(PYTHON) -B main.py gym --flies $(FLIES)

gym-build:
	$(PYTHON) -B -m brain.gym_circuit

run:
	$(PYTHON) -B main.py run --animate

run-fresh:
	$(PYTHON) -B main.py run --animate --reset-memory

run-full:
	$(PYTHON) -B main.py run --animate --brain full

frontend-install:
	cd frontend/web && bun install --frozen-lockfile

frontend-build: frontend-install
	cd frontend/web && bun run build

frontend-test:
	cd frontend/web && bun test

web: frontend-build
	$(PYTHON) -B main.py web

web-full: frontend-build
	$(PYTHON) -B main.py web --brain full

test:
	$(PYTHON) -B -m unittest discover -s tests -t . -v

data-status:
	$(PYTHON) -B main.py data-status

brain-build:
	$(PYTHON) -B main.py brain-build

brain-status:
	$(PYTHON) -B main.py brain-status

brain-benchmark:
	$(PYTHON) -B main.py brain-benchmark

help:
	@printf '%s\n' \
		'make gym FLIES=1  Open bench presses and dumbbell curls in the browser' \
		'make gym-run FLIES=1  Run 300 finite gym steps' \
		'make gym-build    Reproduce gym circuits from official MaleCNS' \
		'make run          Run Experiment 1 with persistent memory' \
		'make run-fresh    Archive memory and run from a clean state' \
		'make run-full     Run Experiment 1 on the full MaleCNS graph' \
		'make web          Run the Three.js observatory with compact brain' \
		'make web-full     Run the Three.js observatory with full brain' \
		'make frontend-build  Build and type-check browser assets' \
		'make frontend-test   Check cameras, neuron inspector, and model integrity' \
		'make test         Run the complete test suite' \
		'make data-status  Validate official MaleCNS data and circuits' \
		'make brain-build  Build the full MaleCNS sparse graph' \
		'make brain-status Validate the full graph artifact' \
		'make brain-benchmark  Measure full graph update speed'
