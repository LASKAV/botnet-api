from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from models.message_templates import (
    MessageTemplates,
    MessageTemplateCreate,
    MessageTemplatePublic,
    MessageTempUpdate,
)
from database import SessionDep
from .users import get_user_by_telegram_id

router = APIRouter(prefix="/message/templates", tags=["Message Templates"])


@router.post("")
async def create_template(
    telegram_id: int, template: MessageTemplateCreate, session: SessionDep
) -> MessageTemplatePublic:
    user = await get_user_by_telegram_id(telegram_id, session)

    message_templates_stmt = select(MessageTemplates).where(
        MessageTemplates.user_id == user.id,
        MessageTemplates.message == template.message,
    )

    result = await session.exec(message_templates_stmt)
    existing_template = result.first()

    if existing_template:
        raise HTTPException(
            status_code=400, detail="A template with this message already exists!"
        )

    db_message_templates = MessageTemplates(**template.model_dump(),
                                             user_id=user.id)

    session.add(db_message_templates)
    await session.commit()
    await session.refresh(db_message_templates)

    return db_message_templates


@router.patch("/{template_id}")
async def update_template(
    template_id: int, template: MessageTempUpdate, session: SessionDep
) -> MessageTemplatePublic:
    template_update = await session.get(MessageTemplates, template_id)

    if template_update is None:
        raise HTTPException(status_code=404, detail="Template not found")

    template_data = template.model_dump(exclude_unset=True)
    for key, value in template_data.items():
        setattr(template_update, key, value)

    session.add(template_update)
    await session.commit()
    await session.refresh(template_update)

    return template_update


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(template_id: int, session: SessionDep):
    template_delete = await session.get(MessageTemplates, template_id)

    if template_delete is None:
        raise HTTPException(status_code=404, detail="Template not found")

    await session.delete(template_delete)
    await session.commit()


@router.get("/{template_id}")
async def read_template(template_id: int, session: SessionDep) -> MessageTemplatePublic:
    message_templates_stmt = select(MessageTemplates).where(
        MessageTemplates.id == template_id
    )
    result = await session.exec(message_templates_stmt)
    db_message_templates = result.first()

    if db_message_templates is None:
        raise HTTPException(status_code=404, detail="Template not found")

    return db_message_templates


@router.get("")
async def read_templates(session: SessionDep) -> list[MessageTemplates]:
    statement = select(MessageTemplates)
    message_templates = await session.exec(statement)
    return message_templates.all()
