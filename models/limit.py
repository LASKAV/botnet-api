from .account import Account
from sqlmodel import Field, Relationship, SQLModel
from typing import Optional
from datetime import datetime


class LimitBase(SQLModel):
    action_type: str
    day_limit: int = Field(default=20)
    fact_limit: int = Field(default=20)
    time_limit: int = Field(default=60)
    time_update: Optional[datetime] = None

    account_id: int = Field(foreign_key="accounts.id")


class Limit(LimitBase, table=True):
    __tablename__ = "limits"

    id: int = Field(default=None, primary_key=True)

    account: Optional["Account"] = Relationship(back_populates="limits")


class LimitCreate(LimitBase):
    account_id: int
    action_type: str
    day_limit: Optional[int] = 20
    time_limit: Optional[int] = 60
    fact_limit: Optional[int] = 20
    


class LimitPublic(LimitBase):
    id: int


class LimitUpdate(SQLModel):
    action_type: Optional[str] = None
    day_limit: Optional[int] = None
    fact_limit: Optional[int] = None
    time_limit: Optional[int] = None
    time_update: Optional[datetime] = None
    account_id: Optional[int] = None