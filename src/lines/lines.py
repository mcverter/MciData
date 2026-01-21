from enum import Enum
import re

from src.lines.counties import counties
from src.lines.regexes import (
    array_to_regex_or,
    borough_re,
    close_code_re,
    cost_re,
    date_re,
    docket_no_re,
    optional_cost_re,
    possible_mci_per_room_re,
    status_re,
    work_item_re,
    zip_re,
)
from src.lines.street_types import street_types


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
street_address_line_regex = re.compile(r"^\d+.*" + street_type_re + r".{0,7}$")
docket_line_regex = re.compile(
    "^"
    + docket_no_re
    + " "
    + status_re
    + " "
    + date_re
    + " "
    + close_code_re
    + possible_mci_per_room_re
)
borough_line_regex = re.compile(
    "^"
    + borough_re
    + ", NY "
    + zip_re
    + " "
    + docket_no_re
    + " "
    + status_re
    + " "
    + date_re
    + " "
    + close_code_re
    + possible_mci_per_room_re
)
work_line_regex = re.compile(
    "^" + work_item_re + " " + cost_re + optional_cost_re + "$"
)
office_of_rent_header = re.compile("^OFFICE OF RENT ADMINISTRATION")
nys_division_header = re.compile("^NYS DIVISION OF HOUSING AND COMMUNITY RENEWAL")
major_capital_header = re.compile("^MAJOR CAPITAL IMPROVEMENT CASES")
county_date_header = re.compile(
    "^FOR " + county_re + " COUNTY FROM " + date_re + " TO " + date_re
)
column_header_1 = re.compile(
    "^BLDG ADDRESS DOCKET NO CASE STATUS CLOSING DATE CLOSE CODE MONTHLY MCI INCR PER ROOM"
)
double_dash_line = re.compile(
    "^================================ ========= =========== ============ ========== ========================="
)
column_header_2 = re.compile("^MCI ITEM CLAIM COST ALLOW COST")
single_dash_line = re.compile("^-------------------- ------------ ------------")
total_cases_county_line = re.compile(r"^TOTAL CASES: (\d+)")
count_per_county_line = re.compile("^" + county_re + r": (\d+)")
total_cases_document_line = re.compile(r"^TOTAL NUMBER OF CASES: (\d+)")
# These lines get run together by pdfplumber!
total_cases_plus_nys_header = re.compile(
    r"^TOTAL NUMBER OF CASES: \d+NYS DIVISION OF HOUSING AND COMMUNITY RENEWAL"
)


def get_line_type_and_matches(
    line: str,
) -> tuple[LineType, re.Match[str]] | tuple[LineType, None]:
    # pdfplumber merges last line of page with first line of next page
    line = re.sub("NYS DIVISION OF HOUSING AND COMMUNITY RENEWAL", "", line)

    if line == "":
        return LineType.NYS_DIVISION_HEADER, None
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
    if m := re.match(street_address_line_regex, line):
        return LineType.STREET_ADDRESS_LINE, m
    if m := re.match(borough_line_regex, line):
        return LineType.BOROUGH_DOCKET_LINE, m
    if m := re.match(docket_line_regex, line):
        return LineType.DOCKET_LINE, m
    if m := re.match(work_line_regex, line):
        return LineType.MCI_WORK_LINE, m
    if m := re.match(total_cases_county_line, line):
        return LineType.TOTAL_CASES_COUNTY_LINE, m
    if m := re.match(count_per_county_line, line):
        return LineType.COUNT_PER_COUNTY_LINE, m
    if m := re.match(total_cases_document_line, line):
        return LineType.TOTAL_CASES_DOCUMENT_LINE, m
    if m := re.match(total_cases_plus_nys_header, line):
        return LineType.TOTAL_CASES_PLUS_NYS_DIVISION_HEADER, m
    raise Exception(f"Line Type not expected {line}")
