import asyncio

import settings
from groq import AsyncGroq


async def main():
    client = AsyncGroq(
        api_key=settings.GROQ_API_KEY,
    )
    models = [
        "llama3-8b-8192",
        "llama3-70b-8192",
        "mixtral-8x7b-32768",
        "gemma-7b-it",
    ]
    chat_completion = await client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Explain the importance of low latency LLMs",
            }
        ],
        model=models[2],
        response_format={"type": "text"}
    )
    print(chat_completion.choices[0].message.content)


if __name__ == '__main__':
    asyncio.run(main())
