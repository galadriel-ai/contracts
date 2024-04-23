import pytest

from src.entities import Chat
from src.entities import PromptType
from src.entities import GroqConfig
from src.domain.llm import generate_response_use_case

MESSAGES = [{"role": "user", "content": "Hello"}]


async def _get_config(model: str) -> GroqConfig:
    return GroqConfig(
        model=model,
        frequency_penalty=0.0,
        logit_bias=None,
        max_tokens=100,
        presence_penalty=0.0,
        response_format=None,
        seed=None,
        stop=None,
        temperature=0.0,
        top_p=1.0,
        user=None,
    )


async def _get_chat(model: str) -> Chat:
    return Chat(
        id="1",
        callback_id="1",
        is_processed=False,
        prompt_type=PromptType.GROQ.value,
        messages=MESSAGES,
        config=await _get_config(model),
    )


@pytest.mark.asyncio
async def test_mixtral():
    chat = await _get_chat("mixtral-8x7b-32768")
    result = await generate_response_use_case._generate_groq_with_params(chat)
    assert "hello" in result.choices[0].message.content.lower()


@pytest.mark.asyncio
async def test_llama3_8b():
    chat = await _get_chat("llama3-8b-8192")
    result = await generate_response_use_case._generate_groq_with_params(chat)
    assert "hello" in result.choices[0].message.content.lower()


@pytest.mark.asyncio
async def test_gemma_7b_it():
    chat = await _get_chat("gemma-7b-it")
    result = await generate_response_use_case._generate_groq_with_params(chat)
    assert "hello" in result.choices[0].message.content.lower()

@pytest.mark.asyncio
async def test_llama3_70b():
    chat = await _get_chat("llama3-70b-8192")
    result = await generate_response_use_case._generate_groq_with_params(chat)
    assert "hello" in result.choices[0].message.content.lower()
