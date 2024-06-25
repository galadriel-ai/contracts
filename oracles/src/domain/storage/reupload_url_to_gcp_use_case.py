import os
import uuid
import aiohttp
import settings
from typing import Optional
from urllib.parse import urlparse, unquote

from src.domain.storage import upload_to_gcp_use_case
from src.domain.storage.entities import UploadToGCPRequest


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
                request = UploadToGCPRequest(
                    destination=new_image_name,
                    data=image_data,
                    content_type=response.headers["Content-Type"],
                )
                return await upload_to_gcp_use_case.execute(request)


async def _generate_filename(original_filename: str) -> str:
    _, extension = os.path.splitext(original_filename)
    return f"{uuid.uuid4()}{extension}"
