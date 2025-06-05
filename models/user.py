from sqlmodel import Field, Relationship, SQLModel
from typing import Optional, List, TYPE_CHECKING
from datetime import date


if TYPE_CHECKING:
    from .app import App
    from .proxy import Proxy
    from .account import Account
    from .message_templates import MessageTemplates
    from .subscription import Subscription


class UserBase(SQLModel):
    name: str
    telegram_id: int = Field(unique=True, index=True)
    admin: bool
    subscribing: bool
    language: str


class User(UserBase, table=True):
    __tablename__ = "users"

    id: int = Field(default=None, primary_key=True)
    date_craet: date = Field(default_factory=date.today)

    accounts: Optional[List["Account"]] = Relationship(
        back_populates="users",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    proxies: Optional[List["Proxy"]] = Relationship(
        back_populates="users",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    apps: Optional[List["App"]] = Relationship(
        back_populates="users",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    messages: Optional[List["MessageTemplates"]] = Relationship(
        back_populates="users",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    subscriptions: Optional[List["Subscription"]] = Relationship(
        back_populates="users",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class UserCreate(UserBase):
    pass


class UserPublic(UserBase):
    id: int


class UserUpdate(UserBase):
    pass
