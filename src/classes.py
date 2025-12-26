from pydantic import BaseModel

"""
Classes for parsing MCI Files
"""


class WorkItem(BaseModel):
    name: str | None = None
    claim_cost: str | None = None
    allow_cost: str | None = None


class Address(BaseModel):
    street_address: str | None = None
    borough: str | None = None
    zip_code: str | None = None


class PropertyMci(BaseModel):
    docket_number: str | None = None
    case_status: str | None = None
    closing_date: str | None = None
    close_code: str | None = None
    monthly_mci_incr_per_room: str | None = None
    address: Address | None = None
    work_items: list[WorkItem]
    report_file: str | None = (
        None  # literal PDF filename (helps trace back to source document)
    )
    report_month: str | None = (
        None  # YYYY-MM month label derived from filename, Excel sortable/filterable
    )
