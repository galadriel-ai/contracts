import json
from typing import List
from web3 import AsyncWeb3
from src.entities import Chat
from src.entities import FunctionCall
from src.entities import KnowledgeBaseIndexingRequest
from src.entities import KnowledgeBaseQuery

import settings


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
        if chats_count > self.last_chats_count:
            print(f"Indexing new prompts from {self.last_chats_count} to {chats_count}")
            for i in range(self.last_chats_count, chats_count):
                callback_id = await self.oracle_contract.functions.promptCallbackIds(
                    i
                ).call()
                is_prompt_processed = (
                    await self.oracle_contract.functions.isPromptProcessed(i).call()
                )
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
            tx = await self.oracle_contract.functions.addResponse(
                chat.id,
                chat.callback_id,
                chat.response,
                chat.error_message,
            ).build_transaction(tx_data)
        except Exception as e:
            chat.is_processed = True
            chat.transaction_receipt = {"error": str(e)}
            return False
        signed_tx = self.web3_client.eth.account.sign_transaction(
            tx, private_key=self.account.key
        )
        tx_hash = await self.web3_client.eth.send_raw_transaction(
            signed_tx.rawTransaction
        )
        tx_receipt = await self.web3_client.eth.wait_for_transaction_receipt(tx_hash)
        chat.transaction_receipt = tx_receipt
        chat.is_processed = bool(tx_receipt.get("status"))
        return bool(tx_receipt.get("status"))

    async def _index_new_function_calls(self):
        function_calls_count = (
            await self.oracle_contract.functions.functionsCount().call()
        )
        if function_calls_count > self.last_function_calls_count:
            print(
                f"Indexing new function calls from {self.last_function_calls_count} to {function_calls_count}"
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
            return False
        signed_tx = self.web3_client.eth.account.sign_transaction(
            tx, private_key=self.account.key
        )
        tx_hash = await self.web3_client.eth.send_raw_transaction(
            signed_tx.rawTransaction
        )
        tx_receipt = await self.web3_client.eth.wait_for_transaction_receipt(tx_hash)
        function_call.transaction_receipt = tx_receipt
        function_call.is_processed = bool(tx_receipt.get("status"))
        return bool(tx_receipt.get("status"))

    async def _index_new_kb_index_requests(self):
        kb_index_request_count = (
            await self.oracle_contract.functions.kbIndexingRequestCount().call()
        )
        if kb_index_request_count > self.last_kb_index_request_count:
            print(
                f"Indexing new knowledge base indexing requests from {self.last_kb_index_request_count} to {kb_index_request_count}"
            )
            for i in range(self.last_kb_index_request_count, kb_index_request_count):
                cid = await self.oracle_contract.functions.kbIndexingRequests(i).call()
                index_cid = await self.oracle_contract.functions.kbIndexes(cid).call()
                self.indexed_kb_index_requests.append(
                    KnowledgeBaseIndexingRequest(
                        id=i,
                        cid=cid,
                        index_cid=index_cid,
                        is_processed=index_cid != "",
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
            tx = await self.oracle_contract.functions.addKnowledgeBaseIndex(
                request.id,
                index_cid,
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
                index_cid = await self.oracle_contract.functions.kbQueryCids(i).call()
                query = await self.oracle_contract.functions.kbQueries(i).call()
                self.indexed_kb_queries.append(
                    KnowledgeBaseQuery(
                        id=i,
                        callback_id=callback_id,
                        is_processed=is_processed,
                        index_cid=index_cid,
                        query=query,
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
