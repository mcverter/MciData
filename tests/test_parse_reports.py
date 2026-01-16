from pathlib import Path
import shutil
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from src import parse_reports


def _run_single_report_check(
    tmp_path, pdf_filename: str, expected_filename: str
) -> None:
    """
    Helper to parse a single PDF into a temp CSV and compare it to the fixture.
    """
    pdf_path = PROJECT_ROOT / "tests" / "data" / pdf_filename
    expected_csv_path = PROJECT_ROOT / "tests" / "data" / expected_filename
    expected_csv = expected_csv_path.read_text().splitlines()

    original_output_path = parse_reports.CSV_OUTPUT_FILEPATH
    original_manifest_path = parse_reports.PROCESSED_MANIFEST_FILE
    original_log_path = parse_reports.LOG_FILEPATH

    temp_output_path = tmp_path / "mci_output.csv"
    temp_manifest_path = tmp_path / "processed_reports.log"
    temp_log_path = tmp_path / "parse_reports.log"

    try:
        parse_reports.set_output_file(str(temp_output_path))
        parse_reports.PROCESSED_MANIFEST_FILE = str(temp_manifest_path)
        parse_reports.configure_logger(str(temp_log_path))

        parse_reports.CSV_OUTPUT_FILE.write(parse_reports.CSV_HEADERS)
        parse_reports.process_file(
            str(pdf_path),
            pdf_path.name,
            parse_reports.derive_report_month(pdf_path.name),
        )
        parse_reports.CSV_OUTPUT_FILE.close()

        actual_lines = temp_output_path.read_text().splitlines()
        assert actual_lines == expected_csv
    finally:
        # Restore module globals so subsequent tests/runs behave normally.
        parse_reports.set_output_file(original_output_path)
        parse_reports.PROCESSED_MANIFEST_FILE = original_manifest_path
        parse_reports.configure_logger(original_log_path)


def test_may_2024_report_parses_to_expected_csv(tmp_path):
    """
    Parse only the May 2024 PDF and verify the CSV rows match the known-good fixture.
    """
    _run_single_report_check(
        tmp_path,
        pdf_filename="may-2024-mci-closed-case-report.pdf",
        expected_filename="may-2024-expected.csv",
    )


def test_duplicate_report_is_skipped(tmp_path):
    """
    Verifies that running the parser twice against the same PDF does not append duplicate rows.
    """
    pdf_src = PROJECT_ROOT / "tests" / "data" / "may-2024-mci-closed-case-report.pdf"
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    pdf_copy = data_dir / pdf_src.name
    shutil.copy(pdf_src, pdf_copy)

    temp_output_path = tmp_path / "mci_output.csv"
    temp_manifest_path = tmp_path / "processed_reports.log"
    temp_log_path = tmp_path / "parse_reports.log"

    original_output_path = parse_reports.CSV_OUTPUT_FILEPATH
    original_manifest_path = parse_reports.PROCESSED_MANIFEST_FILE
    original_log_path = parse_reports.LOG_FILEPATH
    original_input_dir = parse_reports.INPUT_DOCUMENT_BASE_DIR

    try:
        # Redirect parser I/O to the temporary sandbox.
        parse_reports.INPUT_DOCUMENT_BASE_DIR = str(data_dir)
        parse_reports.set_output_file(str(temp_output_path))
        parse_reports.PROCESSED_MANIFEST_FILE = str(temp_manifest_path)
        parse_reports.configure_logger(str(temp_log_path))

        # First pass: file is downloaded for the first time, so rows should be emitted.
        parse_reports.CSV_OUTPUT_FILE.write(parse_reports.CSV_HEADERS)
        parse_reports.process_directory(parse_reports.INPUT_DOCUMENT_BASE_DIR)
        parse_reports.CSV_OUTPUT_FILE.close()
        first_run_lines = temp_output_path.read_text().splitlines()
        assert len(first_run_lines) > 1

        # Second pass: manifest now contains the filename, so no new rows should be added.
        parse_reports.set_output_file(str(temp_output_path))
        parse_reports.process_directory(parse_reports.INPUT_DOCUMENT_BASE_DIR)
        parse_reports.CSV_OUTPUT_FILE.close()
        second_run_lines = temp_output_path.read_text().splitlines()

        assert second_run_lines == first_run_lines
    finally:
        # Restore module globals so other tests/runs behave normally.
        parse_reports.set_output_file(original_output_path)
        parse_reports.PROCESSED_MANIFEST_FILE = original_manifest_path
        parse_reports.INPUT_DOCUMENT_BASE_DIR = original_input_dir
        parse_reports.configure_logger(original_log_path)
