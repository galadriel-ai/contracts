import pytest

from src.entities import Chat
from src.entities import PromptType
from src.entities import OpenAiConfig
from src.domain.llm import generate_response_use_case

MESSAGES = [{"role": "user", "content": "Just say Hello"}]


async def _get_config(model: str) -> OpenAiConfig:
    return OpenAiConfig(
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
        tools=None,
        tool_choice=None,
    )


async def _get_chat(model: str) -> Chat:
    return Chat(
        id="1",
        callback_id="1",
        is_processed=False,
        prompt_type=PromptType.OPENAI.value,
        messages=MESSAGES,
        config=await _get_config(model),
    )


@pytest.mark.asyncio
async def test_gpt_3_5_turbo():
    chat = await _get_chat("gpt-3.5-turbo-1106")
    result = await generate_response_use_case._generate_openai_with_params(chat)
    assert result is not None
    assert "hello" in result.choices[0].message.content.lower()


@pytest.mark.asyncio
async def test_gpt_4_turbo():
    chat = await _get_chat("gpt-4-turbo-preview")
    result = await generate_response_use_case._generate_openai_with_params(chat)
    assert result is not None
    assert "hello" in result.choices[0].message.content.lower()
