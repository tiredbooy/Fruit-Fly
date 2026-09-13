PYTHON ?= .venv/bin/python

.PHONY: run run-fresh run-full test data-status brain-build brain-status brain-benchmark help

run:
	$(PYTHON) -B main.py run --animate

run-fresh:
	$(PYTHON) -B main.py run --animate --reset-memory

run-full:
	$(PYTHON) -B main.py run --animate --brain full

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
		'make run          Run Experiment 1 with persistent memory' \
		'make run-fresh    Archive memory and run from a clean state' \
		'make run-full     Run Experiment 1 on the full MaleCNS graph' \
		'make test         Run the complete test suite' \
		'make data-status  Validate official MaleCNS data and circuits' \
		'make brain-build  Build the full MaleCNS sparse graph' \
		'make brain-status Validate the full graph artifact' \
		'make brain-benchmark  Measure full graph update speed'
