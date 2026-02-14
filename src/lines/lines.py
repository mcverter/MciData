"""Checks type of lines from input file"""

from enum import Enum
import re

from src.regexes.counties import counties
from src.regexes.regexes import (
    array_to_regex_or,
    borough_re,
    close_code_re,
    compile_line_regex,
    cost_re,
    date_re,
    docket_no_re,
    optional_cost_re,
    possible_mci_per_room_re,
    status_re,
    work_item_re,
    zip_re,
)
from src.regexes.street_types import street_types


class LineType(Enum):
    """
    Valid line types
    """

    NO_LINE = 1
    NYS_DIVISION_HEADER = 2
    OFFICE_OF_RENT_HEADER = 3
    MAJOR_CAPITAL_HEADER = 4
    COUNTY_DATE_HEADER = 5
    COLUMN_HEADER_1 = 6
    COLUMN_HEADER_2 = 7
    DASHES = 8
    DOUBLE_DASHES = 9
    STREET_ADDRESS_LINE = 10
    BOROUGH_DOCKET_LINE = 11
    DOCKET_LINE = 12
    MCI_WORK_LINE = 13
    TOTAL_CASES_COUNTY_LINE = 14  # Used at end of county section
    TOTAL_CASES_PLUS_NYS_DIVISION_HEADER = (
        15  # These two lines get run together by pdfplumber
    )
    COUNT_PER_COUNTY_LINE = 16  # Used at end of document
    TOTAL_CASES_DOCUMENT_LINE = 17


county_re = array_to_regex_or(counties)
street_type_re = array_to_regex_or(street_types)

# Line Regexes
street_address_line_regex = compile_line_regex(r"\d.*")
docket_line_regex = compile_line_regex(
    f"{docket_no_re} {status_re} {date_re} {close_code_re}{possible_mci_per_room_re}"
)
borough_line_regex = compile_line_regex(
    f"{borough_re}, NY {zip_re} {docket_no_re} {status_re} {date_re} {close_code_re}{possible_mci_per_room_re}"
)
work_line_regex = compile_line_regex(f"{work_item_re} {cost_re}{optional_cost_re}")
empty_line = r"^[\s\n]*$"
office_of_rent_header = compile_line_regex("OFFICE OF RENT ADMINISTRATION")
nys_division_header = compile_line_regex(
    "NYS DIVISION OF HOUSING AND COMMUNITY RENEWAL"
)
major_capital_header = compile_line_regex("MAJOR CAPITAL IMPROVEMENT CASES")
county_date_header = compile_line_regex(
    "FOR " + county_re + " COUNTY FROM " + date_re + " TO " + date_re
)
column_header_1 = compile_line_regex(
    "BLDG ADDRESS DOCKET NO CASE STATUS CLOSING DATE CLOSE CODE MONTHLY MCI INCR PER ROOM"
)
double_dash_line = compile_line_regex(
    "================================ ========= =========== ============ ========== ========================="
)
column_header_2 = compile_line_regex("MCI ITEM CLAIM COST ALLOW COST")
single_dash_line = compile_line_regex("-------------------- ------------ ------------")
total_cases_county_line = compile_line_regex(r"TOTAL CASES: (\d+)")
count_per_county_line = compile_line_regex(county_re + r": (\d+)")
total_cases_document_line = compile_line_regex(r"TOTAL NUMBER OF CASES: (\d+)")
# These lines get run together by pdfplumber!
total_cases_plus_nys_header = compile_line_regex(
    r"TOTAL NUMBER OF CASES: \d+NYS DIVISION OF HOUSING AND COMMUNITY RENEWAL"
)


def is_well_formed_line(line: str) -> re.Match[str] | None:
    """Checks whether line matches an expected regex pattern"""
    return (
        re.match(empty_line, line)
        or re.match(nys_division_header, line)
        or re.match(office_of_rent_header, line)
        or re.match(major_capital_header, line)
        or re.match(column_header_1, line)
        or re.match(column_header_2, line)
        or re.match(double_dash_line, line)
        or re.match(single_dash_line, line)
        or re.match(county_date_header, line)
        or re.match(street_address_line_regex, line)
        or re.match(borough_line_regex, line)
        or re.match(docket_line_regex, line)
        or re.match(work_line_regex, line)
        or re.match(total_cases_county_line, line)
        or re.match(count_per_county_line, line)
        or re.match(total_cases_document_line, line)
        or re.match(total_cases_plus_nys_header, line)
    )


def get_line_type_and_matches(
    line: str,
) -> tuple[LineType, re.Match[str]] | tuple[LineType, None]:
    """Returns LineType and matches from input line"""
    # pdfplumber merges last line of page with first line of next page
    line = re.sub("NYS DIVISION OF HOUSING AND COMMUNITY RENEWAL", "", line)
    # some files include page numbers
    line = re.sub(r"PAGE\s+\d+", "", line)
    line = line.strip()

    if re.search("1 ELEVATOR", line):
        print("uh oh")
    if re.match(empty_line, line):
        return LineType.NO_LINE, None
    if re.match(office_of_rent_header, line):
        return LineType.OFFICE_OF_RENT_HEADER, None
    if re.match(major_capital_header, line):
        return LineType.MAJOR_CAPITAL_HEADER, None
    if re.match(column_header_1, line):
        return LineType.COLUMN_HEADER_1, None
    if re.match(column_header_2, line):
        return LineType.COLUMN_HEADER_2, None
    if re.match(double_dash_line, line):
        return LineType.DOUBLE_DASHES, None
    if re.match(single_dash_line, line):
        return LineType.DASHES, None
    if m := re.match(county_date_header, line):
        return LineType.COUNTY_DATE_HEADER, m
    if m := re.match(borough_line_regex, line):
        return LineType.BOROUGH_DOCKET_LINE, m
    if m := re.match(docket_line_regex, line):
        return LineType.DOCKET_LINE, m
    if m := re.match(total_cases_county_line, line):
        return LineType.TOTAL_CASES_COUNTY_LINE, m
    if m := re.match(count_per_county_line, line):
        return LineType.COUNT_PER_COUNTY_LINE, m
    if m := re.match(total_cases_document_line, line):
        return LineType.TOTAL_CASES_DOCUMENT_LINE, m
    if m := re.match(total_cases_plus_nys_header, line):
        return LineType.TOTAL_CASES_PLUS_NYS_DIVISION_HEADER, m
    # Work Lines and Addresses are the most variable
    if m := re.match(work_line_regex, line):
        return LineType.MCI_WORK_LINE, m
    # Addresses can be distinguished from work lines by the presence of a cost
    if not re.search(cost_re, line) and re.search(street_address_line_regex, line):
        return LineType.STREET_ADDRESS_LINE, re.match(street_address_line_regex, line)

    raise Exception(f"Line Type not expected {line}")
