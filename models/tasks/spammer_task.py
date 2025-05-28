from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from ..account import Account


class SpammerTaskBase(SQLModel):
    account_id: int = Field(foreign_key="accounts.id", primary_key=True)
    message_template_id: int = Field(foreign_key="message_templates.id", primary_key=True)


class SpammerTask(SpammerTaskBase, table=True):
    __tablename__ = "spammer_tasks"
    
    account: Optional["Account"] = Relationship(back_populates="spammer_tasks")


class SpammerTaskCreate(SpammerTaskBase):
    account_id: List[int]
    message_template_id: List[int]
    description: str = "mailing"
    day_limit: Optional[int] = None
    time_limit: Optional[int] = None