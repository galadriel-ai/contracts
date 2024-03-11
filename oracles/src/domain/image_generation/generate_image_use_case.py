import settings
from typing import Optional
from openai import AsyncOpenAI
from src.domain.image_generation.entities import ImageGenerationResult


async def _generate_image(prompt: str) -> Optional[ImageGenerationResult]:
    client = AsyncOpenAI(
        api_key=settings.OPEN_AI_API_KEY,
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
            prompt=response.data[0].revised_prompt,
            url=response.data[0].url,
        )
    except Exception as exc:
        print(f"Image Generation Exception: {exc}", flush=True)


if __name__ == "__main__":
    import asyncio

    print(asyncio.run(execute("Dead horse in the middle of the road")))
