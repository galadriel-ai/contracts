import json
import time
from dataclasses import dataclass
from typing import List
from typing import Optional

from openai import OpenAI
from openai.types.chat import ChatCompletion
from web3 import Web3

import settings

# Might have to renew connection sometimes?
web3_client = Web3(Web3.HTTPProvider(settings.WEB3_RPC_URL))
account = web3_client.eth.account.from_key(settings.PRIVATE_KEY)
with open(settings.ORACLE_ABI_PATH, "r", encoding="utf-8") as f:
    oracle_abi = json.loads(f.read())["abi"]
contract = web3_client.eth.contract(address=settings.ORACLE_ADDRESS, abi=oracle_abi)

# Really should persist this data..
last_unindexed_prompt_id: int = -1


@dataclass
class PromptAndResponse:
    id: int
    prompt: str
    callback_id: int
    # Not actually needed here, contract handles it
    callback_address: str
    is_processed: bool
    response: Optional[str] = None


calls_made = 0
indexed_prompts: List[PromptAndResponse] = []


def _index_next_prompt():
    global calls_made, last_unindexed_prompt_id
    current_prompt_index = last_unindexed_prompt_id + 1
    while prompt := _get_prompt(current_prompt_index):
        calls_made = calls_made + 1
        if prompt:
            callback_address = contract.functions.callbackAddresses(current_prompt_index).call()
            callback_id = contract.functions.promptCallbackIds(current_prompt_index).call()
            is_prompt_processed = contract.functions.isPromptProcessed(current_prompt_index).call()
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


def _answer_unanswered_prompts():
    for prompt in indexed_prompts:
        if not prompt.is_processed:
            # If already have response but haven't sent on-chain then reuse, some edge-cases here too
            response = prompt.response or _get_openai_answer(prompt.prompt)
            if response:
                prompt.response = response
                if _send_add_response_tx(prompt, response):
                    prompt.is_processed = True


def _get_openai_answer(prompt: str) -> Optional[str]:
    try:
        client = OpenAI(
            # This is the default and can be omitted
            api_key=settings.OPEN_AI_API_KEY,
        )

        chat_completion: ChatCompletion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="gpt-3.5-turbo",
        )
        print("chat_completion:", chat_completion)
        answer = chat_completion.choices[0].message.content
        print("answer from OpenAI:", answer)
        return answer
    except Exception as exc:
        print("OPENAI Exception:", exc)


def _send_add_response_tx(prompt: PromptAndResponse, response: str) -> bool:
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
    tx = contract.functions.addResponse(
        prompt.id,
        response,
        prompt.callback_id,
    ).build_transaction(tx_data)
    signed_tx = web3_client.eth.account.sign_transaction(tx, private_key=account.key)
    tx_hash = web3_client.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = web3_client.eth.wait_for_transaction_receipt(tx_hash)

    return bool(tx_receipt.get("status"))


def _listen():
    global calls_made
    while True:
        try:
            _index_next_prompt()
            _answer_unanswered_prompts()
        except Exception as exc:
            print("Failed to index chain, exc:", exc)
        time.sleep(2)
        print(f"Calls made: {calls_made}")


def main():
    _listen()


if __name__ == '__main__':
    main()
