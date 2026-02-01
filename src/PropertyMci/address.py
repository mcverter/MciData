from dataclasses import dataclass


@dataclass
class Address:
    """Street address of property"""

    street_address: str | None = None
    neighborhood: str | None = None
    county: str | None = None
    zip_code: str | None = None
