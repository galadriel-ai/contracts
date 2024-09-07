from typing import List
from typing import Optional

from web3.exceptions import ContractLogicError

import settings

from src.entities import LangchainKnowledgeBaseIndexingRequest
from src.entities import LangchainKnowledgeBaseQuery
from src.repositories.web3.base import Web3BaseRepository


class Web3LangchainKnowledgeBaseRepository(Web3BaseRepository):
    def __init__(self) -> None:
        super().__init__()
        self.last_kb_index_request_count = 0
        self.indexed_kb_index_requests = []
        self.last_kb_query_count = 0
        self.indexed_kb_queries = []
        self.metrics.update(
            {
                "langchain_knowledgebase_index_count": 0,
                "langchain_knowledgebase_query_count": 0,
                "langchain_knowledgebase_index_read": 0,
                "langchain_knowledgebase_query_read": 0,
                "langchain_knowledgebase_index_answered": 0,
                "langchain_knowledgebase_query_answered": 0,
                "langchain_knowledgebase_index_read_errors": 0,
                "langchain_knowledgebase_query_read_errors": 0,
                "langchain_knowledgebase_index_write_errors": 0,
                "langchain_knowledgebase_query_write_errors": 0,
                "langchain_knowledgebase_index_marked_as_done": 0,
                "langchain_knowledgebase_query_marked_as_done": 0,
            }
        )

    async def _get_knowledge_base_indexing_request(
        self, i: int
    ) -> Optional[LangchainKnowledgeBaseIndexingRequest]:
        try:
            is_processed = (
                await self.oracle_contract.functions.langchainisKbIndexingRequestProcessed(
                    i
                ).call()
            )
            key = await self.oracle_contract.functions.langchainkbIndexingRequests(i).call()
            return LangchainKnowledgeBaseIndexingRequest(
                id=i,
                key=key,
                is_processed=is_processed,
            )
        except ContractLogicError as e:
            print(f"Error getting knowledge base indexing request {i}: {e}")
            return None

    async def _index_new_kb_index_requests(self):
        langchain_kb_index_request_count = (
            await self.oracle_contract.functions.langchainkbIndexingRequestCount().call()
        )
        self.metrics["langchain_knowledgebase_index_count"] = langchain_kb_index_request_count
        if not self.last_kb_index_request_count and langchain_kb_index_request_count > 0:
            self.last_kb_index_request_count = await self._find_first_unprocessed(
                langchain_kb_index_request_count,
                lambda index: self.oracle_contract.functions.langchainisKbIndexingRequestProcessed(
                    index
                ).call(),
            )
            self.metrics["langchain_knowledgebase_index_marked_as_done"] = (
                self.last_kb_index_request_count
            )
            print(
                f"Found first unprocessed kb indexing request {self.last_kb_index_request_count} on cold start, marking all previous as processed",
                flush=True,
            )
        if langchain_kb_index_request_count > self.last_kb_index_request_count:
            print(
                f"Indexing new knowledge base indexing requests from {self.last_kb_index_request_count} to {langchain_kb_index_request_count}"
            )
            for i in range(self.last_kb_index_request_count, langchain_kb_index_request_count):
                langchain_kb_index_request = await self._get_knowledge_base_indexing_request(i)
                if langchain_kb_index_request:
                    self.indexed_kb_index_requests.append(langchain_kb_index_request)
                    self.metrics["langchain_knowledgebase_index_read"] += 1
                    if langchain_kb_index_request.is_processed:
                        self.metrics["langchain_knowledgebase_index_marked_as_done"] += 1
                else:
                    self.metrics["langchain_knowledgebase_index_read_errors"] += 1
                self.last_kb_index_request_count = i + 1

    async def get_unindexed_knowledge_bases(self) -> List[LangchainKnowledgeBaseIndexingRequest]:
        await self._index_new_kb_index_requests()
        unanswered_kb_indexing_requests = [
            kb_indexing_request
            for kb_indexing_request in self.indexed_kb_index_requests
            if not kb_indexing_request.is_processed
        ]
        return unanswered_kb_indexing_requests

    async def send_kb_indexing_response(
        self,
        request: LangchainKnowledgeBaseIndexingRequest,
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
            tx = await self.oracle_contract.functions.addLangchainKnowledgeBaseIndex(
                request.id, error_message
            ).build_transaction(tx_data)
        except Exception as e:
            request.is_processed = True
            request.transaction_receipt = {"error": str(e)}
            self.metrics["langchain_knowledgebase_index_write_errors"] += 1
            await self.mark_kb_indexing_request_as_done(request)
            return False
        tx_receipt = await self._sign_and_send_tx(tx)
        request.transaction_receipt = tx_receipt
        request.is_processed = bool(tx_receipt.get("status"))
        if request.is_processed:
            self.metrics["langchain_knowledgebase_index_answered"] += 1
            self.metrics["langchain_knowledgebase_index_marked_as_done"] += 1
        return bool(tx_receipt.get("status"))

    async def mark_kb_indexing_request_as_done(
        self, request: LangchainKnowledgeBaseIndexingRequest
    ):
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

        tx = await self.oracle_contract.functions.markLangchainKnowledgeBaseAsProcessed(
            request.id,
        ).build_transaction(tx_data)
        tx_receipt = await self._sign_and_send_tx(tx)
        if bool(tx_receipt.get("status")):
            self.metrics["langchain_knowledgebase_index_marked_as_done"] += 1
        return tx_receipt

    async def _get_kb_query(self, i: int) -> Optional[LangchainKnowledgeBaseQuery]:
        try:
            callback_id = await self.oracle_contract.functions.langchainkbQueryCallbackIds(
                i
            ).call()
            is_processed = await self.oracle_contract.functions.langchainisKbQueryProcessed(
                i
            ).call()
            request = await self.oracle_contract.functions.langchainkbQueries(i).call()
            query = request[0]
            num_documents = request[1]
            return LangchainKnowledgeBaseQuery(
                id=i,
                callback_id=callback_id,
                is_processed=is_processed,
                query=query,
                num_documents=num_documents,
            )
        except ContractLogicError as e:
            print(f"Error getting knowledge base query {i}: {e}")
            return None

    async def _index_new_kb_queries(self):
        langchain_kb_query_count = await self.oracle_contract.functions.langchainkbQueryCount().call()
        self.metrics["langchain_knowledgebase_query_count"] = langchain_kb_query_count
        if not self.last_kb_query_count and langchain_kb_query_count > 0:
            self.last_kb_query_count = await self._find_first_unprocessed(
                langchain_kb_query_count,
                lambda index: self.oracle_contract.functions.langchainisKbQueryProcessed(
                    index
                ).call(),
            )
            self.metrics["langchain_knowledgebase_query_marked_as_done"] = (
                self.last_kb_query_count
            )
            print(
                f"Found first unprocessed kb query request {self.last_kb_query_count} on cold start, marking all previous as processed",
                flush=True,
            )
        if langchain_kb_query_count > self.last_kb_query_count:
            print(
                f"Indexing new knowledge base queries from {self.last_kb_query_count} to {langchain_kb_query_count}"
            )
            for i in range(self.last_kb_query_count, langchain_kb_query_count):
                kb_query = await self._get_kb_query(i)
                if kb_query:
                    self.indexed_kb_queries.append(kb_query)
                    self.metrics["langchain_knowledgebase_query_read"] += 1
                    if kb_query.is_processed:
                        self.metrics["langchain_knowledgebase_query_marked_as_done"] += 1
                else:
                    self.metrics["langchain_knowledgebase_query_read_errors"] += 1
                self.last_kb_query_count = i + 1

    async def get_unanswered_kb_queries(self) -> List[LangchainKnowledgeBaseQuery]:
        await self._index_new_kb_queries()
        unanswered_kb_queries = [
            kb_query
            for kb_query in self.indexed_kb_queries
            if not kb_query.is_processed
        ]
        return unanswered_kb_queries

    async def send_kb_query_response(
        self,
        request: LangchainKnowledgeBaseQuery,
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
            tx = await self.oracle_contract.functions.addLangchainKnowledgeBaseQueryResponse(
                request.id, request.callback_id, documents, error_message
            ).build_transaction(tx_data)
        except Exception as e:
            request.is_processed = True
            request.transaction_receipt = {"error": str(e)}
            self.metrics["langchain_knowledgebase_query_write_errors"] += 1
            await self.mark_kb_query_as_done(request)
            return False
        tx_receipt = await self._sign_and_send_tx(tx)
        request.transaction_receipt = tx_receipt
        request.is_processed = bool(tx_receipt.get("status"))
        if request.is_processed:
            self.metrics["langchain_knowledgebase_query_answered"] += 1
            self.metrics["langchain_knowledgebase_query_marked_as_done"] += 1
        return bool(tx_receipt.get("status"))

    async def mark_kb_query_as_done(self, query: LangchainKnowledgeBaseQuery):
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

        tx = await self.oracle_contract.functions.markLangchainKnowledgeBaseQueryAsProcessed(
            query.id,
        ).build_transaction(tx_data)
        tx_receipt = await self._sign_and_send_tx(tx)
        if bool(tx_receipt.get("status")):
            self.metrics["langchain_knowledgebase_query_marked_as_done"] += 1
        return tx_receipt
