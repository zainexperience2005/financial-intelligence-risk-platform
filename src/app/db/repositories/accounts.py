from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Account


def get_account_by_business_id(
    session: Session,
    account_id: str,
) -> Account | None:
    """Retrieves an account by its unique business account ID (e.g., 'ACC-1001')."""
    statement = select(Account).where(Account.account_id == account_id)
    return session.scalar(statement)


def freeze_account_record(
    account: Account,
) -> None:
    """Freezes an account record. Narrow, controlled write surface."""
    account.status = "frozen"
