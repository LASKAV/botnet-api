from sqlmodel import Field, SQLModel
from pydantic import field_validator

"""
Model for message_templates_tasks table
This model is used to store the message templates for the tasks
"""


class MessageTemplatesBase(SQLModel):
    description: str
    message: str


class MessageTemplates(MessageTemplatesBase, table=True):
    __tablename__ = "message_templates"

    id: int | None = Field(default=None, primary_key=True)
    description: str = Field(max_length=100)

    # Chat message - 4096 characters for Telegram
    message: str | None = Field(max_length=4096)

    """
    Pydantic validator
    """

    # Validator for description
    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        if len(value) > 100:
            raise ValueError("Description must not exceed 100 characters")
        return value.strip()

    # Validator for message
    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        if len(value) > 4096:
            raise ValueError("Message must not exceed 4096 characters")
        return value.strip()


class MessageTemplateCreate(MessageTemplatesBase):
    description: str
    message: str


class MessageTemplatePublic(MessageTemplatesBase):
    id: int


class MessageTempUpdate(MessageTemplatesBase):
    description: str | None = None
    message: str | None = None