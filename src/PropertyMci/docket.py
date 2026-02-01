from dataclasses import dataclass


@dataclass
class Docket:
    """Court docket"""

    docket_number: str
    case_status: str
    close_code: str
    closing_date: str
    monthly_mci_incr_per_room: str | None
