from contextlib import asynccontextmanager
from fastapi import FastAPI
from kubernetes_asyncio import config

from modules import (
    accounts,
    apps,
    proxies,
    tasks,
    message_templates,
    group_links,
    join_group_tasks,
    spammer,
    limits,
    invitations,
    account_management,
    jobs,
    users,
)
from settings import settings


async def init_k8s():
    if not settings.enable_kube:
        return

    if settings.kube_config_path:
        await config.load_kube_config(
            config_file=settings.kube_config_path.__str__(),
            context=settings.kube_context,
        )
    else:
        config.load_incluster_config()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_k8s()
    yield


app = FastAPI(redirect_slashes=True, lifespan=lifespan)

app.include_router(apps.router)
# app.include_router(proxies.router)
# app.include_router(accounts.router)
# app.include_router(account_management.router)
# app.include_router(tasks.router)
# app.include_router(message_templates.router)
# app.include_router(group_links.router)
# app.include_router(join_group_tasks.router)
# app.include_router(limits.router)
# app.include_router(spammer.router)
# app.include_router(invitations.router)
app.include_router(users.router)

if settings.enable_kube:
    app.include_router(jobs.router)
