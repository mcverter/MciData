import logging
from operator import attrgetter
import os
import pathlib
import re

import pdfplumber

from classes import Address, PropertyMci, WorkItem
from finite_machine_states.fsm_state import FsmState
from src.lines.lines import LineType, get_line_type_and_matches

"""
Parses all of the MCI files in a directory and outputs a csv file
"""
BASE_DIR = pathlib.Path(__file__).parent.parent
INPUT_DOCUMENT_BASE_DIR = os.path.join(BASE_DIR, "data")
CSV_OUTPUT_FILEPATH = os.path.join(BASE_DIR, "output", "mci_output.csv")
PROCESSED_MANIFEST_FILE = os.path.join(BASE_DIR, "output", "processed_reports.log")
LOG_FILEPATH = os.path.join(BASE_DIR, "output", "parse_reports.log")
CSV_HEADERS = (
    "report_file,report_month,street_address,borough,zip_code,docket_number,case_status,closing_date,"
    "close_code,monthly_mci_incr_per_room,name,claim_cost,allow_cost\n"
)
CSV_OUTPUT_FILE = open(CSV_OUTPUT_FILEPATH, "a+")
REPORT_FILENAME_PATTERN = re.compile(
    r"(?P<month>january|february|march|april|may|june|july|august|september|october|november|december)"
    r"-(?P<year>\d{4})",
    re.IGNORECASE,
)
FSM_STATE: FsmState = FsmState.DOCUMENT_START

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
MONTH_LOOKUP = {
    "january": "01",
    "february": "02",
    "march": "03",
    "april": "04",
    "may": "05",
    "june": "06",
    "july": "07",
    "august": "08",
    "september": "09",
    "october": "10",
    "november": "11",
    "december": "12",
}


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


def derive_report_month(filename: str) -> str:
    """
    Derives a sortable YYYY-MM label from the report filename.
    Returns an empty string when the pattern does not match.
    """
    if match := REPORT_FILENAME_PATTERN.search(filename):
        month = match.group("month").lower()
        year = match.group("year")
        month_number = MONTH_LOOKUP.get(month)
        if month_number:
            return f"{year}-{month_number}"
    return ""


def process_directory(path: str) -> None:
    """
    Processes all pdf files in directory
    :param path: Base directory for input files
    """
    processed_reports = load_processed_reports()

    for file in os.listdir(path):
        if file[-4:] != ".pdf":
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


def is_valid_line_type_and_fsm_state(line_type: LineType) -> bool:
    global FSM_STATE
    if (
        line_type == LineType.NO_LINE
        or LineType.NYS_DIVISION_HEADER
        or LineType.MAJOR_CAPITAL_HEADER
        or LineType.COLUMN_HEADER_1
        or LineType.COLUMN_HEADER_2
        or LineType.DASHES
        or LineType.DOUBLE_DASHES
    ):
        return True

    if FSM_STATE == FsmState.TOTAL_CASES_COUNTY:
        return True
    if FSM_STATE == FsmState.COUNTY_CASES:
        return True
    if FSM_STATE == FsmState.TOTAL_CASES_DOCUMENT:
        return True

    if (
        FSM_STATE == FsmState.DOCUMENT_START
        and line_type == LineType.COUNTY_DATE_HEADER
    ):
        FSM_STATE = FsmState.COUNTY_START
        return True

    if FSM_STATE == FsmState.COUNTY_START and line_type == LineType.STREET_ADDRESS_LINE:
        return True

    if FSM_STATE == FsmState.STREET_ADDRESS:
        return True
    if FSM_STATE == FsmState.WORK_ITEM and (
        LineType
        in [
            LineType.MCI_WORK_LINE,
        ]
    ):
        return True
    logger.error("Error for line type and state")
    return False


#     COUNTY_DATE_HEADER = 5
#     STREET_ADDRESS_LINE = 10
#     BOROUGH_DOCKET_LINE = 11
#     DOCKET_LINE = 12
#     MCI_WORK_LINE = 13
#     TOTAL_CASES_COUNTY_LINE = 14  # Used at end of county section
#     COUNT_PER_COUNTY_LINE = 15  # Used at end of document
#     TOTAL_CASES_DOCUMENT_LINE = 16


def process_file(path: str, report_file: str, report_month: str) -> None:
    """
    Processes all pages of pdf
    :param path: Filepath of pdf file
    """
    file_text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            file_text += page.extract_text()
    pdf.close()
    lines = file_text.split("\n")

    property_mci = None
    address = None

    for line in lines:
        line_type, line_matches = get_line_type_and_matches(line)
        if not is_valid_line_type_and_fsm_state(line_type):
            continue

        match line_type:
            case LineType.STREET_ADDRESS_LINE:
                if property_mci:
                    write_to_csv(property_mci)
                property_mci = PropertyMci(
                    work_items=[], report_file=report_file, report_month=report_month
                )
                address = Address()
                street_address: str = line_matches.group(0)
                address.street_address = street_address
            case LineType.BOROUGH_DOCKET_LINE:
                (
                    borough,
                    zip_code,
                    docket_no,
                    case_status,
                    closing_date,
                    close_code,
                    mci_per_room,
                ) = line_matches.groups()
                address.borough = borough
                address.zip_code = zip_code
                property_mci.docket_number = docket_no
                property_mci.case_status = case_status
                property_mci.close_code = close_code
                property_mci.closing_date = closing_date
                property_mci.address = address
                property_mci.monthly_mci_incr_per_room = (
                    mci_per_room.lstrip() if mci_per_room else ""
                )
            # Docket Line indicates new docket number for previously used address
            case LineType.DOCKET_LINE:
                # write out previous docket for address
                if property_mci:
                    write_to_csv(property_mci)
                docket_no, case_status, closing_date, close_code, mci_per_room = (
                    line_matches.groups()
                )
                property_mci.docket_number = docket_no
                property_mci.case_status = case_status
                property_mci.close_code = close_code
                property_mci.closing_date = closing_date
                property_mci.address = address
                property_mci.monthly_mci_incr_per_room = (
                    mci_per_room.lstrip() if mci_per_room else ""
                )

            case LineType.MCI_WORK_LINE:
                mci_work, claim_cost, allow_cost = line_matches.groups()
                allow_cost = allow_cost.lstrip() if allow_cost is not None else ""
                property_mci.work_items.append(
                    WorkItem(
                        name=mci_work, claim_cost=claim_cost, allow_cost=allow_cost
                    )
                )
            # end of file
            case LineType.TOTAL_CASES_DOCUMENT_LINE:
                if property_mci:
                    write_to_csv(property_mci)


def write_to_csv(property_mci: PropertyMci) -> None:
    """
    Writes each WorkItem in the PropertyMci to the csv file
    """
    (
        report_file,
        report_month,
        docket_number,
        case_status,
        closing_date,
        close_code,
        monthly_mci_incr_per_room,
        address,
        work_items,
    ) = attrgetter(
        "report_file",
        "report_month",
        "docket_number",
        "case_status",
        "closing_date",
        "close_code",
        "monthly_mci_incr_per_room",
        "address",
        "work_items",
    )(property_mci)
    if address is None:
        logger.warning(
            "Skipping write for %s (%s) because address metadata is missing",
            report_file,
            docket_number,
        )
        return
    (street_address, borough, zip_code) = attrgetter(
        "street_address", "borough", "zip_code"
    )(address)
    # Normalize source metadata (report file/month) and closing_date to empty strings. Street address/borough/zip are
    # guaranteed earlier in parsing, but a file rename that doesn't match our pattern or a parsing hiccup in the borough
    # line could leave these as None, which would otherwise show up verbatim in the CSV.
    report_file = report_file or ""
    report_month = report_month or ""
    closing_date = closing_date or ""
    if len(work_items) > 0:
        for item in work_items:
            (name, claim_cost, allow_cost) = attrgetter(
                "name", "claim_cost", "allow_cost"
            )(item)
            output = (
                f"{report_file},{report_month},{street_address},{borough},{zip_code},{docket_number},{case_status},{closing_date},"
                f"{close_code},{monthly_mci_incr_per_room},"
                f"{name},{claim_cost},{allow_cost}"
            )
            CSV_OUTPUT_FILE.write(f"{output}\n")
    else:
        output = (
            f"{report_file},{report_month},{street_address},{borough},{zip_code},{docket_number},{case_status},{closing_date},"
            f"{close_code},{monthly_mci_incr_per_room},"
            f",,"
        )
        CSV_OUTPUT_FILE.write(f"{output}\n")


if __name__ == "__main__":
    CSV_OUTPUT_FILE.write(CSV_HEADERS)
    process_directory(INPUT_DOCUMENT_BASE_DIR)
    CSV_OUTPUT_FILE.close()
