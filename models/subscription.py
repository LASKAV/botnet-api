from sqlmodel import Field, Relationship, SQLModel
from typing import Optional
from datetime import date
# from .user import User


class SubscriptionBase(SQLModel):
    name: str
    payment_tx_hash: str
    payment_currency: str
    amount_paid: float
    wallet_address: str
    user_wallet: str | None = None
    expires_at: date
    status: str  # active, expired, pending


class Subscription(SubscriptionBase, table=True):
    __tablename__ = "subscriptions"

    id: int = Field(default=None, primary_key=True)
    created_at: date = Field(default_factory=date.today)

    user_id: Optional[int] = Field(foreign_key="users.id")

    # users: "User" = Relationship(back_populates="subscriptions")
