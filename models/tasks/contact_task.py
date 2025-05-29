from sqlmodel import CheckConstraint, Field, SQLModel, Relationship
from typing import Optional
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..account import Account


class ContactTaskBase(SQLModel):
    account_id: int = Field(foreign_key="accounts.id", primary_key=True)
    contact_id: int = Field(foreign_key="accounts.id", primary_key=True)
    user_id: int = Field(foreign_key="user.id")


class ContactTask(ContactTaskBase, table=True):
    __tablename__ = "contact_tasks"
    __table_args__ = (CheckConstraint("account_id != contact_id"),)

    account: Optional["Account"] = Relationship(
        back_populates="accounts",
        sa_relationship_kwargs={"foreign_keys": "ContactTask.account_id"},
    )

    contact: Optional["Account"] = Relationship(
        back_populates="contacts",
        sa_relationship_kwargs={"foreign_keys": "ContactTask.contact_id"},
    )
