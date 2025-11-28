# services/backend/app/main.py

from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
import uuid
import time
import asyncio

from sqlmodel import select

from .config import UPLOAD_DIR, PROCESSED_DIR, CORS_ORIGINS
from .db import create_db_and_tables, get_session
from .models import Job, JobLog
from .tasks import process_job_async

# Create tables at startup (SQLite dev or DB from env)
create_db_and_tables()

app = FastAPI(title="ChangeAnyFile API - No Docker / Async Worker")

# CORS: DEV - allow all; you can restrict later
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_MIME = {
    "image/png",
    "image/jpeg",
    "image/webp",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")

    file_id = str(uuid.uuid4())
    filename = f"{file_id}--{file.filename}"
    dest_path = UPLOAD_DIR / filename
    with open(dest_path, "wb") as f:
        f.write(contents)

    print(f"[upload] Saved file to: {dest_path}")
    return {
        "fileId": file_id,
        "originalName": file.filename,
        "savedName": filename,
        "size": len(contents),
        "contentType": file.content_type,
    }


@app.post("/jobs")
async def create_job(payload: dict = Body(...)):
    print("[/jobs] payload received:", payload)

    try:
        file_id = payload.get("fileId")
        prompt = payload.get("prompt", "").strip() if payload.get("prompt") else ""

        if not file_id:
            raise HTTPException(status_code=400, detail="fileId is required")

        # check uploaded file exists
        matches = list(UPLOAD_DIR.glob(f"{file_id}--*"))
        if not matches:
            raise HTTPException(status_code=404, detail="Uploaded file not found")

        original_name = matches[0].name.split("--", 1)[1]

        # --- DB work ---
        session = get_session()

        # create Job row
        job = Job(file_id=file_id, original_name=original_name, prompt=prompt)
        session.add(job)
        session.commit()
        session.refresh(job)

        # log: job created
        log = JobLog(job_id=job.job_id, message="Job created and queued.")
        session.add(log)
        session.commit()

        # 🔑 capture values before closing the session
        job_id = job.job_id
        status = job.status
        created_at = job.created_at

        session.close()

        # start async processing in background (no Celery)
        asyncio.create_task(process_job_async(job_id))

        return {
            "jobId": job_id,
            "status": status,
            "createdAt": created_at,
        }

    except HTTPException:
        raise
    except Exception as e:
        print("[/jobs] ERROR:", repr(e))
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")


@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    session = get_session()

    stmt = select(Job).where(Job.job_id == job_id)
    job = session.exec(stmt).first()
    if not job:
        session.close()
        raise HTTPException(status_code=404, detail="Job not found")

    logs_stmt = select(JobLog).where(JobLog.job_id == job.job_id).order_by(JobLog.created_at)
    logs = [r.message for r in session.exec(logs_stmt).all()]

    result = (
        {
            "filename": job.result_filename,
            "path": job.result_path,
            "size": job.result_size,
        }
        if job.status == "completed" and job.result_path
        else None
    )

    session.close()

    return {
        "jobId": job.job_id,
        "fileId": job.file_id,
        "originalName": job.original_name,
        "prompt": job.prompt,
        "status": job.status,
        "createdAt": job.created_at,
        "updatedAt": job.updated_at,
        "result": result,
        "logs": logs,
    }


@app.get("/download/result/{job_id}")
async def download_result(job_id: str):
    session = get_session()
    stmt = select(Job).where(Job.job_id == job_id)
    job = session.exec(stmt).first()
    session.close()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "completed" or not job.result_path:
        raise HTTPException(status_code=400, detail="Result not available yet")

    result_path = Path(job.result_path)
    if not result_path.exists():
        raise HTTPException(status_code=500, detail="Result file missing")

    return FileResponse(
        path=str(result_path),
        filename=job.result_filename,
        media_type="application/octet-stream",
    )
