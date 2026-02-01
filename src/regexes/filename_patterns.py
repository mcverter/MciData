import re

mci_report_pattern = re.compile(
    r"(?P<direct_feed>(DirectFeed-\d\d-)?)"

    r"(?P<month>january|february|march|april|may|june|july|august|september|october|november|december)"
    r"-(?P<year>\d{4})"

    "-mci-closed-case-report",
    re.IGNORECASE,
)
month_lookup = {
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


def is_valid_input_filename(filename: str) -> bool:
    return filename[-4:] in [".pdf", ".txt"] and re.match(mci_report_pattern, filename)


def derive_report_month(filename: str) -> str:
    """
    Derives a sortable YYYY-MM label from the report filename.
    Returns an empty string when the pattern does not match.
    """
    if match := mci_report_pattern.search(filename):
        month = match.group("month").lower()
        year = match.group("year")
        month_number = month_lookup.get(month)
        if month_number:
            return f"{year}-{month_number}"
    return ""
