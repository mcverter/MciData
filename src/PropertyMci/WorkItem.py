from pydantic import BaseModel


class WorkItem(BaseModel):
    name: str | None = None
    claim_cost: str | None = None
    allow_cost: str | None = None
