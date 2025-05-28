from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from ..account import Account


class InvitationTaskBase(SQLModel):
    account_id: int = Field(foreign_key="accounts.id", primary_key=True)
    target_link: Optional[str] = None


class InvitationTask(InvitationTaskBase, table=True):
    __tablename__ = "invitation_tasks"
    
    account: Optional["Account"] = Relationship(back_populates="invitation_tasks")


class InvitationTaskCreate(InvitationTaskBase):
    account_id: List[int]
    target_link: str
    description: str = "invitation"
    day_limit: Optional[int] = None
    time_limit: Optional[int] = None