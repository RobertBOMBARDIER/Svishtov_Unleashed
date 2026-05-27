"""
Photo storage service.

Responsibilities
----------------
- Validate that an uploaded file is a genuine JPEG or PNG image (using Pillow).
- Save the original file to ``<STORAGE_PATH>/<uuid>.<ext>``.
- Generate a thumbnail (max 300×300 px, aspect-ratio preserved) and save it
  to ``<STORAGE_PATH>/thumbnails/<uuid>_thumb.<ext>``.
- Return the relative URL paths that are stored in the database.

Storage layout (Railway Persistent Volume mounted at /data/photos by default)
------------------------------------------------------------------------------
  /data/photos/
      <uuid>.jpg          ← original
      thumbnails/
          <uuid>_thumb.jpg ← thumbnail (max 300×300)

The ``STORAGE_PATH`` setting can be overridden via the environment variable of
the same name (see app/core/config.py).
"""

import io
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

from app.core.config import settings

# ── Constants ─────────────────────────────────────────────────────────────────

ALLOWED_FORMATS = {"JPEG", "PNG"}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}
THUMBNAIL_MAX_SIZE = (300, 300)

# Maximum upload size: 10 MB (Requirement 3.8)
MAX_FILE_BYTES = 10 * 1024 * 1024


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_storage_root() -> Path:
    """Return the root storage directory, creating it if necessary."""
    root = Path(settings.STORAGE_PATH)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _get_thumbnails_dir() -> Path:
    """Return the thumbnails sub-directory, creating it if necessary."""
    thumbs = _get_storage_root() / "thumbnails"
    thumbs.mkdir(parents=True, exist_ok=True)
    return thumbs


def _ext_for_format(fmt: str) -> str:
    """Return the file extension for a Pillow format string."""
    return "jpg" if fmt == "JPEG" else "png"


# ── Public API ────────────────────────────────────────────────────────────────

async def save_photo(upload: UploadFile) -> tuple[str, str]:
    """
    Validate, save, and thumbnail an uploaded photo.

    Parameters
    ----------
    upload:
        The ``UploadFile`` received from the multipart/form-data request.

    Returns
    -------
    (image_url, thumbnail_url)
        Relative URL paths (e.g. ``/static/photos/abc.jpg``) suitable for
        storing in the database and serving to clients.

    Raises
    ------
    HTTPException 400
        If the file is not a valid JPEG or PNG, or exceeds 10 MB.
    """
    # ── Read raw bytes ────────────────────────────────────────────────────────
    raw = await upload.read()

    if len(raw) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Dimensiunea fișierului depășește limita de "
                f"{MAX_FILE_BYTES // (1024 * 1024)} MB."
            ),
        )

    # ── Validate with Pillow ──────────────────────────────────────────────────
    try:
        img = Image.open(io.BytesIO(raw))
        img.verify()  # raises if the file is corrupt / not a valid image
    except (UnidentifiedImageError, Exception) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fișierul nu este o imagine validă.",
        ) from exc

    # Re-open after verify() (Pillow closes the stream after verify)
    img = Image.open(io.BytesIO(raw))

    if img.format not in ALLOWED_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Format neacceptat: {img.format!r}. "
                "Sunt acceptate doar JPEG și PNG."
            ),
        )

    # ── Determine paths ───────────────────────────────────────────────────────
    file_id = str(uuid.uuid4())
    ext = _ext_for_format(img.format)
    pillow_format = img.format  # "JPEG" or "PNG"

    storage_root = _get_storage_root()
    thumbs_dir = _get_thumbnails_dir()

    original_filename = f"{file_id}.{ext}"
    thumb_filename = f"{file_id}_thumb.{ext}"

    original_path = storage_root / original_filename
    thumb_path = thumbs_dir / thumb_filename

    # ── Save original ─────────────────────────────────────────────────────────
    # Convert to RGB for JPEG (PNG can be RGBA)
    save_img = img
    if pillow_format == "JPEG" and img.mode not in ("RGB", "L"):
        save_img = img.convert("RGB")

    save_img.save(str(original_path), format=pillow_format)

    # ── Generate thumbnail ────────────────────────────────────────────────────
    thumb_img = img.copy()
    if pillow_format == "JPEG" and thumb_img.mode not in ("RGB", "L"):
        thumb_img = thumb_img.convert("RGB")

    thumb_img.thumbnail(THUMBNAIL_MAX_SIZE, Image.LANCZOS)
    thumb_img.save(str(thumb_path), format=pillow_format)

    # ── Build URL paths ───────────────────────────────────────────────────────
    image_url = f"/static/photos/{original_filename}"
    thumbnail_url = f"/static/photos/thumbnails/{thumb_filename}"

    return image_url, thumbnail_url


def delete_photo_files(image_url: str, thumbnail_url: str) -> None:
    """
    Remove the physical files for a photo from the storage volume.

    Silently ignores missing files (idempotent).

    Parameters
    ----------
    image_url:
        The ``image_url`` value stored in the database (e.g. ``/static/photos/abc.jpg``).
    thumbnail_url:
        The ``thumbnail_url`` value stored in the database.
    """
    storage_root = _get_storage_root()

    # Strip the /static/photos/ prefix to get the filename
    for url, base_dir in [
        (image_url, storage_root),
        (thumbnail_url, storage_root),
    ]:
        # Normalise: remove leading /static/photos/ or /static/photos/thumbnails/
        relative = url.lstrip("/")
        # Remove "static/photos/" prefix
        if relative.startswith("static/photos/thumbnails/"):
            filename = relative[len("static/photos/thumbnails/"):]
            file_path = storage_root / "thumbnails" / filename
        elif relative.startswith("static/photos/"):
            filename = relative[len("static/photos/"):]
            file_path = storage_root / filename
        else:
            # Fallback: treat as absolute path
            file_path = Path(url)

        try:
            file_path.unlink(missing_ok=True)
        except OSError:
            pass  # Best-effort deletion
