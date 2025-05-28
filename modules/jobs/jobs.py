import logging

from fastapi import APIRouter, HTTPException
from kubernetes_asyncio import client
from pydantic import BaseModel

from database import SessionDep
from models.account import Account
from settings import settings

from .k8s_utils import (
    create_kubernetes_job,
    delete_kubernetes_job,
    deserialize_job_name,
    serialize_job_name,
)

logger = logging.getLogger("uvicorn")


router = APIRouter(tags=["Jobs"])


class JobStatus(BaseModel):
    active: bool


@router.get("/jobs")
async def read_jobs() -> list[int]:
    jobs: client.V1JobList = []

    async with client.ApiClient() as api:
        batch_v1 = client.BatchV1Api(api)
        jobs: client.V1JobList = await batch_v1.list_namespaced_job(
            namespace=settings.kube_namespace
        )

    jobs_accounts_ids = []

    for job in jobs.items:
        try:
            account_id = deserialize_job_name(job.metadata.name)
            jobs_accounts_ids.append(account_id)
        except ValueError:
            logger.warning(f'Job "{job.metadata.name}" has invalid name')

    return jobs_accounts_ids


@router.get("/accounts/{account_id}/job")
async def read_account_job(account_id: int, session: SessionDep) -> JobStatus:
    account = await session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    async with client.ApiClient() as api:
        batch_v1 = client.BatchV1Api(api)

        job: client.V1Job | None = None

        try:
            job = await batch_v1.read_namespaced_job_status(
                name=serialize_job_name(account_id), namespace=settings.kube_namespace
            )
        except client.ApiException:
            pass

        if job:
            return JobStatus(active=True)
        else:
            return JobStatus(active=False)


@router.put("/accounts/{account_id}/job")
async def update_job_status(
    account_id: int, req_body: JobStatus, session: SessionDep
) -> JobStatus:
    account = await session.get(Account, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    async with client.ApiClient() as api:
        batch_v1 = client.BatchV1Api(api)
        core_v1 = client.CoreV1Api(api)

        job: client.V1Job | None = None

        try:
            job = await batch_v1.read_namespaced_job_status(
                name=serialize_job_name(account_id), namespace=settings.kube_namespace
            )
        except client.ApiException as e:
            logger.info("Job not found", exc_info=e)

        if job is None and req_body.active:
            old_job_pods: client.V1PodList = await core_v1.list_namespaced_pod(
                settings.kube_namespace, label_selector=f"account-job-{account_id}"
            )
            if old_job_pods.items:
                logger.warning(f"Job pods for account {account_id} not deleted yet")
                raise HTTPException(status_code=409, detail="Job pods not deleted yet")

            logger.info(f"Creating job for account {account_id}")
            await create_kubernetes_job(batch_v1, account_id)
            return JobStatus(active=True)

        if job and not req_body.active:
            await delete_kubernetes_job(batch_v1, account_id)
            return JobStatus(active=False)

        return req_body
