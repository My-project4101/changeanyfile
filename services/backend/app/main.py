from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlmodel import select
from pathlib import Path
from mimetypes import guess_type
import shutil
import uuid
import json
import time

from .db import get_session, init_db
from .models import Job
from .schemas import CreateJobRequest
from .ai_parser import parse_prompt_with_ai

from .tasks import process_job_async

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"

UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_id = f"{uuid.uuid4()}--{file.filename}"
    dest = UPLOAD_DIR / file_id

    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {
        "file_id": file_id,
        "original_name": file.filename
    }


@app.post("/jobs")
async def create_job(
    req: CreateJobRequest,
    background_tasks: BackgroundTasks
):
    session = get_session()

    actions = parse_prompt_with_ai(req.prompt)

    job = Job(
        file_id=req.file_id,
        original_name=req.file_id.split("--", 1)[-1],
        prompt=req.prompt,
        actions_json=json.dumps(actions),
        status="queued",
        created_at=int(time.time()),
        updated_at=int(time.time())
    )

    session.add(job)
    session.commit()
    session.refresh(job)

    background_tasks.add_task(process_job_async, job.job_id)

    session.close()
    return job


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    session = get_session()
    job = session.exec(
        select(Job).where(Job.job_id == job_id)
    ).first()
    session.close()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@app.get("/download/result/{job_id}")
def download_result(job_id: str):
    session = get_session()
    job = session.exec(
        select(Job).where(Job.job_id == job_id)
    ).first()
    session.close()

    if not job or not job.result_path:
        raise HTTPException(status_code=404, detail="Result not found")

    result_path = Path(job.result_path)
    if not result_path.exists():
        raise HTTPException(status_code=404, detail="File missing")

    mime, _ = guess_type(str(result_path))
    if not mime:
        mime = "application/octet-stream"

    return FileResponse(
        path=str(result_path),
        filename=result_path.name,
        media_type=mime
    )
