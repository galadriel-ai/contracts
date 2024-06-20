from typing import List
from typing import Optional

from web3.exceptions import ContractLogicError

import settings

from src.entities import KnowledgeBaseIndexingRequest
from src.entities import KnowledgeBaseQuery
from src.repositories.web3.base import Web3BaseRepository


class Web3KnowledgeBaseRepository(Web3BaseRepository):
    def __init__(self) -> None:
        super().__init__()
        self.last_kb_index_request_count = 0
        self.indexed_kb_index_requests = []
        self.last_kb_query_count = 0
        self.indexed_kb_queries = []
        self.metrics.update(
            {
                "knowledgebase_index_count": 0,
                "knowledgebase_query_count": 0,
                "knowledgebase_index_read": 0,
                "knowledgebase_query_read": 0,
                "knowledgebase_index_answered": 0,
                "knowledgebase_query_answered": 0,
                "knowledgebase_index_read_errors": 0,
                "knowledgebase_query_read_errors": 0,
                "knowledgebase_index_write_errors": 0,
                "knowledgebase_query_write_errors": 0,
                "knowledgebase_index_marked_as_done": 0,
                "knowledgebase_query_marked_as_done": 0,
            }
        )

    async def _get_knowledge_base_indexing_request(
        self, i: int
    ) -> Optional[KnowledgeBaseIndexingRequest]:
        try:
            is_processed = (
                await self.oracle_contract.functions.isKbIndexingRequestProcessed(
                    i
                ).call()
            )
            cid = await self.oracle_contract.functions.kbIndexingRequests(i).call()
            index_cid = await self.oracle_contract.functions.kbIndexes(cid).call()
            return KnowledgeBaseIndexingRequest(
                id=i,
                cid=cid,
                index_cid=index_cid,
                is_processed=is_processed,
            )
        except ContractLogicError as e:
            print(f"Error getting knowledge base indexing request {i}: {e}")
            return None

    async def _index_new_kb_index_requests(self):
        kb_index_request_count = (
            await self.oracle_contract.functions.kbIndexingRequestCount().call()
        )
        self.metrics["knowledgebase_index_count"] = kb_index_request_count
        if not self.last_kb_index_request_count and kb_index_request_count > 0:
            self.last_kb_index_request_count = await self._find_first_unprocessed(
                kb_index_request_count,
                lambda index: self.oracle_contract.functions.isKbIndexingRequestProcessed(
                    index
                ).call(),
            )
            self.metrics["knowledgebase_index_marked_as_done"] = (
                self.last_kb_index_request_count
            )
            print(
                f"Found first unprocessed kb indexing request {self.last_kb_index_request_count} on cold start, marking all previous as processed",
                flush=True,
            )
        if kb_index_request_count > self.last_kb_index_request_count:
            print(
                f"Indexing new knowledge base indexing requests from {self.last_kb_index_request_count} to {kb_index_request_count}"
            )
            for i in range(self.last_kb_index_request_count, kb_index_request_count):
                kb_index_request = await self._get_knowledge_base_indexing_request(i)
                if kb_index_request:
                    self.indexed_kb_index_requests.append(kb_index_request)
                    self.metrics["knowledgebase_index_read"] += 1
                    if kb_index_request.is_processed:
                        self.metrics["knowledgebase_index_marked_as_done"] += 1
                else:
                    self.metrics["knowledgebase_index_read_errors"] += 1
                self.last_kb_index_request_count = i + 1

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
            self.metrics["knowledgebase_index_write_errors"] += 1
            await self.mark_kb_indexing_request_as_done(request)
            return False
        tx_receipt = await self._sign_and_send_tx(tx)
        request.transaction_receipt = tx_receipt
        request.is_processed = bool(tx_receipt.get("status"))
        if request.is_processed:
            self.metrics["knowledgebase_index_answered"] += 1
            self.metrics["knowledgebase_index_marked_as_done"] += 1
        return bool(tx_receipt.get("status"))

    async def mark_kb_indexing_request_as_done(
        self, request: KnowledgeBaseIndexingRequest
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

        tx = await self.oracle_contract.functions.markKnowledgeBaseAsProcessed(
            request.id,
        ).build_transaction(tx_data)
        tx_receipt = await self._sign_and_send_tx(tx)
        if bool(tx_receipt.get("status")):
            self.metrics["knowledgebase_index_marked_as_done"] += 1
        return tx_receipt

    async def _get_kb_query(self, i: int) -> Optional[KnowledgeBaseQuery]:
        try:
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
            return KnowledgeBaseQuery(
                id=i,
                callback_id=callback_id,
                is_processed=is_processed,
                cid=cid,
                index_cid=index_cid,
                query=query,
                num_documents=num_documents,
            )
        except ContractLogicError as e:
            print(f"Error getting knowledge base query {i}: {e}")
            return None

    async def _index_new_kb_queries(self):
        kb_query_count = await self.oracle_contract.functions.kbQueryCount().call()
        self.metrics["knowledgebase_query_count"] = kb_query_count
        if not self.last_kb_query_count and kb_query_count > 0:
            self.last_kb_query_count = await self._find_first_unprocessed(
                kb_query_count,
                lambda index: self.oracle_contract.functions.isKbQueryProcessed(
                    index
                ).call(),
            )
            self.metrics["knowledgebase_query_marked_as_done"] = (
                self.last_kb_query_count
            )
            print(
                f"Found first unprocessed kb query request {self.last_kb_query_count} on cold start, marking all previous as processed",
                flush=True,
            )
        if kb_query_count > self.last_kb_query_count:
            print(
                f"Indexing new knowledge base queries from {self.last_kb_query_count} to {kb_query_count}"
            )
            for i in range(self.last_kb_query_count, kb_query_count):
                kb_query = await self._get_kb_query(i)
                if kb_query:
                    self.indexed_kb_queries.append(kb_query)
                    self.metrics["knowledgebase_query_read"] += 1
                    if kb_query.is_processed:
                        self.metrics["knowledgebase_query_marked_as_done"] += 1
                else:
                    self.metrics["knowledgebase_query_read_errors"] += 1
                self.last_kb_query_count = i + 1

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
            self.metrics["knowledgebase_query_write_errors"] += 1
            await self.mark_kb_query_as_done(request)
            return False
        tx_receipt = await self._sign_and_send_tx(tx)
        request.transaction_receipt = tx_receipt
        request.is_processed = bool(tx_receipt.get("status"))
        if request.is_processed:
            self.metrics["knowledgebase_query_answered"] += 1
            self.metrics["knowledgebase_query_marked_as_done"] += 1
        return bool(tx_receipt.get("status"))

    async def mark_kb_query_as_done(self, query: KnowledgeBaseQuery):
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

        tx = await self.oracle_contract.functions.markKnowledgeBaseQueryAsProcessed(
            query.id,
        ).build_transaction(tx_data)
        tx_receipt = await self._sign_and_send_tx(tx)
        if bool(tx_receipt.get("status")):
            self.metrics["knowledgebase_query_marked_as_done"] += 1
        return tx_receipt
