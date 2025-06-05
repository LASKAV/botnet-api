from typing import TYPE_CHECKING, Optional, List

from pydantic import BaseModel
from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel
from .tasks.contact_task import ContactTask

if TYPE_CHECKING:
    from .app import App
    from .proxy import Proxy
    from .limit import Limit
    from .tasks.contact_task import ContactTask
    from .tasks.join_group_task import JoinGroupTask
    from .tasks.spammer_task import SpammerTask
    from .tasks.invitation_task import InvitationTask
    from .user import User


class AccountBase(SQLModel):
    phone: str = Field(unique=True)
    label: Optional[str] = None
    password: Optional[str] = None
    session: Optional[str] = None

    app_id: int = Field(foreign_key="apps.id")
    proxy_id: Optional[int] = Field(default=None, foreign_key="proxies.id")


class Account(AccountBase, table=True):
    __tablename__ = "accounts"

    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_id: Optional[int] = None

    waiting_code: bool = False
    warm_up: bool = False
    join: bool = False
    mail: bool = False
    invite: bool = False

    user_id: int = Field(foreign_key="users.id")

    emoji: List[str] = Field(
        default_factory=lambda: ["❤", "🔥", "👍"],
        sa_column=Column(JSON, server_default='["❤", "🔥", "👍"]'),
    )

    apps: "App" = Relationship(back_populates="accounts")

    users: "User" = Relationship(back_populates="accounts")

    proxies: Optional["Proxy"] = Relationship(back_populates="accounts")

    limits: List["Limit"] = Relationship(
        back_populates="account",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    accounts: Optional[List["ContactTask"]] = Relationship(
        back_populates="account",
        sa_relationship_kwargs={
            "foreign_keys": "ContactTask.account_id",
            "cascade": "all, delete-orphan",
        },
    )

    contacts: Optional[List["ContactTask"]] = Relationship(
        back_populates="contact",
        sa_relationship_kwargs={
            "foreign_keys": "ContactTask.contact_id",
            "cascade": "all, delete-orphan",
        },
    )

    group_tasks: Optional[List["JoinGroupTask"]] = Relationship(
        back_populates="account",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    spammer_tasks: Optional[List["SpammerTask"]] = Relationship(
        back_populates="account",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    invitation_tasks: Optional[List["InvitationTask"]] = Relationship(
        back_populates="account",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class AccountCreate(AccountBase):
    pass


class AccountPublic(AccountBase):
    id: int


class AccountUpdate(AccountBase):
    phone: Optional[str] = None
    label: Optional[str] = None
    password: Optional[str] = None
    app_id: Optional[int] = None
    proxy_id: Optional[int] = None
    session: Optional[str] = None


class AccountEmojiUpdate(BaseModel):
    emoji: Optional[List[str]] = None


class AccountEmojiResponse(BaseModel):
    id: int
    emoji: List[str]
