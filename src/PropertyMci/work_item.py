"""MCI Work Item"""

from dataclasses import dataclass


@dataclass
class WorkItem:
    mci_work: str
    claim_cost: str
    allow_cost: str
