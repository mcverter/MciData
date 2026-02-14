"""MCI Work Item for Property Location and Docket"""

from dataclasses import dataclass

from src.PropertyMci.address import Address
from src.PropertyMci.docket import Docket
from src.PropertyMci.work_item import WorkItem


@dataclass
class PropertyMci:
    """MCI Work Item for Property Location and Docket"""

    address: Address
    docket: Docket
    work_item: WorkItem | None
