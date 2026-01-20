import json
import shutil
import time
from pathlib import Path

from PIL import Image
from sqlmodel import select

from .db import get_session
from .models import Job

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
PROCESSED_DIR = BASE_DIR / "processed"

UPLOAD_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)


def process_image_with_actions(src: Path, dest_base: Path, actions: dict) -> Path:
    with Image.open(src) as img:
        img = img.convert("RGB")

        # Resize
        resize = actions.get("resize")
        if resize:
            w = resize.get("width")
            h = resize.get("height")
            if w and h:
                img.thumbnail((w, h), Image.LANCZOS)

        # Format
        pil_format = "JPEG"
        ext = src.suffix.lower()

        convert = actions.get("convert")
        if convert:
            fmt = convert.get("format")
            if fmt == "webp":
                pil_format = "WEBP"
                ext = ".webp"
            elif fmt == "png":
                pil_format = "PNG"
                ext = ".png"
            elif fmt == "jpeg":
                pil_format = "JPEG"
                ext = ".jpg"

        # Compression
        quality = 80
        compression = actions.get("compression")
        if compression and "quality" in compression:
            quality = int(compression["quality"])

        final_path = dest_base.with_suffix(ext)

        save_args = {"optimize": True}
        if pil_format in ("JPEG", "WEBP"):
            save_args["quality"] = quality

        img.save(final_path, format=pil_format, **save_args)
        return final_path


def process_job_async(job_id: str):
    session = get_session()

    job = session.exec(
        select(Job).where(Job.job_id == job_id)
    ).first()

    if not job:
        session.close()
        return

    job.status = "processing"
    session.add(job)
    session.commit()

    try:
        src = UPLOAD_DIR / job.file_id
        dest_base = PROCESSED_DIR / f"{job.file_id}-processed"

        is_image = src.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
        final_path = None

        if is_image:
            actions = json.loads(job.actions_json) if job.actions_json else {}
            final_path = process_image_with_actions(src, dest_base, actions)
        else:
            final_path = dest_base.with_suffix(src.suffix)
            shutil.copy2(src, final_path)

        job.result_filename = final_path.name
        job.result_path = str(final_path)
        job.result_size = final_path.stat().st_size
        job.status = "completed"
        job.updated_at = int(time.time())

    except Exception as e:
        print(f"Worker failed: {e}")
        job.status = "failed"
        job.updated_at = int(time.time())

    finally:
        session.add(job)
        session.commit()
        session.close()
