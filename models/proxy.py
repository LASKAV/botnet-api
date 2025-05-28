from sqlmodel import Field, Relationship, SQLModel

from .account import Account


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
    label: str | None = None
    # How to use enums in sqlmodel: https://github.com/fastapi/sqlmodel/issues/401
    # Why not enum: https://github.com/sqlalchemy/alembic/issues/1254
    protocol: str
    address: str
    port: int
    username: str
    password: str

    accounts: list["Account"] = Relationship(back_populates="proxy")


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
