import logging
import os
import pathlib
from operator import attrgetter

import pdfplumber
import re
from regexes import borough_line_regex, street_address_line_regex, work_line_regex
from classes import Address, WorkItem, PropertyMci
"""
Parses all of the MCI files in a directory and outputs a csv file
"""

BASE_DIR = pathlib.Path(__file__).parent.parent
INPUT_DOCUMENT_BASE_DIR = os.path.join(BASE_DIR, "data")
CSV_OUTPUT_FILEPATH = os.path.join(BASE_DIR, "output", "mci_output.csv")
PROCESSED_MANIFEST_FILE = os.path.join(BASE_DIR, "output", "processed_reports.log")
LOG_FILEPATH = os.path.join(BASE_DIR, "output", "parse_reports.log")
CSV_HEADERS = ("report_file,report_month,street_address,borough,zip_code,docket_number,case_status,closing_date,"
               "close_code,monthly_mci_incr_per_room,name,claim_cost,allow_cost\n")
CSV_OUTPUT_FILE = open(CSV_OUTPUT_FILEPATH, "a")
REPORT_FILENAME_PATTERN = re.compile(
    r"(?P<month>january|february|march|april|may|june|july|august|september|october|november|december)"
    r"-(?P<year>\d{4})",
    re.IGNORECASE,
)
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


configure_logger(LOG_FILEPATH)
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

def load_processed_reports():
    """
    Returns a set containing the filenames of reports already processed into the CSV.
    """
    if not os.path.exists(PROCESSED_MANIFEST_FILE):
        return set()
    with open(PROCESSED_MANIFEST_FILE, "r") as manifest:
        return {line.strip() for line in manifest if line.strip()}

def record_processed_report(filename: str):
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

def process_directory(path: str):
    """
    Processes all pdf files in directory
    :param path: Base directory for input files
    """
    processed_reports = load_processed_reports()
    files = sorted(file for file in os.listdir(path) if file.lower().endswith(".pdf"))
    logger.info("Discovered %d PDF files in %s", len(files), path)
    for file in files:
        if file in processed_reports:
            logger.info("Skipping %s (already processed)", file)
            continue
        report_month = derive_report_month(file)
        logger.info("Processing file %s (report_month=%s)", file, report_month or "unknown")
        process_file(os.path.join(path,file), file, report_month)
        processed_reports.add(file)
        record_processed_report(file)
        logger.info("Finished file %s", file)

def process_file(path: str, report_file: str, report_month: str):
    """
    Processes all pages of pdf
    :param path: Filepath of pdf file
    """
    property_mci = None
    address = None
    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            # process_page returns the ongoing PropertyMci/Address so entries that span a page break continue intact.
            property_mci, address = process_page(page, report_file, report_month, page_number, property_mci, address)
    pdf.close()
    if property_mci:
        # File ended mid-entry; finish writing the last accumulated PropertyMci.
        write_to_csv(property_mci)
        property_mci = None
        address = None


def process_page(page, report_file: str, report_month: str, page_number: int,
                property_mci=None, address=None):
    """
    Constructs a PropertyMci from the lines of page and outputs result to CSV file

    Line processing logic is based on the layout of the PDF files
    * Street Address Line begins a PropertyMCI.
    * Borough Line comes immediately next. It contains the borough, zip code, docket #, case status, close code,
        closing date, and possibly the MCI increment per room.
    * MCI Work Lines come immediately next.  They contain the work name, claim cost, and allow cost.

    A PropertyMCI entry is complete and can be written to an output file when any of the following occurs:
    * A new Street Address Line begins a new PropertyMCI.
    * The bottom line of the file is reached. The bottom line might also be a Work Line.
    """
    text = page.extract_text() or ""
    lines = text.split('\n')
    logger.info("Parsing %s page %s with %d lines", report_file, page_number, len(lines))

    for index, line in enumerate(lines):
        # street address line indicates start of PropertyMci
        if m := re.match(street_address_line_regex, line):
            # Add previous PropertyMci to array
            if property_mci:
                write_to_csv(property_mci)
                property_mci = None
                address = None
            property_mci = PropertyMci(work_items= [], report_file=report_file, report_month=report_month)
            address = Address()
            street_address = m.group(0)
            address.street_address = street_address

        elif m := re.match(borough_line_regex, line):
            if property_mci is None or address is None:
                logger.warning("Borough line encountered before street address in %s page %s: %s",
                               report_file, page_number, line)
                continue
            borough, zip_code, docket_no, case_status, closing_date, close_code, mci_per_room = m.groups()
            address.borough = borough
            address.zip_code = zip_code
            property_mci.docket_number = docket_no
            property_mci.case_status = case_status
            property_mci.close_code = close_code
            property_mci.closing_date = closing_date
            property_mci.address = address
            property_mci.monthly_mci_incr_per_room = mci_per_room.lstrip() if mci_per_room is not None else ""
        elif m := re.match(work_line_regex, line):
            if property_mci is None:
                logger.warning("Work line encountered before street address in %s page %s: %s",
                               report_file, page_number, line)
                continue
            mci_work, claim_cost, allow_cost = m.groups()
            allow_cost = allow_cost.lstrip() if allow_cost is not None else ""
            property_mci.work_items.append(
                WorkItem(name=mci_work,
                         claim_cost=claim_cost,
                         allow_cost = allow_cost)
            )
            # MCI_Item might be last line of file
            if index == len(lines) -1:
                write_to_csv(property_mci)
                property_mci = None
                address = None

        # Add final PropertyMci to array
        elif index == len(lines) -1 and property_mci:
            # Return the partially built PropertyMci so the caller can continue it on the next page.
            return property_mci, address

    return property_mci, address

def write_to_csv(property_mci: PropertyMci):
    """
    Writes each WorkItem in the PropertyMci to the csv file
    """
    (report_file, report_month, docket_number, case_status, closing_date,
     close_code, monthly_mci_incr_per_room, address, work_items) = attrgetter(
        'report_file', 'report_month', 'docket_number', 'case_status', 'closing_date', 'close_code',
        'monthly_mci_incr_per_room', 'address', 'work_items')(property_mci)
    if address is None:
        logger.warning("Skipping write for %s (%s) because address metadata is missing", report_file, docket_number)
        return
    (street_address, borough, zip_code) = attrgetter('street_address', 'borough', 'zip_code')(address)
    # Normalize source metadata (report file/month) and closing_date to empty strings. Street address/borough/zip are
    # guaranteed earlier in parsing, but a file rename that doesn't match our pattern or a parsing hiccup in the borough
    # line could leave these as None, which would otherwise show up verbatim in the CSV.
    report_file = report_file or ""
    report_month = report_month or ""
    closing_date = closing_date or ""
    if len(work_items) > 0:
        for item in work_items:
            (name, claim_cost, allow_cost) = attrgetter('name', 'claim_cost', 'allow_cost')(item)
            output = (f"{report_file},{report_month},{street_address},{borough},{zip_code},{docket_number},{case_status},{closing_date},"
                      f"{close_code},{monthly_mci_incr_per_room},"
                      f"{name},{claim_cost},{allow_cost}")
            CSV_OUTPUT_FILE.write(f"{output}\n")
    else:
        output = (f"{report_file},{report_month},{street_address},{borough},{zip_code},{docket_number},{case_status},{closing_date},"
                  f"{close_code},{monthly_mci_incr_per_room},"
                  f",,")
        CSV_OUTPUT_FILE.write(f"{output}\n")

if __name__ == "__main__":
    CSV_OUTPUT_FILE.write(CSV_HEADERS)
    process_directory(INPUT_DOCUMENT_BASE_DIR)
    CSV_OUTPUT_FILE.close()
