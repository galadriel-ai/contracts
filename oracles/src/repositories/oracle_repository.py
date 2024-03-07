import json
from typing import List
from web3 import Web3
from src.entities import PromptAndResponse

import settings


class OracleRepository:

    def __init__(self) -> None:
        self.calls_made = 0
        self.last_unindexed_prompt_id = -1
        self.indexed_prompts = []
        self.web3_client = Web3(Web3.HTTPProvider(settings.WEB3_RPC_URL))
        self.account = self.web3_client.eth.account.from_key(settings.PRIVATE_KEY)
        with open(settings.ORACLE_ABI_PATH, "r", encoding="utf-8") as f:
            oracle_abi = json.loads(f.read())["abi"]

        self.oracle_contract = self.web3_client.eth.contract(
            address=settings.ORACLE_ADDRESS, abi=oracle_abi
        )

    def _index_next_prompt(self):
        current_prompt_index = self.last_unindexed_prompt_id + 1
        while prompt := self._get_prompt(current_prompt_index):
            self.calls_made = self.calls_made + 1
            if prompt:
                callback_address = self.contract.functions.callbackAddresses(
                    current_prompt_index
                ).call()
                callback_id = self.contract.functions.promptCallbackIds(
                    current_prompt_index
                ).call()
                is_prompt_processed = self.contract.functions.isPromptProcessed(
                    current_prompt_index
                ).call()
                self.calls_made = self.calls_made + 3

                if is_prompt_processed:
                    print(
                        f"Prompt with index {current_prompt_index} is already processed"
                    )
                else:
                    print(f"Found new prompt: {prompt}")

                self.indexed_prompts.append(
                    PromptAndResponse(
                        id=current_prompt_index,
                        prompt=prompt,
                        callback_id=callback_id,
                        callback_address=callback_address,
                        is_processed=is_prompt_processed,
                        response=None,
                    )
                )
                self.last_unindexed_prompt_id = current_prompt_index
            current_prompt_index = self.last_unindexed_prompt_id + 1
        else:
            self.calls_made = self.calls_made + 1

    def get_unanswered_prompts(self) -> List[PromptAndResponse]:
        self._index_next_prompt()
        return [prompt for prompt in self.indexed_prompts if not prompt.is_processed]

    def _get_prompt(self, current_prompt_index: int) -> str:
        try:
            return self.contract.functions.prompts(current_prompt_index).call()
        except:
            return None

    def _index_next_prompt(self):
        current_prompt_index = self.last_unindexed_prompt_id + 1
        while prompt := self._get_prompt(current_prompt_index):
            self.calls_made = self.calls_made + 1
            if prompt:
                callback_address = self.contract.functions.callbackAddresses(
                    current_prompt_index
                ).call()
                callback_id = self.contract.functions.promptCallbackIds(
                    current_prompt_index
                ).call()
                is_prompt_processed = self.contract.functions.isPromptProcessed(
                    current_prompt_index
                ).call()
                calls_made = calls_made + 3

                if is_prompt_processed:
                    print(
                        f"Prompt with index {current_prompt_index} is already processed"
                    )
                else:
                    print(f"Found new prompt: {prompt}")

                self.indexed_prompts.append(
                    PromptAndResponse(
                        id=current_prompt_index,
                        prompt=prompt,
                        callback_id=callback_id,
                        callback_address=callback_address,
                        is_processed=is_prompt_processed,
                        response=None,
                    )
                )
                self.last_unindexed_prompt_id = current_prompt_index
            current_prompt_index = self.last_unindexed_prompt_id + 1
        else:
            self.calls_made = self.calls_made + 1

    def send_response(self, prompt: PromptAndResponse, response: str) -> bool:
        nonce = self.web3_client.eth.get_transaction_count(self.account.address)
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
        tx = self.contract.functions.addResponse(
            prompt.id,
            response,
            prompt.callback_id,
        ).build_transaction(tx_data)
        signed_tx = self.web3_client.eth.account.sign_transaction(
            tx, private_key=self.account.key
        )
        tx_hash = self.web3_client.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_receipt = self.web3_client.eth.wait_for_transaction_receipt(tx_hash)
        prompt.is_processed = bool(tx_receipt.get("status"))
        return bool(tx_receipt.get("status"))
