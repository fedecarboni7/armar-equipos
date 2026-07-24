import io
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError
from PIL import Image

from app.config.settings import Settings

from app.config.logging_config import logger


_settings = Settings()

_s3_client = None


def get_r2_client():
    global _s3_client
    if _s3_client is None:
        endpoint_url = f"https://{_settings.r2_account_id}.r2.cloudflarestorage.com"
        _s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=_settings.r2_access_key_id,
            aws_secret_access_key=_settings.r2_secret_access_key,
            region_name="auto",
        )
    return _s3_client


MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
TARGET_SIZE = 512
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


def process_player_photo(file_bytes: bytes) -> bytes:
    if len(file_bytes) > MAX_FILE_SIZE:
        raise ValueError("La imagen no puede superar 5MB")

    try:
        img = Image.open(io.BytesIO(file_bytes))
        img.verify()
    except Exception:
        raise ValueError("El archivo no es una imagen válida o está corrupto")

    try:
        img = Image.open(io.BytesIO(file_bytes))
    except Exception:
        raise ValueError("El archivo no es una imagen válida o está corrupto")

    if img.format not in ALLOWED_FORMATS:
        raise ValueError(f"Formato no soportado: {img.format}. Usá JPEG, PNG o WEBP")

    if img.mode in ("RGBA", "LA", "PA"):
        img = img.convert("RGB")
    elif img.mode != "RGB":
        img = img.convert("RGB")

    width, height = img.size
    min_dim = min(width, height)
    left = (width - min_dim) // 2
    top = (height - min_dim) // 2
    img = img.crop((left, top, left + min_dim, top + min_dim))

    img = img.resize((TARGET_SIZE, TARGET_SIZE), Image.LANCZOS)

    buffer = io.BytesIO()
    img.save(buffer, format="WEBP", quality=80)
    return buffer.getvalue()


def upload_player_photo(
    player_type: str, player_id: int, processed_bytes: bytes
) -> str:
    key = f"players/{player_type}/{player_id}/{uuid4()}.webp"
    client = get_r2_client()
    client.put_object(
        Bucket=_settings.r2_bucket_name,
        Key=key,
        Body=processed_bytes,
        ContentType="image/webp",
    )
    return f"{_settings.r2_public_url}/{key}"


def delete_player_photo(photo_url: str) -> None:
    public_url = _settings.r2_public_url
    if photo_url.startswith(public_url):
        key = photo_url[len(public_url) + 1 :]
    else:
        key = photo_url

    try:
        client = get_r2_client()
        client.delete_object(Bucket=_settings.r2_bucket_name, Key=key)
    except ClientError as e:
        logger.warning("Failed to delete photo from R2 (key=%s): %s", key, e)
