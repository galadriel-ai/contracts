import json
import time
from typing import Optional
import settings
from knowledgebase.entities import KnowledgeBaseIndexingResponse

from web3 import Web3


web3_client = Web3(Web3.HTTPProvider(settings.RPC_URL))
account = web3_client.eth.account.from_key(settings.PRIVATE_KEY)
with open(settings.ORACLE_ABI_PATH, "r", encoding="utf-8") as f:
    oracle_abi = json.loads(f.read())["abi"]

contract = web3_client.eth.contract(address=settings.ORACLE_ADDRESS, abi=oracle_abi)


def _get_index_cid(cid: str) -> str:
    return contract.functions.kbIndexes(cid).call()


def _get_indexing_error(request_id: int) -> str:
    return contract.functions.kbIndexingRequestErrors(request_id).call()


def _is_indexing_request_processed(request_id: int) -> bool:
    return contract.functions.isKbIndexingRequestProcessed(request_id).call()


def _request_indexing(cid: str) -> Optional[int]:
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

    event = contract.events.KnowledgeBaseIndexRequestAdded()
    decoded_logs = event.process_receipt(tx_receipt)
    success = bool(tx_receipt.get("status"))
    if success:
        return decoded_logs[0]["args"]["id"]


def _wait_for_indexing(
    request_id: int, cid: str, max_loops: int = 120
) -> KnowledgeBaseIndexingResponse:
    print("Waiting for indexing to complete...", end="", flush=True)
    for _ in range(max_loops):
        index_cid = _get_index_cid(cid)
        error = _get_indexing_error(request_id)
        is_processed = _is_indexing_request_processed(request_id)
        if is_processed:
            return KnowledgeBaseIndexingResponse(
                id=request_id,
                is_processed=is_processed,
                index_cid=index_cid,
                error=error,
            )
        else:
            time.sleep(5)
    return KnowledgeBaseIndexingResponse(
        id=request_id,
        is_processed=False,
        index_cid=None,
        error="Timed out waiting for indexing to finish",
    )


def execute(cid: str) -> KnowledgeBaseIndexingResponse:
    index_cid = _get_index_cid(cid)
    if len(index_cid) and index_cid[0]:
        return KnowledgeBaseIndexingResponse(
            id=None, is_processed=True, index_cid=index_cid, error=None
        )
    request_id = _request_indexing(cid)
    if request_id is None:
        return KnowledgeBaseIndexingResponse(
            id=None,
            is_processed=False,
            index_cid=None,
            error="Failed to request indexing",
        )
    print("done.")
    return _wait_for_indexing(request_id, cid)
