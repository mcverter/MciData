import re
"""
Regular expressions for parsing MCI Data fies
"""

# Date and Cost
date_re = r"(\d{2}/\d{2}/\d{4})"
cost_re = r"(\d*\.\d{2})"
optional_cost_re = r"( \d*\.\d{2})?"

# For Borough Line
borough_re = r"(\w[\w ]+)"
zip_re = r"(\d{5})"
docket_no_re = r"(\w{10})"
status_re = "(OPEN|CLOSED)"
close_code_re = r"(\w{2})"
possible_mci_per_room_re = r"( \d*\.\d{2})?"

work_item_re = r"(^[A-Z]\D*)"

# Line Regexes
street_address_line_regex = re.compile(r"\d+.*")
borough_line_regex = re.compile(borough_re + ", NY " + zip_re + " " + docket_no_re + " " + status_re \
                     + " " + date_re + " " +  close_code_re + possible_mci_per_room_re)
work_line_regex = re.compile(work_item_re + " " + cost_re + optional_cost_re)

