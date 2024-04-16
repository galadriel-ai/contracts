import backoff
import settings
from typing import Optional
import httpx
import openai
from openai import AsyncOpenAI
from src.domain.tools.image_generation.entities import ImageGenerationResult

TIMEOUT = httpx.Timeout(timeout=600.0, connect=10.0)


@backoff.on_exception(
    backoff.expo, (openai.RateLimitError, openai.APITimeoutError), max_tries=3
)
async def _generate_image(prompt: str) -> Optional[ImageGenerationResult]:
    client = AsyncOpenAI(
        api_key=settings.OPEN_AI_API_KEY,
        timeout=TIMEOUT,
    )

    return await client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )


async def execute(prompt: str) -> Optional[ImageGenerationResult]:
    try:
        response = await _generate_image(prompt)
        return ImageGenerationResult(
            url=response.data[0].url,
            error="",
        )
    except openai.APIError as api_error:
        print(f"OpenAI API error: {api_error}", flush=True)
        return ImageGenerationResult(
            url="",
            error=api_error.message,
        )
    except Exception as e:
        print(f"Image generation error: {e}", flush=True)
        return ImageGenerationResult(
            url="",
            error=str(e),
        )


if __name__ == "__main__":
    import asyncio

    print(asyncio.run(execute("Dead horse in the middle of the road")))
