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
from web3 import AsyncWeb3

import settings
from src.entities import ALLOWED_FUNCTION_NAMES
from src.entities import Chat
from src.entities import FunctionCall
from src.entities import GroqConfig
from src.entities import GroqModelType
from src.entities import OpenAiConfig
from src.entities import OpenAiModelType
from src.entities import OpenaiToolChoiceType
from src.entities import PromptType
from src.entities import KnowledgeBaseIndexingRequest
from src.entities import KnowledgeBaseQuery
from web3.types import TxReceipt


class OracleRepository:
    def __init__(self) -> None:
        self.last_chats_count = 0
        self.indexed_chats = []
        self.last_function_calls_count = 0
        self.indexed_function_calls = []
        self.last_kb_index_request_count = 0
        self.indexed_kb_index_requests = []
        self.last_kb_query_count = 0
        self.indexed_kb_queries = []
        self.web3_client = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(settings.WEB3_RPC_URL))
        self.account = self.web3_client.eth.account.from_key(settings.PRIVATE_KEY)
        with open(settings.ORACLE_ABI_PATH, "r", encoding="utf-8") as f:
            oracle_abi = json.loads(f.read())["abi"]

        self.oracle_contract = self.web3_client.eth.contract(
            address=settings.ORACLE_ADDRESS, abi=oracle_abi
        )

    async def _index_new_chats(self):
        chats_count = await self.oracle_contract.functions.promptsCount().call()
        config = None
        if chats_count > self.last_chats_count:
            print(f"Indexing new prompts from {self.last_chats_count} to {chats_count}",
                  flush=True)
            for i in range(self.last_chats_count, chats_count):
                callback_id = await self.oracle_contract.functions.promptCallbackIds(
                    i
                ).call()
                is_prompt_processed = (
                    await self.oracle_contract.functions.isPromptProcessed(i).call()
                )
                prompt_type = await self._get_prompt_type(i)
                if prompt_type == PromptType.OPENAI:
                    config = await self._get_openai_config(i)
                elif prompt_type == PromptType.GROQ:
                    config = await self._get_groq_config(i)
                messages = []
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
                self.indexed_chats.append(
                    Chat(
                        id=i,
                        messages=messages,
                        callback_id=callback_id,
                        is_processed=is_prompt_processed,
                        prompt_type=prompt_type,
                        config=config,
                    )
                )
            self.last_chats_count = chats_count

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
            await self.mark_as_done(chat)
            return False
        tx_receipt = await self._sign_and_send_tx(tx)
        chat.transaction_receipt = tx_receipt
        chat.is_processed = bool(tx_receipt.get("status"))
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
        return await self._sign_and_send_tx(tx)

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

    async def _index_new_function_calls(self):
        function_calls_count = (
            await self.oracle_contract.functions.functionsCount().call()
        )
        if function_calls_count > self.last_function_calls_count:
            print(
                f"Indexing new function calls from {self.last_function_calls_count} to {function_calls_count}",
                flush=True,
            )
            for i in range(self.last_function_calls_count, function_calls_count):
                callback_id = await self.oracle_contract.functions.functionCallbackIds(
                    i
                ).call()
                is_function_call_processed = (
                    await self.oracle_contract.functions.isFunctionProcessed(i).call()
                )
                function_type = await self.oracle_contract.functions.functionTypes(
                    i
                ).call()
                function_input = await self.oracle_contract.functions.functionInputs(
                    i
                ).call()
                self.indexed_function_calls.append(
                    FunctionCall(
                        id=i,
                        callback_id=callback_id,
                        is_processed=is_function_call_processed,
                        function_type=function_type,
                        function_input=function_input,
                    )
                )
            self.last_function_calls_count = function_calls_count

    async def get_unanswered_function_calls(self) -> List[FunctionCall]:
        await self._index_new_function_calls()
        unanswered_function_calls = [
            function_call
            for function_call in self.indexed_function_calls
            if not function_call.is_processed
        ]
        return unanswered_function_calls

    async def send_function_call_response(
        self, function_call: FunctionCall, response: str, error_message: str = ""
    ) -> bool:
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
        try:
            tx = await self.oracle_contract.functions.addFunctionResponse(
                function_call.id,
                function_call.callback_id,
                response,
                error_message,
            ).build_transaction(tx_data)
        except Exception as e:
            function_call.is_processed = True
            function_call.transaction_receipt = {"error": str(e)}
            await self.mark_function_call_as_done(function_call)
            return False
        tx_receipt = await self._sign_and_send_tx(tx)
        function_call.transaction_receipt = tx_receipt
        function_call.is_processed = bool(tx_receipt.get("status"))
        return bool(tx_receipt.get("status"))

    async def mark_function_call_as_done(self, function_call: FunctionCall):
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

        tx = await self.oracle_contract.functions.markFunctionAsProcessed(
            function_call.id,
        ).build_transaction(tx_data)
        return await self._sign_and_send_tx(tx)

    async def _index_new_kb_index_requests(self):
        kb_index_request_count = (
            await self.oracle_contract.functions.kbIndexingRequestCount().call()
        )
        if kb_index_request_count > self.last_kb_index_request_count:
            print(
                f"Indexing new knowledge base indexing requests from {self.last_kb_index_request_count} to {kb_index_request_count}"
            )
            for i in range(self.last_kb_index_request_count, kb_index_request_count):
                is_processed = (
                    await self.oracle_contract.functions.isKbIndexingRequestProcessed(
                        i
                    ).call()
                )
                cid = await self.oracle_contract.functions.kbIndexingRequests(i).call()
                index_cid = await self.oracle_contract.functions.kbIndexes(cid).call()
                self.indexed_kb_index_requests.append(
                    KnowledgeBaseIndexingRequest(
                        id=i,
                        cid=cid,
                        index_cid=index_cid,
                        is_processed=is_processed,
                    )
                )
            self.last_kb_index_request_count = kb_index_request_count

    async def get_unindexed_knowledge_bases(self) -> List[KnowledgeBaseIndexingRequest]:
        await self._index_new_kb_index_requests()
        unanswered_kb_indexing_requests = [
            kb_indexing_request
            for kb_indexing_request in self.indexed_kb_index_requests
            if not kb_indexing_request.is_processed
        ]
        return unanswered_kb_indexing_requests

    async def send_kb_indexing_response(
        self,
        request: KnowledgeBaseIndexingRequest,
        index_cid: str,
        error_message: str,
    ) -> bool:
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
        try:
            tx = await self.oracle_contract.functions.addKnowledgeBaseIndex(
                request.id, index_cid, error_message
            ).build_transaction(tx_data)
        except Exception as e:
            request.is_processed = True
            request.transaction_receipt = {"error": str(e)}
            return False
        signed_tx = self.web3_client.eth.account.sign_transaction(
            tx, private_key=self.account.key
        )
        tx_hash = await self.web3_client.eth.send_raw_transaction(
            signed_tx.rawTransaction
        )
        tx_receipt = await self.web3_client.eth.wait_for_transaction_receipt(tx_hash)
        request.transaction_receipt = tx_receipt
        request.is_processed = bool(tx_receipt.get("status"))
        return bool(tx_receipt.get("status"))

    async def _index_new_kb_queries(self):
        kb_query_count = await self.oracle_contract.functions.kbQueryCount().call()
        if kb_query_count > self.last_kb_query_count:
            print(
                f"Indexing new knowledge base queries from {self.last_kb_query_count} to {kb_query_count}"
            )
            for i in range(self.last_kb_query_count, kb_query_count):
                callback_id = await self.oracle_contract.functions.kbQueryCallbackIds(
                    i
                ).call()
                is_processed = await self.oracle_contract.functions.isKbQueryProcessed(
                    i
                ).call()
                request = await self.oracle_contract.functions.kbQueries(i).call()
                cid = request[0]
                query = request[1]
                num_documents = request[2]
                index_cid = await self.oracle_contract.functions.kbIndexes(cid).call()
                self.indexed_kb_queries.append(
                    KnowledgeBaseQuery(
                        id=i,
                        callback_id=callback_id,
                        is_processed=is_processed,
                        cid=cid,
                        index_cid=index_cid,
                        query=query,
                        num_documents=num_documents,
                    )
                )
            self.last_kb_query_count = kb_query_count

    async def get_unanswered_kb_queries(self) -> List[KnowledgeBaseQuery]:
        await self._index_new_kb_queries()
        unanswered_kb_queries = [
            kb_query
            for kb_query in self.indexed_kb_queries
            if not kb_query.is_processed
        ]
        return unanswered_kb_queries

    async def send_kb_query_response(
        self,
        request: KnowledgeBaseQuery,
        documents: List[str],
        error_message: str = "",
    ) -> bool:
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
        try:
            tx = await self.oracle_contract.functions.addKnowledgeBaseQueryResponse(
                request.id, request.callback_id, documents, error_message
            ).build_transaction(tx_data)
        except Exception as e:
            request.is_processed = True
            request.transaction_receipt = {"error": str(e)}
            return False
        signed_tx = self.web3_client.eth.account.sign_transaction(
            tx, private_key=self.account.key
        )
        tx_hash = await self.web3_client.eth.send_raw_transaction(
            signed_tx.rawTransaction
        )
        tx_receipt = await self.web3_client.eth.wait_for_transaction_receipt(tx_hash)
        request.transaction_receipt = tx_receipt
        request.is_processed = bool(tx_receipt.get("status"))
        return bool(tx_receipt.get("status"))

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
                tool_choice=config[11] if (config[11] and config[11] in get_args(
                    OpenaiToolChoiceType)) else None,
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
                user=_value_or_none(config[10]),
            )
        except:
            return None

    async def _get_prompt_type(self, i) -> PromptType:
        prompt_type: Optional[str] = await self.oracle_contract.functions.promptType(
            i).call()
        if not prompt_type:
            return PromptType.DEFAULT
        try:
            return PromptType(prompt_type)
        except:
            return PromptType.DEFAULT

    async def _sign_and_send_tx(self, tx) -> TxReceipt:
        signed_tx = self.web3_client.eth.account.sign_transaction(
            tx, private_key=self.account.key
        )
        tx_hash = await self.web3_client.eth.send_raw_transaction(
            signed_tx.rawTransaction
        )
        await self.web3_client.eth.wait_for_transaction_receipt(tx_hash)

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


def _value_or_none(value: Any) -> Optional[Any]:
    return value if value else None


def _parse_float_from_int(
    value: Optional[float],
    min_value: int,
    max_value: int,
    decimals: int = 1
) -> Optional[int]:
    return round(value / (10 ** decimals), 1) if (
        min_value <= value <= max_value) else None


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
        "systemFingerprint": completion.system_fingerprint,
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
        "created": completion.created,
        "model": completion.model,
        "systemFingerprint": completion.system_fingerprint,
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
