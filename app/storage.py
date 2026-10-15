"""Profile picture storage on local disk.

For production with multiple servers, replace save/delete with S3, Cloudflare R2
or Google Cloud Storage. The rest of the app only uses these two functions.
"""

import io
import uuid
from pathlib import Path

from PIL import Image, ImageOps

from app.config import settings


Image.MAX_IMAGE_PIXELS = 25_000_000  # reject "decompression bomb" images
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}

AVATAR_DIR = Path(settings.media_dir) / "avatars"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)



class InvalidImageError(ValueError):
    pass



def process_avatar(data: bytes) -> bytes:
    """Validate a real image, fix rotation, crop to a square, and re-encode.

    Re-encoding also strips EXIF metadata such as the GPS location where the
    photo was taken, which protects your users' privacy.
    """
    try:
        Image.open(io.BytesIO(data)).verify()  # checks file integrity
        img = Image.open(io.BytesIO(data))
        if img.format not in ALLOWED_FORMATS:
            raise InvalidImageError("Only JPEG, PNG or WebP images are allowed")
        img = ImageOps.exif_transpose(img)  # respect phone camera rotation
        img = img.convert("RGB")
        size = settings.avatar_size_px
        img = ImageOps.fit(img, (size, size), Image.LANCZOS)
        out = io.BytesIO()
        img.save(out, "WEBP", quality=85)
        return out.getvalue()
    except InvalidImageError:
        raise
    except Exception:
        raise InvalidImageError("File is not a valid image")


def save_avatar(image_bytes: bytes) -> str:
    key = f"{uuid.uuid4().hex}.webp"  # random name: can't be guessed or clash
    (AVATAR_DIR / key).write_bytes(image_bytes)
    return key


def delete_avatar(key: str | None) -> None:
    if key:
        (AVATAR_DIR / key).unlink(missing_ok=True)
