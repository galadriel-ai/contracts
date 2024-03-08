import asyncio
from src.repositories.oracle_repository import OracleRepository
from src.domain.llm import generate_response_use_case

repository = OracleRepository()


async def _answer_unanswered_prompts():
    prompts = await repository.get_unanswered_prompts()
    for prompt in prompts:
        try:
            response = await generate_response_use_case(
                "gpt-4-turbo-preview", prompt.prompt
            )
            if response:
                prompt.response = response
                await repository.send_response(prompt, response)
        except Exception as ex:
            print(f"Failed to answer prompt {prompt.id}, exc: {ex}")


async def _listen():
    while True:
        try:
            await _answer_unanswered_prompts()
        except Exception as exc:
            print("Failed to index chain, exc:", exc)
        await asyncio.sleep(2)
        print(f"Calls made: {repository.calls_made}")


async def main():
   await  _listen()


if __name__ == "__main__":
    asyncio.run(main())
