# Tech stack
- Python standard-library project; current local interpreter is Python 3.14.7 at .venv/bin/python.
- requirements.txt pins compatible NumPy, pandas, PyArrow, and SciPy ranges.
- GNU Make provides user entrypoints.
- unittest is the test framework.
- MaleCNS v1.0 local CSV/TSV assets are large and checksum-pinned in data/malecns/v1.0/source-manifest.json.
- Full neural propagation uses a memory-mapped SciPy CSR matrix on CPU.
- Persistence is versioned JSON written atomically with stdlib filesystem APIs.
