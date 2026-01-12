import asyncio
import time
import shutil
from pathlib import Path

from sqlmodel import select
from PIL import Image

from .db import get_session
from .models import Job, JobLog
from .config import UPLOAD_DIR, PROCESSED_DIR
import re
from typing import Optional, Tuple

def detect_target_format(prompt: str, original_suffix: str) -> str:
    p = (prompt or "").lower()

    if "webp" in p:
        return "WEBP"
    if "png" in p:
        return "PNG"
    if "jpg" in p or "jpeg" in p:
        return "JPEG"

    # 🔑 IMPORTANT CHANGE:
    # If user did NOT ask for conversion → keep original format
    ext = original_suffix.lower()
    if ext in [".jpg", ".jpeg"]:
        return "JPEG"
    if ext == ".png":
        return "PNG"
    if ext == ".webp":
        return "WEBP"

    # Absolute fallback (rare)
    return "JPEG"

def extract_resize_from_prompt(prompt: str) -> Optional[Tuple[int, int]]:
    """
    Extract resize instructions from prompt.
    Supports:
    - 30x30
    - resize to 300x300
    - passport size
    """
    if not prompt:
        return None

    p = prompt.lower()

    # Passport size (India standard)
    if "passport" in p:
        return (413, 531)

    # Match 30x30, 300x300, etc.
    match = re.search(r"(\d{2,4})\s*[xX]\s*(\d{2,4})", p)
    if match:
        return (int(match.group(1)), int(match.group(2)))

    return None

def process_image(src: Path, dest: Path, prompt: str) -> Path:
    with Image.open(src) as img:
        img = img.convert("RGB")

        # --- resize logic ---
        target_size = extract_resize_from_prompt(prompt)
        if target_size:
            # Maintain aspect ratio, fit inside target box
            img.thumbnail(target_size, Image.LANCZOS)

        # --- format detection ---
        fmt = detect_target_format(prompt, src.suffix)

        if fmt == "WEBP":
            dest = dest.with_suffix(".webp")
        elif fmt == "JPEG":
            dest = dest.with_suffix(".jpg")
        elif fmt == "PNG":
            dest = dest.with_suffix(".png")

        # --- compression logic ---
        p = (prompt or "").lower()
        quality = 80

        if "compress" in p or "small" in p:
            quality = 65
        if "very small" in p:
            quality = 45
        if "high quality" in p:
            quality = 90

        save_args = {
            "optimize": True
        }

        if fmt in ["JPEG", "WEBP"]:
            save_args["quality"] = quality

        dest.parent.mkdir(parents=True, exist_ok=True)
        img.save(dest, format=fmt, **save_args)

        return dest



async def process_job_async(job_id: str):
    session = get_session()

    try:
        job = session.exec(
            select(Job).where(Job.job_id == job_id)
        ).first()

        if not job:
            return

        def log(msg: str):
            session.add(JobLog(job_id=job.job_id, message=msg))
            session.commit()

        job.status = "processing"
        job.updated_at = int(time.time())
        session.add(job)
        session.commit()

        log("Worker started processing")

        files = list(UPLOAD_DIR.glob(f"{job.file_id}--*"))
        if not files:
            log("Uploaded file not found")
            job.status = "failed"
            session.commit()
            return

        src = files[0]
        dest = PROCESSED_DIR / f"{src.stem}-processed{src.suffix}"

        is_image = src.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]

        await asyncio.sleep(0.5)

        if is_image:
            log("Image detected, applying conversion/compression")
            try:
                final_path = process_image(src, dest, job.prompt or "")
                log(f"Image processed: {final_path.name}")
            except Exception as e:
                log(f"Image processing failed, fallback to copy: {e}")
                shutil.copy2(src, dest)
                final_path = dest
        else:
            log("Non-image file, using copy")
            shutil.copy2(src, dest)
            final_path = dest

        await asyncio.sleep(1)

        job.status = "completed"
        job.result_filename = final_path.name
        job.result_path = str(final_path)
        job.result_size = final_path.stat().st_size
        job.updated_at = int(time.time())

        session.add(job)
        session.commit()

        log("Job completed successfully")

    except Exception as e:
        session.add(JobLog(job_id=job_id, message=f"Worker failed: {e}"))
        job.status = "failed"
        session.commit()
    finally:
        session.close()
