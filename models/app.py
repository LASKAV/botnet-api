from sqlmodel import Field, Relationship, SQLModel

from .account import Account
from .user import User


class AppBase(SQLModel):
    label: str | None = None
    api_id: int
    api_hash: str


class App(AppBase, table=True):
    __tablename__ = "apps"

    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")

    accounts: list["Account"] = Relationship(back_populates="apps")
    users: "User" = Relationship(back_populates="apps")


class AppCreate(AppBase):
    pass


class AppPublic(AppBase):
    id: int


class AppUpdate(AppBase):
    label: str | None = None
    api_id: int | None = None
    api_hash: str | None = None
