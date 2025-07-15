import yaml
from jinja2 import Template
from kubernetes_asyncio import client

from settings import settings

with open("/app/job-template.yaml", "r") as stream:
    template_text = stream.read()

job_template: Template = Template(template_text)


def serialize_job_name(account_id: int):
    return "account-job-" + str(account_id)


def deserialize_job_name(job_name: str):
    without_prefix = job_name.removeprefix("account-job-")
    return int(without_prefix)


async def create_kubernetes_job(api: client.BatchV1Api, account_id: int, owner_id: int):
    context = {
        "job_name": serialize_job_name(account_id),
        "account_id": account_id,
        "owner_id": owner_id
    }

    rendered_yaml = job_template.render(context)
    body = yaml.safe_load(rendered_yaml)
    await api.create_namespaced_job(settings.kube_namespace, body)


async def delete_kubernetes_job(api: client.BatchV1Api, account_id: int):
    await api.delete_namespaced_job(
        serialize_job_name(account_id), settings.kube_namespace
    )
