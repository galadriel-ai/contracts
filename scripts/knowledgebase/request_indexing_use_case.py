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


def _index_next_prompt():
    global calls_made, last_unindexed_prompt_id
    current_prompt_index = last_unindexed_prompt_id + 1
    while prompt := _get_prompt(current_prompt_index):
        calls_made = calls_made + 1
        if prompt:
            callback_address = contract.functions.callbackAddresses(
                current_prompt_index
            ).call()
            callback_id = contract.functions.promptCallbackIds(
                current_prompt_index
            ).call()
            is_prompt_processed = contract.functions.isPromptProcessed(
                current_prompt_index
            ).call()
            calls_made = calls_made + 3

            if is_prompt_processed:
                print(f"Prompt with index {current_prompt_index} is already processed")
            else:
                print(f"Found new prompt: {prompt}")

            indexed_prompts.append(
                PromptAndResponse(
                    id=current_prompt_index,
                    prompt=prompt,
                    callback_id=callback_id,
                    callback_address=callback_address,
                    is_processed=is_prompt_processed,
                    response=None,
                )
            )
            last_unindexed_prompt_id = current_prompt_index
        current_prompt_index = last_unindexed_prompt_id + 1
    else:
        calls_made = calls_made + 1


def _get_prompt(current_prompt_index):
    try:
        return contract.functions.prompts(current_prompt_index).call()
    except:
        return None


def _get_index_cid(cid: str) -> str:
    return contract.functions.kbIndexes(cid).call()

def _request_indexing(cid: str) -> bool:
    nonce = web3_client.eth.get_transaction_count(account.address)
    tx_data = {
        "from": account.address,
        "nonce": nonce,
        # TODO: pick gas amount in a better way
        # "gas": 1000000,
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
    while True:
        index_cid = _get_index_cid(cid)
        if len(index_cid) > 0:
            return index_cid
        else:
            time.sleep(5)


def execute(cid: str) -> Optional[str]:
    index_cid = _get_index_cid(cid)
    if len(index_cid) > 0 :
        return index_cid
    requested = _request_indexing(cid)
    if not requested:
        return None
    return _wait_for_indexing(cid)

