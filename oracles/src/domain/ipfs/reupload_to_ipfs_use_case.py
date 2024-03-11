import aiohttp
import settings
from typing import Optional


async def execute(download_url: str) -> Optional[str]:
    async with aiohttp.ClientSession() as session:
        async with session.get(download_url) as download_response:
            if download_response.status == 200:
                image_data = await download_response.read()
                headers = {
                    "Authorization": f"Bearer {settings.NFT_STORAGE_API_KEY}",
                    "Content-Type": download_response.headers.get(
                        "Content-Type", "application/octet-stream"
                    ),
                }
                async with session.post(
                    "https://api.nft.storage/upload", data=image_data, headers=headers
                ) as upload_response:
                    json_response = await upload_response.json()
                    cid = json_response.get("value").get("cid")
                    if cid:
                        return f"ipfs://{cid}"
