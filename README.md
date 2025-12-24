This repo provides helper scripts for handling Major Capital Improvement Case files from the NYS Division of Housing and Community Renewal.

This repo is intended to be adapted for a larger project.  In its current form, it consists of two scripts:
* `src/fetch_reports.py` scrapes the transparency initiative page, downloads any month report PDFs that are not already present, and stores them in `data/`.
* `src/parse_reports.py` walks through every PDF in `data/`, extracts the MCI data (assuming the current PDF layout), and appends results to `output/mci_output.csv`. Each row is prefixed with the source `report_file` and sortable `report_month` (YYYY-MM). Delete the CSV first if you want a clean regeneration instead of appending.

### Assumptions
* `fetch_reports.py` skips downloads when a file with the derived month name already exists in `data/`.
* `src/parse_reports.py` makes strong assumptions about the layout of the MCI files: each entry begins with a line containing the street address, followed by a line with the borough and other information about the property, followed by zero or more lines specifying each MCI work item and its associated costs; unexpected layout changes will break parsing.

### Usage
1. Create a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`.
3. Download any missing PDFs (optional but recommended each month): `python src/fetch_reports.py`.
4. Parse the PDFs into the CSV: `python src/parse_reports.py`. This script logs processed filenames in `output/processed_reports.log`; remove entries there if you need to reprocess a given PDF.

### Testing
Run `pytest tests/test_parse_reports.py` to exercise the regression suite. Current coverage ensures the parser emits identical CSV rows for:
* `tests/data/september-2025-mci-closed-case-report.pdf` vs. `tests/data/september-2025-expected.csv`
* `tests/data/may-2024-mci-closed-case-report.pdf` vs. `tests/data/may-2024-expected.csv`
* Duplicate skip behavior: running `process_directory` twice against the same file confirms no duplicate rows are appended after the manifest marks the report as processed.

Any change that perturbs those outputs fails immediately; expand with more fixtures as needed.
*TODOs:* Manually vet each “expected” CSV to confirm it matches the official source, and consider caching file hashes (not just filenames) when tracking downloaded/processed PDFs so content updates are detected.

### Forward-looking automation notes
* **Scheduling**: Two obvious paths are (a) a GitHub Actions cron workflow that installs dependencies and runs `fetch_reports.py` + `parse_reports.py`, or (b) a Docker image run on a scheduler (e.g., ECS/k8s CronJob). Decide where the outputs should land (commit to a repo branch, upload to object storage, etc.).
* **Persisting state**: `output/processed_reports.log` and `output/parse_reports.log` are currently git-ignored. A scheduled job needs to retrieve / persist the manifest between runs (or replace it with a hash-based metadata store) so duplicates are still skipped.
* **Logging**: Actions runners capture stdout/stderr, but containers might benefit from writing logs to stdout instead of a file, or shipping `parse_reports.log` to your log store.
* **Hash-based dedupe**: Eventually replace filename-only checks with hashes (or store both) so republished PDFs with the same name trigger reprocessing. Plan for a cache (JSON, SQLite, etc.) that records filename + hash + processed timestamp.
