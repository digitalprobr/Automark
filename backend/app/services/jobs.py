from __future__ import annotations
from dataclasses import dataclass
from typing import Dict
import uuid


@dataclass
class Job:
    id: str
    status: str
    input_name: str
    logo_name: str
    input_path: str
    logo_path: str
    output_name: str | None = None
    output_path: str | None = None
    position: str = "bottom-right"
    scale: float = 0.2
    progress: int = 0  # 0-100 percentage
    file_size: int | None = None  # file size in bytes


_jobs: Dict[str, Job] = {}


def create_job(input_name: str, logo_name: str, input_path: str, logo_path: str, position: str = "bottom-right", scale: float = 0.2, file_size: int | None = None) -> Job:
    job_id = str(uuid.uuid4())
    job = Job(
        id=job_id,
        status="queued",
        input_name=input_name,
        logo_name=logo_name,
        input_path=input_path,
        logo_path=logo_path,
        position=position,
        scale=scale,
        file_size=file_size,
    )
    _jobs[job_id] = job
    return job


def get_job(job_id: str) -> Job | None:
    return _jobs.get(job_id)


def list_jobs() -> list[Job]:
    return list(_jobs.values())


def update_job_status(job_id: str, status: str, output_name: str | None = None, output_path: str | None = None, progress: int | None = None) -> None:
    job = _jobs.get(job_id)
    if not job:
        return
    job.status = status
    job.output_name = output_name
    job.output_path = output_path
    if progress is not None:
        job.progress = progress
