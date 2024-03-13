import aiohttp
import json
import settings
from src.domain.search.entities import WebSearchResult


async def execute(query: str) -> WebSearchResult:
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
                result = json.dumps(data["organic"])
                return WebSearchResult(
                    result=result,
                    error="",
                )
    except Exception as e:
        return WebSearchResult(
            result="",
            error=str(e),
        )
