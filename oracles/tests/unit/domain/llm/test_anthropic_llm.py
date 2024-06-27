from unittest.mock import MagicMock
from anthropic import NOT_GIVEN

from src.domain.llm import anthropic_llm
from src.entities import Chat
from src.entities import LlmConfig


def test_convert_output_to_chat_completion():
    chat = Chat(
        id="mock-id",
        callback_id=0,
        is_processed=False,
        prompt_type="default",
        messages=[{"role": "user", "content": "Hello, how are you?"}],
        config=LlmConfig(
            max_tokens=50,
            model="test-model",
            stop=None,
            temperature=0.7,
            tool_choice=None,
            tools=[],
            frequency_penalty=0.0,
            logit_bias=None,
            presence_penalty=0.0,
            response_format=None,
            seed=None,
            top_p=None,
            user="test-user",
        ),
    )

    message = MagicMock()
    message.content = [
        MagicMock(type="text", text="I'm fine, thank you!"),
        MagicMock(
            id="mock-id", type="tool_use", name="fetchData", input={"param": "value"}
        ),
    ]
    message.content[1].name = "fetchData"
    message.stop_reason = "end_turn"
    message.id = "mock-id"
    message.usage = MagicMock(input_tokens=5, output_tokens=5)

    chat_completion = anthropic_llm._convert_output_to_chat_completion(chat, message)

    assert chat_completion.id == "mock-id"
    assert chat_completion.model == "test-model"
    assert chat_completion.object == "chat.completion"
    assert chat_completion.choices[0].message.content == "I'm fine, thank you!"
    assert chat_completion.choices[0].finish_reason == "stop"
    assert chat_completion.usage.total_tokens == 10

    tool_calls = chat_completion.choices[0].message.tool_calls
    assert tool_calls[0].function.name == "fetchData"
    assert tool_calls[0].function.arguments == '{"param": "value"}'


def test_convert_tool_definitions():
    tools = [
        {
            "function": {
                "name": "fetchData",
                "description": "Fetches data",
                "parameters": "{}",
            }
        }
    ]
    expected_output = [
        {"name": "fetchData", "description": "Fetches data", "input_schema": "{}"}
    ]
    assert anthropic_llm._convert_tool_definitions(tools) == expected_output
    assert anthropic_llm._convert_tool_definitions(None) == NOT_GIVEN


def test_convert_tool_calls():
    message = MagicMock()
    message.content = [
        MagicMock(),
        MagicMock(
            id="mock-id", type="tool_use", name="fetchData", input={"param": "value"}
        ),
    ]
    message.content[1].name = "fetchData"
    tool_calls = anthropic_llm._convert_tool_calls(message)
    assert tool_calls[0].function.name == "fetchData"
    assert tool_calls[0].function.arguments == '{"param": "value"}'


def test_convert_finish_reason():
    assert anthropic_llm._convert_finish_reason("end_turn") == "stop"
    assert anthropic_llm._convert_finish_reason("max_tokens") == "length"
    assert anthropic_llm._convert_finish_reason("stop_sequence") == "stop"
    assert anthropic_llm._convert_finish_reason("tool_use") == "tool_calls"
    assert anthropic_llm._convert_finish_reason("unknown_reason") == "stop"
