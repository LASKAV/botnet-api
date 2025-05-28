from fastapi import APIRouter, HTTPException
from sqlmodel import select

from database import SessionDep
from models.tasks.join_group_task import JoinGroupTask

router = APIRouter(prefix="/group/join/tasks", tags=["Join Group Tasks"])


@router.get("/{account_id}")
async def read_join_group_tasks(account_id: int, session: SessionDep):
    tasks = select(JoinGroupTask).where(JoinGroupTask.account_id == account_id)
    result = await session.exec(tasks)
    answer = result.all()
    if answer is None:
        raise HTTPException(status_code=404, detail="Group link not found")

    return answer
