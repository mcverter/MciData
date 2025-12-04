from pydantic import BaseModel
from typing import Optional
"""
Classes for parsing MCI Files
"""
class WorkItem(BaseModel):
    name: Optional[str] = None
    claim_cost: Optional[str] = None 
    allow_cost: Optional[str] = None 

class Address(BaseModel):
    street_address: Optional[str] = None
    borough: Optional[str] = None 
    zip_code: Optional[str] = None

class PropertyMci(BaseModel):
    docket_number: Optional[str] = None
    case_status: Optional[str] = None 
    closing_date: Optional[str] = None
    close_code: Optional[str] = None
    monthly_mci_incr_per_room: Optional[str] = None
    address: Optional[Address] = None
    work_items: list[WorkItem]
    report_file: Optional[str] = None  # literal PDF filename (helps trace back to source document)
    report_month: Optional[str] = None  # YYYY-MM month label derived from filename, Excel sortable/filterable
