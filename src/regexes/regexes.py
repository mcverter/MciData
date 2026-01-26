"""Regular expressions for parsing MCI Data fies"""

from src.regexes.work_status import work_status


def array_to_regex_or(arr: list[str]) -> str:
    """Converts list of strings to regex OR string"""
    return "(" + "|".join(arr) + ")"


# Date and Cost
date_re = r"(\d{2}/\d{2}/\d{4})"
# Costs are assumed to include cents (two decimal places) according to current report formatting.
cost_re = r"(\d*\.\d{2})"
optional_cost_re = r"( \d*\.\d{2})?"

# For Borough Line
borough_re = r"(\w[\w ]+)"
zip_re = r"(\d{5})"
docket_no_re = r"([A-Z]{2}[0-9]{6}[A-Z]{2})"  # r"(\w{9, 10})" # # JX630020OM
status_re = array_to_regex_or(work_status)  # "(OPEN|CLOSED)"
close_code_re = r"(\w{2})"
# Monthly MCI increment values can appear with whole numbers or 1 to 2 decimal places (e.g., 0.3 or 18.66).
possible_mci_per_room_re = r"( \d*(?:\.\d{1,2})?)?"

work_item_re = r"(.*?)"

town_state_zip_re = ""
