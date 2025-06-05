from sqlmodel import Field, Relationship, SQLModel

from .account import Account
from .user import User


class ProxyBase(SQLModel):
    label: str | None = None
    protocol: str
    address: str
    port: int
    username: str
    password: str


class Proxy(ProxyBase, table=True):
    __tablename__ = "proxies"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")

    accounts: list["Account"] = Relationship(back_populates="proxy")
    users: "User" = Relationship(back_populates="proxies")


class ProxyCreate(ProxyBase):
    pass


class ProxyPublic(ProxyBase):
    id: int


class ProxyUpdate(ProxyBase):
    label: str | None = None
    protocol: str | None = None
    address: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None
