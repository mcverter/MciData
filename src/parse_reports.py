"""Parses document from NYS State and produces csv"""

import logging
from operator import attrgetter
import os
import pathlib

from finite_machine_states.fsm_state import FsmState
from src.MciFileProcessor.mci_file_processor import MciFileProcessor
from src.PropertyMci.property_mci import PropertyMci
from src.regexes.filename_patterns import (
    derive_report_month,
    is_valid_input_filename,
)

"""
Parses all of the MCI files in a directory and outputs a csv file
"""
BASE_DIR = pathlib.Path(__file__).parent.parent
INPUT_DOCUMENT_BASE_DIR = os.path.join(BASE_DIR, "data")
CSV_OUTPUT_FILEPATH = os.path.join(BASE_DIR, "output", "mci_output.csv")
PROCESSED_MANIFEST_FILE = os.path.join(BASE_DIR, "output", "processed_reports.log")
LOG_FILEPATH = os.path.join(BASE_DIR, "output", "parse_reports.log")
CSV_HEADERS = (
    "report_file,report_month,street_address,neighborhood,zip_code,county,docket_number,case_status,closing_date,"
    "close_code,monthly_mci_incr_per_room,name,claim_cost,allow_cost\n"
)
CSV_OUTPUT_FILE = open(CSV_OUTPUT_FILEPATH, "a+")
# REPORT_FILENAME_PATTERN = re.compile(
#      r"(?P<month>january|february|march|april|may|june|july|august|september|october|november|december|DirectFeed)"
#     r"-(?P<year>\d{4})",
#     re.IGNORECASE,
# )
FSM_STATE: FsmState = FsmState.START_DOCUMENT

logger = logging.getLogger("parse_reports")


def configure_logger(log_path: str) -> None:
    """
    Configure the module logger to write to the provided log file.
    """
    global LOG_FILEPATH
    LOG_FILEPATH = log_path
    os.makedirs(os.path.dirname(LOG_FILEPATH), exist_ok=True)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
    handler = logging.FileHandler(LOG_FILEPATH, mode="a")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def set_output_file(path: str) -> None:
    """
    Override the CSV output path. Useful for tests.
    """
    global CSV_OUTPUT_FILEPATH, CSV_OUTPUT_FILE
    CSV_OUTPUT_FILE.close()
    CSV_OUTPUT_FILEPATH = path
    CSV_OUTPUT_FILE = open(CSV_OUTPUT_FILEPATH, "a")


configure_logger(str(LOG_FILEPATH))


def load_processed_reports() -> set[str]:
    """
    Returns a set containing the filenames of reports already processed into the CSV.
    """
    if not os.path.exists(PROCESSED_MANIFEST_FILE):
        return set()
    with open(PROCESSED_MANIFEST_FILE) as manifest:
        return {line.strip() for line in manifest if line.strip()}


def record_processed_report(filename: str) -> None:
    """
    Appends a filename to the processed reports manifest.
    """
    os.makedirs(os.path.dirname(PROCESSED_MANIFEST_FILE), exist_ok=True)
    with open(PROCESSED_MANIFEST_FILE, "a") as manifest:
        manifest.write(f"{filename}\n")


def process_directory(path: str) -> None:
    """
    Processes all pdf files in directory
    :param path: Base directory for input files
    """
    processed_reports = load_processed_reports()

    for file in os.listdir(path):
        if not is_valid_input_filename(file):
            continue
        if file in processed_reports:
            logger.info("Skipping %s (already processed)", file)
            continue
        report_month = derive_report_month(file)
        logger.info(
            "Processing file %s (report_month=%s)", file, report_month or "unknown"
        )
        process_file(os.path.join(path, file), file, report_month)
        processed_reports.add(file)
        record_processed_report(file)
        logger.info("Finished file %s", file)


def process_file(filepath: str, filename: str, report_month: str) -> None:
    file_processor = MciFileProcessor(filepath)
    all_mcis = file_processor.process_file()
    write_mcis_to_csv(all_mcis, filename, report_month)


def write_mcis_to_csv(
    all_mcis: list[PropertyMci], filename: str, report_month: str
) -> None:
    for mci in all_mcis:
        (street_address, neighborhood, zip_code, county) = attrgetter(
            "street_address", "neighborhood", "zip_code", "county"
        )(mci.address)
        (docket_number, case_status, close_code, closing_date) = attrgetter(
            "docket_number", "case_status", "close_code", "closing_date"
        )(mci.docket)
        monthly_mci_incr_per_room = (
            mci.docket.monthly_mci_incr_per_room
            if mci.docket.monthly_mci_incr_per_room
            else ""
        )
        if mci.work_item:
            (mci_work, claim_cost, allow_cost) = attrgetter(
                "mci_work", "claim_cost", "allow_cost"
            )(mci.work_item)
        else:
            mci_work = claim_cost = allow_cost = ""

        output = (
            f"{filename},{report_month},{street_address},{neighborhood},{zip_code},{county},{docket_number},{case_status},{closing_date},"
            f"{close_code},{monthly_mci_incr_per_room},"
            f"{mci_work},{claim_cost},{allow_cost}"
        )
        CSV_OUTPUT_FILE.write(f"{output}\n")


if __name__ == "__main__":
    CSV_OUTPUT_FILE.write(CSV_HEADERS)
    process_directory(INPUT_DOCUMENT_BASE_DIR)
    CSV_OUTPUT_FILE.close()
