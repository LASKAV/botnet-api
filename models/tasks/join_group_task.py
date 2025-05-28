from sqlmodel import Field, SQLModel, Relationship
from ..account import Account
from typing import Optional


class JoinGroupTaskBase(SQLModel):
    account_id: int = Field(foreign_key="accounts.id", primary_key=True)
    group_link_id: int = Field(foreign_key="group_links.id",
                                primary_key=True)
    

class JoinGroupTask(JoinGroupTaskBase, table=True):
    __tablename__ = "join_group_tasks"

    account: Optional["Account"] = Relationship(back_populates="group_tasks")





