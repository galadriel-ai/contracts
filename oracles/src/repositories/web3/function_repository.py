from typing import List
from typing import Optional

from web3.exceptions import ContractLogicError

import settings

from src.entities import FunctionCall
from src.repositories.web3.base import Web3BaseRepository


class Web3FunctionRepository(Web3BaseRepository):
    def __init__(self) -> None:
        super().__init__()
        self.last_function_calls_count = 0
        self.indexed_function_calls = []

    async def _get_function_call(self, i: int) -> Optional[FunctionCall]:
        try:
            callback_id = await self.oracle_contract.functions.functionCallbackIds(
                i
            ).call()
            is_function_call_processed = (
                await self.oracle_contract.functions.isFunctionProcessed(i).call()
            )
            function_type = await self.oracle_contract.functions.functionTypes(i).call()
            function_input = await self.oracle_contract.functions.functionInputs(
                i
            ).call()
            return FunctionCall(
                id=i,
                callback_id=callback_id,
                is_processed=is_function_call_processed,
                function_type=function_type,
                function_input=function_input,
            )
        except ContractLogicError as e:
            print(f"Error getting function call {i}: {e.message}", flush=True)
            return None

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
                function_call = await self._get_function_call(i)
                if function_call:
                    self.indexed_function_calls.append(function_call)
                self.last_function_calls_count = i + 1

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
