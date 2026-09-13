PYTHON ?= .venv/bin/python

.PHONY: run run-fresh test data-status help

run:
	$(PYTHON) -B main.py run --animate

run-fresh:
	$(PYTHON) -B main.py run --animate --reset-memory

test:
	$(PYTHON) -B -m unittest discover -s tests -t . -v

data-status:
	$(PYTHON) -B main.py data-status

help:
	@printf '%s\n' \
		'make run          Run Experiment 1 with persistent memory' \
		'make run-fresh    Archive memory and run from a clean state' \
		'make test         Run the complete test suite' \
		'make data-status  Validate official MaleCNS data and circuits'
