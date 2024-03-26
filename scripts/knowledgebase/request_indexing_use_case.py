import json
import time
from typing import Optional

import settings

from web3 import Web3


web3_client = Web3(Web3.HTTPProvider(settings.RPC_URL))
account = web3_client.eth.account.from_key(settings.PRIVATE_KEY)
with open(settings.ORACLE_ABI_PATH, "r", encoding="utf-8") as f:
    oracle_abi = json.loads(f.read())["abi"]

contract = web3_client.eth.contract(address=settings.ORACLE_ADDRESS, abi=oracle_abi)


def _get_index_cid(cid: str) -> str:
    return contract.functions.kbIndexes(cid).call()


def _request_indexing(cid: str) -> bool:
    nonce = web3_client.eth.get_transaction_count(account.address)
    tx_data = {
        "from": account.address,
        "nonce": nonce,
        "maxFeePerGas": web3_client.to_wei("2", "gwei"),
        "maxPriorityFeePerGas": web3_client.to_wei("1", "gwei"),
    }
    if chain_id := settings.CHAIN_ID:
        tx_data["chainId"] = int(chain_id)
    tx = contract.functions.addKnowledgeBase(
        cid,
    ).build_transaction(tx_data)
    signed_tx = web3_client.eth.account.sign_transaction(tx, private_key=account.key)
    tx_hash = web3_client.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = web3_client.eth.wait_for_transaction_receipt(tx_hash)
    return bool(tx_receipt.get("status"))


def _wait_for_indexing(cid: str, max_loops: int = 120) -> Optional[str]:
    print("Waiting for indexing to complete...")
    for _ in range(max_loops):
        index_cid = _get_index_cid(cid)
        if len(index_cid) > 0:
            return index_cid
        else:
            time.sleep(5)


def execute(cid: str) -> Optional[str]:
    index_cid = _get_index_cid(cid)
    if len(index_cid) > 0:
        return index_cid
    requested = _request_indexing(cid)
    if not requested:
        return None
    return _wait_for_indexing(cid)
