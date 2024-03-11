import os
import uuid
import aiohttp
import settings
from typing import Optional
from google.cloud import storage
from urllib.parse import urlparse, unquote


async def _generate_filename(original_filename: str) -> str:
    _, extension = os.path.splitext(original_filename)
    return f"{uuid.uuid4()}{extension}"


async def execute(download_url: str) -> Optional[str]:
    # don't reupload to GCP if we are in local environment
    if settings.ENVIRONMENT == "local":
        return download_url
    parsed_url = urlparse(download_url)
    original_image_name = unquote(parsed_url.path.split("/")[-1])
    new_image_name = await _generate_filename(original_image_name)

    async with aiohttp.ClientSession() as session:
        async with session.get(download_url) as response:
            if response.status == 200:
                image_data = await response.read()

                storage_client = storage.Client()
                bucket = storage_client.bucket(settings.GCS_BUCKET_NAME)
                blob = bucket.blob(original_image_name)
                blob.upload_from_string(
                    image_data, content_type=response.headers["Content-Type"]
                )
                return f"https://storage.googleapis.com/{settings.GCS_BUCKET_NAME}/{new_image_name}"
