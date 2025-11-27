# services/backend/app/tasks.py
"""
Async job processor without Celery / Redis.

We:
- Read Job from DB
- Update status & logs
- Copy file from uploads -> processed with "-processed" suffix
"""

import time
import shutil
import asyncio
from sqlmodel import select

from .db import get_session
from .models import Job, JobLog
from .config import UPLOAD_DIR, PROCESSED_DIR


async def process_job_async(job_id: str):
    """
    Process a single job asynchronously:
    - Mark status = processing
    - Find uploaded file
    - Copy to processed
    - Mark status = completed or failed
    """
    session = get_session()
    try:
        stmt = select(Job).where(Job.job_id == job_id)
        job = session.exec(stmt).first()
        if not job:
            print(f"[worker] Job {job_id} not found")
            return

        def add_log(msg: str):
            log = JobLog(job_id=job.job_id, message=msg)
            session.add(log)
            session.commit()

        # mark processing
        job.status = "processing"
        job.updated_at = int(time.time())
        session.add(job)
        session.commit()
        add_log("Worker started processing (async).")

        # find the uploaded file
        matches = list(UPLOAD_DIR.glob(f"{job.file_id}--*"))
        if not matches:
            add_log("Uploaded file not found on disk.")
            job.status = "failed"
            job.updated_at = int(time.time())
            session.add(job)
            session.commit()
            return

        src = matches[0]
        processed_name = f"{src.stem}-processed{src.suffix}"
        dest = PROCESSED_DIR / processed_name

        add_log(f"Copying {src.name} -> {processed_name}")
        # simulate some delay
        await asyncio.sleep(1)

        # copy file (blocking but quick; okay for dev)
        shutil.copy2(src, dest)
        add_log("File copied to processed folder.")

        await asyncio.sleep(2)

        job.result_filename = processed_name
        job.result_path = str(dest)
        job.result_size = dest.stat().st_size
        job.status = "completed"
        job.updated_at = int(time.time())
        session.add(job)
        session.commit()

        add_log("Processing completed successfully.")
        print(f"[worker] job {job_id} completed")

    except Exception as e:
        print(f"[worker] job {job_id} failed: {e}")
        # best-effort: mark failed
        try:
            job.status = "failed"
            job.updated_at = int(time.time())
            session.add(job)
            session.commit()
        except Exception:
            pass
    finally:
        session.close()
