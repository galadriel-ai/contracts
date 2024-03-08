import asyncio
from src.repositories.oracle_repository import OracleRepository
from src.llm import generate_response_use_case

repository = OracleRepository()


async def _answer_unanswered_prompts():
    prompts = repository.get_unanswered_prompts()
    for prompt in prompts:
        try:
            response = await generate_response_use_case(
                "gpt-4-turbo-preview", prompt.prompt
            )
            if response:
                prompt.response = response
                repository.send_response(prompt, response)
        except Exception as ex:
            print(f"Failed to answer prompt {prompt.id}, exc: {ex}")


async def _listen():
    global calls_made
    while True:
        try:
            _answer_unanswered_prompts()
        except Exception as exc:
            print("Failed to index chain, exc:", exc)
        asyncio.sleep(2)
        print(f"Calls made: {calls_made}")


async def main():
   await  _listen()


if __name__ == "__main__":
    asyncio.run(main())
