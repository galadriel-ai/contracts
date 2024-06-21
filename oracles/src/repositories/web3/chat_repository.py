import json
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import get_args

from groq.types.chat import ChatCompletion as GroqChatCompletion
from openai.types.chat import ChatCompletion
from openai.types.chat import ChatCompletionToolParam
from pydantic import TypeAdapter
from web3.exceptions import ContractLogicError

import settings
from src.entities import ALLOWED_FUNCTION_NAMES
from src.entities import Chat
from src.entities import GroqConfig
from src.entities import GroqModelType
from src.entities import OpenAiConfig
from src.entities import OpenAiModelType
from src.entities import OpenaiToolChoiceType
from src.entities import PromptType
from src.repositories.web3.base import Web3BaseRepository


class Web3ChatRepository(Web3BaseRepository):
    def __init__(self) -> None:
        super().__init__()
        self.last_chats_count = 0
        self.indexed_chats = []
        self.metrics.update(
            {
                "chats_count": 0,
                "chats_read": 0,
                "chats_answered": 0,
                "chats_configuration_errors": 0,
                "chats_history_read_errors": 0,
                "chats_write_errors": 0,
                "chats_marked_as_done": 0,
            }
        )

    async def _get_chat(self, i: int) -> Optional[Chat]:
        config = None
        callback_id = await self.oracle_contract.functions.promptCallbackIds(i).call()

        try:
            prompt_type = await self._get_prompt_type(i)
            is_prompt_processed = (
                await self.oracle_contract.functions.isPromptProcessed(i).call()
            )
            gpt_vision_support = False
            if prompt_type == PromptType.OPENAI:
                config = await self._get_openai_config(i)
                gpt_vision_support = (
                    config.model == "gpt-4-turbo" or config.model == "gpt-4o"
                )
            elif prompt_type == PromptType.GROQ:
                config = await self._get_groq_config(i)
        except Exception as e:
            print(f"Error getting chat {i} configuration: {e}", flush=True)
            self.metrics["chats_configuration_errors"] += 1
            return None

        messages = []
        try:
            if gpt_vision_support:
                history = await self.oracle_contract.functions.getMessagesAndRoles(
                    i, callback_id
                ).call()
                messages = await self._format_history(history)
            else:
                contents = await self.oracle_contract.functions.getMessages(
                    i, callback_id
                ).call()
                roles = await self.oracle_contract.functions.getRoles(
                    i, callback_id
                ).call()
                for j in range(len(contents)):
                    messages.append(
                        {
                            "role": roles[j],
                            "content": contents[j],
                        }
                    )
        except Exception as e:
            print(f"Error getting chat {i} history: {e}", flush=True)
            self.metrics["chats_history_read_errors"] += 1
            return None

        return Chat(
            id=i,
            messages=messages,
            callback_id=callback_id,
            is_processed=is_prompt_processed,
            prompt_type=prompt_type,
            config=config,
        )

    async def _index_new_chats(self):
        chats_count = await self.oracle_contract.functions.promptsCount().call()
        self.metrics["chats_count"] = chats_count
        if not self.last_chats_count and chats_count > 0:
            self.last_chats_count = await self._find_first_unprocessed(
                chats_count,
                lambda index: self.oracle_contract.functions.isPromptProcessed(
                    index
                ).call(),
            )
            self.metrics["chats_marked_as_done"] = self.last_chats_count
            print(
                f"Found first unprocessed chat {self.last_chats_count} on cold start, marking all previous as processed",
                flush=True,
            )
        if chats_count > self.last_chats_count:
            print(
                f"Indexing new prompts from {self.last_chats_count} to {chats_count}",
                flush=True,
            )
            for i in range(self.last_chats_count, chats_count):
                chat = await self._get_chat(i)
                if chat:
                    self.indexed_chats.append(chat)
                    self.metrics["chats_read"] += 1
                    if chat.is_processed:
                        self.metrics["chats_marked_as_done"] += 1
                self.last_chats_count = i + 1

    async def get_unanswered_chats(self) -> List[Chat]:
        await self._index_new_chats()
        unanswered_chats = [
            chat for chat in self.indexed_chats if not chat.is_processed
        ]
        return unanswered_chats

    async def send_chat_response(self, chat: Chat) -> bool:
        try:
            tx = await self._build_response_tx(chat)
        except Exception as e:
            chat.is_processed = True
            chat.transaction_receipt = {"error": str(e)}
            self.metrics["chats_write_errors"] += 1
            await self.mark_as_done(chat)
            return False
        tx_receipt = await self._sign_and_send_tx(tx)
        chat.transaction_receipt = tx_receipt
        chat.is_processed = bool(tx_receipt.get("status"))
        if chat.is_processed:
            self.metrics["chats_answered"] += 1
            self.metrics["chats_marked_as_done"] += 1
        else:
            self.metrics["chats_write_errors"] += 1
        return bool(tx_receipt.get("status"))

    async def mark_as_done(self, chat: Chat):
        nonce = await self.web3_client.eth.get_transaction_count(self.account.address)
        tx_data = {
            "from": self.account.address,
            "nonce": nonce,
            # TODO: pick gas amount in a better way
            # "gas": 1000000,
            "maxFeePerGas": self.web3_client.to_wei("2", "gwei"),
            "maxPriorityFeePerGas": self.web3_client.to_wei("1", "gwei"),
        }
        if chain_id := settings.CHAIN_ID:
            tx_data["chainId"] = int(chain_id)

        if chat.prompt_type == PromptType.OPENAI:
            tx = await self.oracle_contract.functions.markOpenAiPromptAsProcessed(
                chat.id,
            ).build_transaction(tx_data)
        elif chat.prompt_type == PromptType.GROQ:
            tx = await self.oracle_contract.functions.markGroqPromptAsProcessed(
                chat.id,
            ).build_transaction(tx_data)
        else:
            tx = await self.oracle_contract.functions.markPromptAsProcessed(
                chat.id,
            ).build_transaction(tx_data)
        tx_receipt = await self._sign_and_send_tx(tx)
        if bool(tx_receipt.get("status")):
            self.metrics["chats_marked_as_done"] += 1
        return tx_receipt

    async def _build_response_tx(self, chat: Chat):
        nonce = await self.web3_client.eth.get_transaction_count(self.account.address)
        tx_data = {
            "from": self.account.address,
            "nonce": nonce,
            # TODO: pick gas amount in a better way
            # "gas": 1000000,
            "maxFeePerGas": self.web3_client.to_wei("2", "gwei"),
            "maxPriorityFeePerGas": self.web3_client.to_wei("1", "gwei"),
        }
        if chain_id := settings.CHAIN_ID:
            tx_data["chainId"] = int(chain_id)
        if chat.prompt_type == PromptType.OPENAI:
            tx = await self.oracle_contract.functions.addOpenAiResponse(
                chat.id,
                chat.callback_id,
                _format_openai_response(chat.response),
                chat.error_message,
            ).build_transaction(tx_data)
        elif chat.prompt_type == PromptType.GROQ:
            tx = await self.oracle_contract.functions.addGroqResponse(
                chat.id,
                chat.callback_id,
                _format_groq_response(chat.response),
                chat.error_message,
            ).build_transaction(tx_data)
        # Eventually more options here
        else:
            tx = await self.oracle_contract.functions.addResponse(
                chat.id,
                chat.callback_id,
                chat.response,
                chat.error_message,
            ).build_transaction(tx_data)
        return tx

    async def _get_openai_config(self, i: int) -> Optional[OpenAiConfig]:
        config = await self.oracle_contract.functions.openAiConfigurations(i).call()
        if not config or not config[0] or not config[0] in get_args(OpenAiModelType):
            return None
        try:
            return OpenAiConfig(
                model=config[0],
                frequency_penalty=_parse_float_from_int(config[1], -20, 20),
                logit_bias=_parse_json_string(config[2]),
                # Check max value?
                max_tokens=_value_or_none(config[3]),
                presence_penalty=_parse_float_from_int(config[4], -20, 20),
                response_format=_get_response_format(config[5]),
                seed=_value_or_none(config[6]),
                stop=_value_or_none(config[7]),
                temperature=_parse_float_from_int(config[8], 0, 20),
                top_p=_parse_float_from_int(config[9], 0, 100, decimals=2),
                tools=_parse_tools(config[10]),
                tool_choice=(
                    config[11]
                    if (config[11] and config[11] in get_args(OpenaiToolChoiceType))
                    else None
                ),
                user=_value_or_none(config[12]),
            )
        except:
            return None

    async def _get_groq_config(self, i: int) -> Optional[GroqConfig]:
        config = await self.oracle_contract.functions.groqConfigurations(i).call()
        if not config or not config[0] or not config[0] in get_args(GroqModelType):
            return None
        try:
            return GroqConfig(
                model=config[0],
                frequency_penalty=_parse_float_from_int(config[1], -20, 20),
                logit_bias=_parse_json_string(config[2]),
                # Check max value?
                max_tokens=_value_or_none(config[3]),
                presence_penalty=_parse_float_from_int(config[4], -20, 20),
                response_format=_get_response_format(config[5]),
                seed=_value_or_none(config[6]),
                stop=_value_or_none(config[7]),
                temperature=_parse_float_from_int(config[8], 0, 20),
                top_p=_parse_float_from_int(config[9], 0, 100, decimals=2),
                tools=_parse_tools(config[10]),
                tool_choice=(
                    config[11]
                    if (config[11] and config[11] in get_args(OpenaiToolChoiceType))
                    else None
                ),
                user=_value_or_none(config[12]),
            )
        except:
            return None

    async def _get_prompt_type(self, i) -> PromptType:
        prompt_type: Optional[str] = await self.oracle_contract.functions.promptType(
            i
        ).call()
        if not prompt_type:
            return PromptType.DEFAULT
        try:
            return PromptType(prompt_type)
        except:
            return PromptType.DEFAULT

    async def _format_history(self, history: List[str]) -> List[Dict]:
        formatted_history = []
        for entry in history:
            content = []
            for c in entry[1]:
                if c[0] == "text":
                    content.append(
                        {
                            "type": "text",
                            "text": c[1],
                        }
                    )
                elif c[0] == "image_url":
                    content.append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": c[1],
                            },
                        },
                    )
            message = {
                "role": entry[0],
                "content": content,
            }
            formatted_history.append(message)
        return formatted_history


def _value_or_none(value: Any) -> Optional[Any]:
    return value if value else None


def _parse_float_from_int(
    value: Optional[float], min_value: int, max_value: int, decimals: int = 1
) -> Optional[int]:
    return (
        round(value / (10**decimals), 1) if (min_value <= value <= max_value) else None
    )


def _parse_json_string(value: Optional[str]) -> Optional[Dict]:
    if not value:
        return None
    try:
        return json.loads(value)
    except:
        return None


def _get_response_format(value: Optional[str]):
    parsed = _parse_json_string(value)
    if parsed and (parsed.get("type") or "") in ["text", "json_object"]:
        return parsed
    return None


def _format_openai_response(completion: Optional[ChatCompletion]) -> Dict:
    if not completion:
        return {
            "id": "",
            "content": "",
            "functionName": "",
            "functionArguments": "",
            "created": 0,
            "model": "",
            "systemFingerprint": "",
            "object": "",
            "completionTokens": 0,
            "promptTokens": 0,
            "totalTokens": 0,
        }
    choice = completion.choices[0].message
    return {
        "id": completion.id,
        "content": choice.content if choice.content else "",
        "functionName": choice.tool_calls[0].function.name if choice.tool_calls else "",
        "functionArguments": (
            choice.tool_calls[0].function.arguments if choice.tool_calls else ""
        ),
        "created": completion.created,
        "model": completion.model,
        "systemFingerprint": completion.system_fingerprint or "",
        "object": completion.object,
        "completionTokens": completion.usage.completion_tokens,
        "promptTokens": completion.usage.prompt_tokens,
        "totalTokens": completion.usage.total_tokens,
    }


def _format_groq_response(completion: Optional[GroqChatCompletion]) -> Dict:
    if not completion:
        return {
            "id": "",
            "content": "",
            "functionName": "",
            "functionArguments": "",
            "created": 0,
            "model": "",
            "systemFingerprint": "",
            "object": "",
            "completionTokens": 0,
            "promptTokens": 0,
            "totalTokens": 0,
        }
    choice = completion.choices[0].message
    return {
        "id": completion.id,
        "content": choice.content if choice.content else "",
        "functionName": choice.tool_calls[0].function.name if choice.tool_calls else "",
        "functionArguments": (
            choice.tool_calls[0].function.arguments if choice.tool_calls else ""
        ),
        "created": completion.created,
        "model": completion.model,
        "systemFingerprint": completion.system_fingerprint or "",
        "object": completion.object,
        "completionTokens": completion.usage.completion_tokens,
        "promptTokens": completion.usage.prompt_tokens,
        "totalTokens": completion.usage.total_tokens,
    }


def _parse_tools(value: str) -> Optional[List[ChatCompletionToolParam]]:
    if not value:
        return None
    try:
        tools = []
        parsed = json.loads(value)
        dict_validator = TypeAdapter(ChatCompletionToolParam)
        [tools.append(dict_validator.validate_python(p)) for p in parsed]
        filtered_tools: List[ChatCompletionToolParam] = []
        for tool in tools:
            if tool["function"]["name"] in ALLOWED_FUNCTION_NAMES:
                filtered_tools.append(tool)
        return filtered_tools
    except:
        return None
