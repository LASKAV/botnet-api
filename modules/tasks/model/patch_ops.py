from typing import Literal
from pydantic import BaseModel


class PatchWaitingCode(BaseModel):
    op: Literal["replace"]
    path: str = "/waiting_code"
    value: bool


class PatchWarmUp(BaseModel):
    op: Literal["replace"]
    path: str = "/warm_up"
    value: bool


class PatchJoin(BaseModel):
    op: Literal["replace"]
    path: str = "/join"
    value: bool


class PatchMail(BaseModel):
    op: Literal["replace"]
    path: str = "/mail"
    value: bool


class PatchInvite(BaseModel):
    op: Literal["replace"]
    path: str = "/invite"
    value: bool


class PatchContact(BaseModel):
    op: Literal["add", "remove", "replace"]
    path: str = "/contact"
    value: list[str]


class PatchJoinGroup(BaseModel):
    op: Literal["add", "remove", "replace"]
    path: str = "/join_group"
    value: list[str]


class PatchSpam(BaseModel):
    op: Literal["add", "remove", "replace"]
    path: str = "/spam"
    value: list[str]


class PatchInvitation(BaseModel):
    op: Literal["add", "remove", "replace"]
    path: str = "/invitation"
    value: str
