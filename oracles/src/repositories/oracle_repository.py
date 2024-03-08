import json
from typing import List
from web3 import AsyncWeb3
from src.entities import Chat

import settings


class OracleRepository:

    def __init__(self) -> None:
        self.last_chats_count = 0
        self.indexed_chats = []
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
            print(
                f"Indexing new prompts from {self.last_chats_count} to {chats_count}"
            )
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
        unanswered_chats = [chat for chat in self.indexed_chats if not chat.is_processed]
        return unanswered_chats

    async def send_response(self, chat: Chat, response: str) -> bool:
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
            chat.id,
            chat.callback_id,
            response,
            "assistant",
        ).build_transaction(tx_data)
        signed_tx = self.web3_client.eth.account.sign_transaction(
            tx, private_key=self.account.key
        )
        tx_hash = await self.web3_client.eth.send_raw_transaction(
            signed_tx.rawTransaction
        )
        tx_receipt = await self.web3_client.eth.wait_for_transaction_receipt(tx_hash)
        chat.is_processed = bool(tx_receipt.get("status"))
        return bool(tx_receipt.get("status"))
