from typing import Optional

from sqlmodel import Field, SQLModel
from pydantic import field_validator


class GroupLinkBase(SQLModel):
    link: str


class GroupLink(GroupLinkBase, table=True):
    __tablename__ = "group_links"
    id: int | None = Field(default=None, primary_key=True)
    link: str = Field(max_length=256)

    @field_validator("link")
    @classmethod
    def validate_link(cls, value: str) -> str:
        if len(value) > 256:
            raise ValueError("Link must not exceed 256 characters")
        return value.strip()


class LinkPublic(GroupLinkBase):
    id: int


class LinkCreate(GroupLinkBase):
    link: str


class LinkUpdate(SQLModel):
    link: str | None = None


class GroupLinkCreate(GroupLinkBase):
    account_id: list[int]
    day_limit: Optional[int] = None
    time_limit: Optional[int] = None
    link: list[str]
