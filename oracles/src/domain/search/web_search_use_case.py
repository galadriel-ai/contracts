import aiohttp
import json
import settings
from typing import Optional


async def execute(query: str) -> Optional[str]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": settings.SERPER_API_KEY,
                    "Content-Type": "application/json",
                },
                json={"q": query},
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return json.dumps(data["organic"])
    except Exception as e:
        print(f"Web search failed: {e}")
    return None
