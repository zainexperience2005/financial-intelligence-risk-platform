from typing import Literal

from pydantic import BaseModel


class ProposedAction(BaseModel):
    action: Literal["freeze_account"]

    account_id: str

    reason: str


class ActionResult(BaseModel):
    action: str
    account_id: str
    success: bool
    message: str
