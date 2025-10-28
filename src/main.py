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
CSV_OUTPUT_FILE = open(CSV_OUTPUT_FILEPATH, "a")

def process_directory(path: str):
    """
    Processes all pdf files in directory
    :param path: Base directory for input files
    """
    files = os.listdir(path)
    for file in files:
        if file.endswith("pdf"):
            process_file(os.path.join(path,file))

def process_file(path: str):
    """
    Processes all pages of pdf
    :param path: Filepath of pdf file
    """
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            process_page(page)
    pdf.close()


def process_page(page):
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
    text = page.extract_text()
    lines = text.split('\n')

    property_mci = None
    address = None

    for index, line in enumerate(lines):
        # street address line indicates start of PropertyMci
        if m := re.match(street_address_line_regex, line):
            # Add previous PropertyMci to array
            if property_mci:
                write_to_csv(property_mci)
            property_mci = PropertyMci(work_items= [])
            address = Address()
            street_address = m.group(0)
            address.street_address = street_address

        elif m := re.match(borough_line_regex, line):
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

        # Add final PropertyMci to array
        elif index == len(lines) -1 and property_mci:
            write_to_csv(property_mci)

def write_to_csv(property_mci: PropertyMci):
    """
    Writes each WorkItem in the PropertyMci to the csv file
    """
    (docket_number, case_status, closing_date,
     close_code, monthly_mci_incr_per_room, address, work_items) = attrgetter(
        'docket_number', 'case_status', 'closing_date', 'close_code',
        'monthly_mci_incr_per_room', 'address', 'work_items')(property_mci)
    (street_address, borough, zip_code) = attrgetter('street_address', 'borough', 'zip_code')(address)
    if len(work_items) > 0:
        for item in work_items:
            (name, claim_cost, allow_cost) = attrgetter('name', 'claim_cost', 'allow_cost')(item)
            output = (f"{street_address},{borough},{zip_code},{docket_number},{case_status},"
                      f"{close_code},{monthly_mci_incr_per_room},"
                      f"{name},{claim_cost},{allow_cost}")
            CSV_OUTPUT_FILE.write(f"{output}\n")
    else:
        output = (f"{street_address},{borough},{zip_code},{docket_number},{case_status},"
                  f"{close_code},{monthly_mci_incr_per_room},"
                  f",,")
        CSV_OUTPUT_FILE.write(f"{output}\n")

if __name__ == "__main__":
    headers = "street_address,borough,zip_code,docket_number,case_status,"\
              "close_code,monthly_mci_incr_per_room,"\
              "name,claim_cost,allow_cost\n"
    CSV_OUTPUT_FILE.write(headers)
    process_directory(INPUT_DOCUMENT_BASE_DIR)
    CSV_OUTPUT_FILE.close()