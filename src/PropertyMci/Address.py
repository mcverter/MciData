from pydantic import BaseModel


class Address(BaseModel):
    street_address: str | None = None
    borough: str | None = None
    zip_code: str | None = None
