import json

from web3 import AsyncWeb3
from web3.types import TxReceipt

import settings


class Web3BaseRepository:
    def __init__(self) -> None:
        self.web3_client = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(settings.WEB3_RPC_URL))
        self.account = self.web3_client.eth.account.from_key(settings.PRIVATE_KEY)
        with open(settings.ORACLE_ABI_PATH, "r", encoding="utf-8") as f:
            oracle_abi = json.loads(f.read())["abi"]

        self.oracle_contract = self.web3_client.eth.contract(
            address=settings.ORACLE_ADDRESS, abi=oracle_abi
        )
        self.metrics = {
            "transactions_sent": 0,
            "errors": 0,
        }

    async def _sign_and_send_tx(self, tx) -> TxReceipt:
        try:
            signed_tx = self.web3_client.eth.account.sign_transaction(
                tx, private_key=self.account.key
            )
            tx_hash = await self.web3_client.eth.send_raw_transaction(
                signed_tx.rawTransaction
            )
            return await self.web3_client.eth.wait_for_transaction_receipt(tx_hash)
        except Exception as e:
            self.metrics["errors"] += 1
            raise e
        finally:
            self.metrics["transactions_sent"] += 1

    def get_metrics(self):
        return self.metrics
