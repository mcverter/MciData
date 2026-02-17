This repo provides helper scripts for handling Major Capital Improvement Case files from the NYS Division of Housing and Community Renewal.

### Project structure
* `src/fetch_reports.py` scrapes the [transparency initiative page](https://hcr.ny.gov/office-rent-administration-transparency-initiative), downloads any monthly report PDFs that are not already present, and stores them in `data/`.
* `src/parse_reports.py` walks through every PDF in `data/`, extracts the MCI data (assuming the current PDF layout), and appends results to `output/mci_output.csv`. Each row is prefixed with the source `report_file` and sortable `report_month` (YYYY-MM). Delete the CSV and `output/processed_reports.log` if you want a clean regeneration instead of appending.
* `src/classes.py` defines Pydantic models (`Address`, `WorkItem`, `PropertyMci`) used during parsing.
* `src/regexes.py` contains compiled regular expressions for street address lines, borough lines, and work item lines.

### Assumptions
* `fetch_reports.py` skips downloads when a file with the derived month name already exists in `data/`.
* `parse_reports.py` makes strong assumptions about the layout of the MCI files: each entry begins with a line containing the street address, followed by a line with the borough and other information about the property, followed by zero or more lines specifying each MCI work item and its associated costs; unexpected layout changes will break parsing.

### Usage
1. Create a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`.
3. Download any missing PDFs (optional but recommended each month): `python src/fetch_reports.py`.
4. Parse the PDFs into the CSV: `python src/parse_reports.py`. This script logs processed filenames in `output/processed_reports.log`; remove entries there if you need to reprocess a given PDF.

### Scheduling
A GitHub Actions workflow (`.github/workflows/fetch-and-parse.yml`) runs `fetch_reports.py` and `parse_reports.py` on the 5th of each month. It can also be triggered manually via `workflow_dispatch`. The workflow runs the test suite after parsing; if tests fail the commit step is skipped so bad data is not persisted. New PDFs, CSV output, and the processed-reports manifest are committed back to the repo automatically.

### Testing
Run `pytest tests/test_parse_reports.py` to exercise the regression suite. Current coverage ensures:
* The parser emits identical CSV rows for `tests/data/may-2024-mci-closed-case-report.pdf` vs. `tests/data/may-2024-expected.csv`.
* Duplicate skip behavior: running `process_directory` twice against the same file confirms no duplicate rows are appended after the manifest marks the report as processed.

Any change that perturbs those outputs fails immediately; expand with more fixtures as needed.

### TODOs
* Manually vet the expected CSV fixture against the official source PDF.
* Add more test fixtures (e.g., September 2025) to broaden regression coverage.
* Replace filename-only dedup with hash-based dedup so republished PDFs with the same name trigger reprocessing.
