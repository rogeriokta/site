import os
import uuid
import aiofiles
from pathlib import Path

from app.config import get_settings

settings = get_settings()


async def save_upload(
    file_bytes: bytes,
    original_filename: str,
    subdir: str = "uploads",
) -> str:
    ext = Path(original_filename).suffix or ".jpg"
    filename = f"{uuid.uuid4()}{ext}"
    dir_path = Path(subdir)
    dir_path.mkdir(parents=True, exist_ok=True)
    filepath = dir_path / filename

    async with aiofiles.open(str(filepath), "wb") as f:
        await f.write(file_bytes)

    return str(filepath)


async def save_processed(
    image_bytes: bytes,
    correction_id: str,
    subdir: str = "processed",
) -> str:
    filename = f"{correction_id}.jpg"
    dir_path = Path(subdir)
    dir_path.mkdir(parents=True, exist_ok=True)
    filepath = dir_path / filename

    async with aiofiles.open(str(filepath), "wb") as f:
        await f.write(image_bytes)

    return str(filepath)


def get_file_url(filepath: str) -> str:
    if not filepath:
        return ""
    path = Path(filepath)
    filename = path.name
    parent = path.parent.name
    return f"/{parent}/{filename}"


def cleanup_file(filepath: str):
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
    except OSError:
        pass
