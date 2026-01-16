from src.lines.lines import LineType, get_line_type_and_matches

NO_LINE = ""
NYS_DIVISION_HEADER = "NYS DIVISION OF HOUSING AND COMMUNITY RENEWAL"
OFFICE_OF_RENT_HEADER = "OFFICE OF RENT ADMINISTRATION"
MAJOR_CAPITAL_HEADER = "MAJOR CAPITAL IMPROVEMENT CASES"
COUNTY_DATE_HEADER = "FOR NASSAU COUNTY FROM 05/01/2024 TO 05/31/2024"
COLUMN_HEADER_1 = "BLDG ADDRESS DOCKET NO CASE STATUS CLOSING DATE CLOSE CODE MONTHLY MCI INCR PER ROOM"
COLUMN_HEADER_2 = "MCI ITEM CLAIM COST ALLOW COST"
DASHES = "-------------------- ------------ ------------"
DOUBLE_DASHES = "================================ ========= =========== ============ ========== ========================="
STREET_ADDRESS_LINE = "465 SHORE RD"
BOROUGH_DOCKET_LINE = "LONG BEACH, NY 11561 MP710004OM CLOSED 05/02/2024 VO"
DOCKET_LINE = "MP710004OM CLOSED 05/02/2024 VO"
MCI_WORK_LINE = "ELEVATOR UPGRADING 155787.00 154098.70"
TOTAL_CASES_COUNTY_LINE = "TOTAL CASES: 14"
COUNT_PER_COUNTY_LINE = "QUEENS: 8"
TOTAL_CASES_DOCUMENT_LINE = "TOTAL NUMBER OF CASES: 38"


def test_well_formed_lines_processed():
    assert (
        get_line_type_and_matches(NYS_DIVISION_HEADER)[0]
        == LineType.NYS_DIVISION_HEADER
    )
    assert (
        get_line_type_and_matches(OFFICE_OF_RENT_HEADER)[0]
        == LineType.OFFICE_OF_RENT_HEADER
    )
    assert (
        get_line_type_and_matches(MAJOR_CAPITAL_HEADER)[0]
        == LineType.MAJOR_CAPITAL_HEADER
    )
    assert (
        get_line_type_and_matches(COUNTY_DATE_HEADER)[0] == LineType.COUNTY_DATE_HEADER
    )
    assert get_line_type_and_matches(COLUMN_HEADER_1)[0] == LineType.COLUMN_HEADER_1
    assert get_line_type_and_matches(COLUMN_HEADER_2)[0] == LineType.COLUMN_HEADER_2
    assert get_line_type_and_matches(DOUBLE_DASHES)[0] == LineType.DOUBLE_DASHES
    assert get_line_type_and_matches(DASHES)[0] == LineType.DASHES
    assert (
        get_line_type_and_matches(STREET_ADDRESS_LINE)[0]
        == LineType.STREET_ADDRESS_LINE
    )
    assert (
        get_line_type_and_matches(BOROUGH_DOCKET_LINE)[0]
        == LineType.BOROUGH_DOCKET_LINE
    )
    assert get_line_type_and_matches(DOCKET_LINE)[0] == LineType.DOCKET_LINE
    assert get_line_type_and_matches(MCI_WORK_LINE)[0] == LineType.MCI_WORK_LINE
    assert (
        get_line_type_and_matches(COUNT_PER_COUNTY_LINE)[0]
        == LineType.COUNT_PER_COUNTY_LINE
    )
    assert (
        get_line_type_and_matches(TOTAL_CASES_DOCUMENT_LINE)[0]
        == LineType.TOTAL_CASES_DOCUMENT_LINE
    )
    assert (
        get_line_type_and_matches(TOTAL_CASES_COUNTY_LINE)[0]
        == LineType.TOTAL_CASES_COUNTY_LINE
    )


def test_unexpected_lines_log_errors():
    pass
