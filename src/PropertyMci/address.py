from dataclasses import dataclass


@dataclass
class Address:
    """Street address of property"""

    street_address: str | None = None
    borough: str | None = None
    zip_code: str | None = None
