from __future__ import annotations
from pathlib import Path
import sys
import logging
from datetime import datetime

from ..services.jobs import get_job, update_job_status

logger = logging.getLogger(__name__)

# File-based logging for thread pool debugging
LOG_FILE = Path(__file__).resolve().parents[3] / "storage" / "processing.log"
LOG_FILE.parent.mkdir(exist_ok=True)

def log_to_file(message: str):
    """Write message to log file with timestamp for thread pool debugging"""
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {message}\n")
            f.flush()
    except Exception as e:
        print(f"Failed to write to log file: {e}", flush=True)


def _load_marker():
    root = Path(__file__).resolve().parents[3]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    import marker  # type: ignore
    return marker


def process_job(job_id: str, output_dir: str) -> None:
    job = get_job(job_id)
    if not job:
        msg = f"Job {job_id} not found"
        logger.error(msg)
        log_to_file(f"ERROR: {msg}")
        return

    log_to_file(f"Starting job {job_id}: {job.input_path} with {job.logo_path}")
    logger.info(f"Starting watermark job {job_id}: {job.input_path} with {job.logo_path}")
    update_job_status(job_id, "processing", progress=0)
    
    try:
        marker = _load_marker()
        log_to_file(f"Job {job_id}: Loading video {job.input_path}")
        logger.info(f"Processing video: {job.input_path}")
        update_job_status(job_id, "processing", progress=10)
        
        # Pass position and scale parameters to watermarking
        output_path = marker.add_watermark(
            job.input_path, 
            job.logo_path, 
            output_dir,
            position=job.position,
            scale=job.scale
        )
        log_to_file(f"Job {job_id}: Watermark applied, progress to 90%")
        update_job_status(job_id, "processing", progress=90)
        logger.info(f"Watermark completed, output: {output_path}")
        
        if not output_path or not Path(output_path).exists():
            msg = f"Output file not found: {output_path}"
            log_to_file(f"ERROR Job {job_id}: {msg}")
            logger.error(msg)
            update_job_status(job_id, "failed", progress=0)
            return
            
        output_name = Path(output_path).name
        log_to_file(f"Job {job_id}: COMPLETED - Output: {output_name}")
        logger.info(f"Job {job_id} completed successfully")
        update_job_status(job_id, "completed", output_name=output_name, output_path=output_path, progress=100)
    except Exception as e:
        msg = f"Job {job_id} failed: {str(e)}"
        log_to_file(f"ERROR: {msg}")
        logger.error(msg, exc_info=True)
        import traceback
        tb = traceback.format_exc()
        log_to_file(tb)
        update_job_status(job_id, "failed", progress=0)

