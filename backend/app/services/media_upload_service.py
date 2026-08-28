"""
Disk storage for reference media an instructor attaches to an assignment
(a photo of correct handshape, or a short demo video) — the platform's
first user-uploaded binary file, so this is also where the upload
constraints live: a fixed allowlist of real image/video content types
(never trusting the client-supplied filename) and a size cap, so a bad
upload fails loudly and predictably instead of silently accepting
anything or filling the disk.

Files are named by a fresh UUID, never the client's original filename —
avoids path-traversal from a crafted filename and avoids collisions
without needing to touch the DB first.
"""

import uuid
from pathlib import Path
from typing import Optional

from fastapi import UploadFile

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "uploads" / "assignments"

MAX_MEDIA_BYTES = 20 * 1024 * 1024  # 20MB

CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": ("image", ".jpg"),
    "image/png": ("image", ".png"),
    "image/gif": ("image", ".gif"),
    "image/webp": ("image", ".webp"),
    "video/mp4": ("video", ".mp4"),
    "video/webm": ("video", ".webm"),
    "video/quicktime": ("video", ".mov"),
}


class UnsupportedMedia(ValueError):
    pass


def save_assignment_media(upload_file: UploadFile, data: bytes) -> tuple[str, str]:
    """
    Validates and writes an uploaded reference file to disk. Returns
    (relative_path, media_type) — relative_path is what gets stored on
    the assignment row and turned into a /media/... URL; media_type is
    "image" or "video", used by the frontend to pick <img> vs <video>.
    """
    if len(data) > MAX_MEDIA_BYTES:
        raise UnsupportedMedia(
            f"File is too large ({len(data) / 1_000_000:.1f}MB) — the limit is {MAX_MEDIA_BYTES // 1_000_000}MB."
        )

    content_type = (upload_file.content_type or "").lower()
    if content_type not in CONTENT_TYPE_EXTENSIONS:
        raise UnsupportedMedia(
            f"Unsupported file type: {content_type or 'unknown'}. "
            f"Supported types: {', '.join(sorted(CONTENT_TYPE_EXTENSIONS))}."
        )

    media_type, extension = CONTENT_TYPE_EXTENSIONS[content_type]

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}{extension}"
    (UPLOAD_DIR / filename).write_bytes(data)

    return f"assignments/{filename}", media_type


def delete_assignment_media(relative_path: Optional[str]) -> None:
    """Best-effort cleanup — a missing file (already gone, or a bad path)
    is not an error here, since the caller's real intent (removing the
    assignment row) should never fail because of stale disk state."""
    if not relative_path:
        return
    upload_root = UPLOAD_DIR.parent
    target = (upload_root / relative_path).resolve()
    if upload_root.resolve() not in target.parents:
        return  # refuse to delete anything outside the upload root
    target.unlink(missing_ok=True)
