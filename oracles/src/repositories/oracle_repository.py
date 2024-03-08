import json
from typing import List
from web3 import AsyncWeb3
from src.entities import PromptAndResponse

import settings


class OracleRepository:

    def __init__(self) -> None:
        self.last_prompt_count = 0
        self.indexed_prompts = []
        self.web3_client = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(settings.WEB3_RPC_URL))
        self.account = self.web3_client.eth.account.from_key(settings.PRIVATE_KEY)
        with open(settings.ORACLE_ABI_PATH, "r", encoding="utf-8") as f:
            oracle_abi = json.loads(f.read())["abi"]

        self.oracle_contract = self.web3_client.eth.contract(
            address=settings.ORACLE_ADDRESS, abi=oracle_abi
        )

    async def _index_new_prompts(self):
        prompts_count = await self.oracle_contract.functions.promptsCount().call()
        if prompts_count > self.last_prompt_count:
            for i in range(self.last_prompt_count, prompts_count -1 ):
                prompt = await self._get_prompt(i)
                if prompt:
                    callback_address = await self._get_callback_address(i)
                    callback_id = await self.oracle_contract.functions.promptCallbackIds(i).call()
                    is_prompt_processed = await self.oracle_contract.functions.isPromptProcessed(i).call()
                    self.indexed_prompts.append(
                        PromptAndResponse(
                            id=i,
                            prompt=prompt,
                            callback_id=callback_id,
                            callback_address=callback_address,
                            is_processed=is_prompt_processed,
                            response=None,
                        )
                    )

    async def _get_callback_address(self, current_prompt_index: int) -> str:
        try:
            return await self.oracle_contract.functions.callbackAddresses(current_prompt_index).call()
        except Exception as e:
            print(e)
            return None

    async def get_unanswered_prompts(self) -> List[PromptAndResponse]:
        await self._index_next_prompt()
        return [prompt for prompt in self.indexed_prompts if not prompt.is_processed]

    async def send_response(self, prompt: PromptAndResponse, response: str) -> bool:
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
        tx = await self.oracle_contract.functions.addResponse(
            prompt.id,
            response,
            prompt.callback_id,
        ).build_transaction(tx_data)
        signed_tx = await self.web3_client.eth.account.sign_transaction(
            tx, private_key=self.account.key
        )
        tx_hash = await self.web3_client.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_receipt = await self.web3_client.eth.wait_for_transaction_receipt(tx_hash)
        prompt.is_processed = bool(tx_receipt.get("status"))
        return bool(tx_receipt.get("status"))
