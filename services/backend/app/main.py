from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path
import uuid

app = FastAPI(title="ChangeAnyFile API")

# Allow frontend dev origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev only; lock down in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent  # services/backend
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_MIME = {
    "image/png",
    "image/jpeg",
    "image/webp",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain"
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_MIME:
        # allow all for now, but warn (you can restrict later)
        # return HTTPException(status_code=400, detail="File type not allowed")
        pass

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")

    # create unique file id & save
    file_id = str(uuid.uuid4())
    filename = f"{file_id}--{file.filename}"
    dest_path = UPLOAD_DIR / filename
    with open(dest_path, "wb") as f:
        f.write(contents)

    return {
        "fileId": file_id,
        "originalName": file.filename,
        "savedName": filename,
        "size": len(contents),
        "contentType": file.content_type,
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
