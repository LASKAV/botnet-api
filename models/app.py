from sqlmodel import Field, Relationship, SQLModel

from .account import Account


class AppBase(SQLModel):
    label: str | None = None
    api_id: int
    api_hash: str


class App(AppBase, table=True):
    __tablename__ = "apps"

    id: int = Field(default=None, primary_key=True)

    accounts: list["Account"] = Relationship(back_populates="app")


class AppCreate(AppBase):
    pass


class AppPublic(AppBase):
    id: int


class AppUpdate(AppBase):
    label: str | None = None
    api_id: int | None = None
    api_hash: str | None = None
