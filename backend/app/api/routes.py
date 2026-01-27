from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pathlib import Path
import shutil
from concurrent.futures import ThreadPoolExecutor
import os
import logging
import traceback

from ..models.schemas import JobCreate, JobStatus
from ..services.jobs import create_job, get_job, list_jobs, update_job_status, _jobs
from ..core.config import settings
from ..services.watermark import process_job

router = APIRouter()

logger = logging.getLogger(__name__)

# Thread pool for parallel video processing
# Use a conservative number of workers (roughly half of CPUs, capped)
MAX_WORKERS = min(4, max(1, (os.cpu_count() or 2) // 2))
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.post("/jobs/reset")
def reset_jobs():
    """Clear all jobs (for testing only)."""
    _jobs.clear()
    return {"status": "reset"}


@router.post("/jobs", response_model=JobStatus)
def create_job_endpoint(payload: JobCreate):
    job = create_job(payload.input_name, payload.logo_name, payload.input_name, payload.logo_name)
    return JobStatus(
        id=job.id,
        status=job.status,
        input_name=job.input_name,
        logo_name=job.logo_name,
        output_name=job.output_name,
    )


@router.get("/jobs", response_model=list[JobStatus])
def list_jobs_endpoint():
    try:
        return [
            JobStatus(
                id=j.id,
                status=j.status,
                input_name=j.input_name,
                logo_name=j.logo_name,
                output_name=j.output_name,
                position=j.position,
                scale=j.scale,
                progress=j.progress,
            )
            for j in list_jobs()
        ]
    except Exception as e:
        tb = traceback.format_exc()
        logger.error("Error in list_jobs_endpoint: %s", e)
        # write to storage/errors.log if available
        try:
            errfile = Path(__file__).resolve().parents[3] / "storage" / "errors.log"
            errfile.parent.mkdir(parents=True, exist_ok=True)
            with errfile.open("a", encoding="utf-8") as f:
                f.write("---\n")
                f.write("list_jobs_endpoint error:\n")
                f.write(tb + "\n")
        except Exception:
            logger.exception("Failed to write error log")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/jobs/{job_id}", response_model=JobStatus)
def get_job_endpoint(job_id: str):
    try:
        job = get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return JobStatus(
            id=job.id,
            status=job.status,
            input_name=job.input_name,
            logo_name=job.logo_name,
            output_name=job.output_name,
            position=job.position,
            scale=job.scale,
            progress=job.progress,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in get_job_endpoint: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/jobs/upload", response_model=list[JobStatus])
def upload_and_create_jobs(
    background_tasks: BackgroundTasks,
    videos: list[UploadFile] = File(...),
    logo: UploadFile = File(...),
    position: str = "bottom-right",
    scale: float = 0.2,
):
    try:
        base_dir = Path(settings.storage_dir)
        input_dir = base_dir / "inputs"
        logo_dir = base_dir / "logos"
        output_dir = base_dir / "outputs"

        input_dir.mkdir(parents=True, exist_ok=True)
        logo_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        logo_path = logo_dir / logo.filename
        with logo_path.open("wb") as buffer:
            shutil.copyfileobj(logo.file, buffer)

        job_statuses: list[JobStatus] = []
        for video in videos:
            video_path = input_dir / video.filename
            with video_path.open("wb") as buffer:
                shutil.copyfileobj(video.file, buffer)

            job = create_job(video.filename, logo.filename, str(video_path), str(logo_path), position, scale)
            update_job_status(job.id, "queued")
            # Submit to thread pool for parallel processing (multiple videos at once)
            executor.submit(process_job, job.id, str(output_dir))

            job_statuses.append(
                JobStatus(
                    id=job.id,
                    status=job.status,
                    input_name=job.input_name,
                    logo_name=job.logo_name,
                    position=job.position,
                    scale=job.scale,
                    output_name=job.output_name,
                    progress=job.progress,
                )
            )

        return job_statuses
    except Exception as e:
        logger.error("Error in upload_and_create_jobs: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/jobs/{job_id}/download")
def download_job_output(job_id: str):
    try:
        job = get_job(job_id)
        if not job or not job.output_path:
            raise HTTPException(status_code=404, detail="Output not ready")
        return FileResponse(path=job.output_path, filename=job.output_name or Path(job.output_path).name)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in download_job_output: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")
