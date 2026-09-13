# Tech stack
- Python standard-library project; current local interpreter is Python 3.14.7 at .venv/bin/python.
- No package manifest and no third-party runtime/test dependencies currently.
- GNU Make provides user entrypoints.
- unittest is the test framework.
- MaleCNS v1.0 local CSV/TSV assets are large and checksum-pinned in data/malecns/v1.0/source-manifest.json.
- Persistence is versioned JSON written atomically with stdlib filesystem APIs.