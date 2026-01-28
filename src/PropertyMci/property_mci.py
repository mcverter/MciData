"""MCI Item for Property Location and Docket"""

from dataclasses import dataclass

from src.PropertyMci.address import Address
from src.PropertyMci.docket import Docket
from src.PropertyMci.work_item import WorkItem


@dataclass
class PropertyMci:
    # docket_number: str | None = None
    # case_status: str | None = None
    # closing_date: str | None = None
    # close_code: str | None = None
    # monthly_mci_incr_per_room: str | None = None
    address: Address
    docket: Docket
    work_item: WorkItem | None
    # report_file: str | None = (
    #     None  # literal PDF filename (helps trace back to source document)
    # )
    # report_month: str | None = (
    #     None  # YYYY-MM month label derived from filename, Excel sortable/filterable
    # )
