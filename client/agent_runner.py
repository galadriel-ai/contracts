import json
import os
import time

from termcolor import cprint
from web3 import Web3

import settings

os.environ["FORCE_COLOR"] = "1"

web3_client = Web3(Web3.HTTPProvider(settings.WEB3_RPC_URL))
account = web3_client.eth.account.from_key(settings.PRIVATE_KEY)
with open(settings.AGENT_ABI_PATH, "r", encoding="utf-8") as f:
    agent_abi = json.loads(f.read())["abi"]
contract = web3_client.eth.contract(address=settings.AGENT_ADDRESS, abi=agent_abi)


def main() -> None:
    prompt = "You are a helpfup assistant!\nUser: Hello\nGive a very brief history of Estonia (max 20 words per response): \nAssistant: "
    iteration_count = 3

    cprint("=============== Agent run started ===============", "yellow")
    start = time.time()

    tx_data = {
        "gas": 500000,
        "maxFeePerGas": web3_client.to_wei("2", "gwei"),
        "maxPriorityFeePerGas": web3_client.to_wei("1", "gwei"),
        "nonce": web3_client.eth.get_transaction_count(account.address),
    }
    if chain_id := settings.CHAIN_ID:
        tx_data["chainId"] = int(chain_id)
    tx = contract.functions.runAgent(
        prompt, 3
    ).build_transaction(tx_data)
    signed_tx = web3_client.eth.account.sign_transaction(
        tx, private_key=account.key)

    tx_hash = web3_client.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = web3_client.eth.wait_for_transaction_receipt(tx_hash)
    if not bool(tx_receipt.get("status")):
        raise Exception("Failed to create runAgent transaction")

    # Rest of it is just printing results :)

    run_id = _get_run_id(tx_receipt)

    i = 0
    while True:
        time.sleep(5)
        try:
            prompts = contract.functions.getPrompts(run_id).call()
            responses = contract.functions.getResponses(run_id).call()

            for j in range(len(responses)):
                if i <= j:
                    cprint(f"prompt[{j}]", "yellow")
                    cprint(prompts[j], "green")
                    cprint(f"response[{j}]", "yellow")
                    cprint(responses[j], "green")
                    i = i + 1

            if i >= iteration_count - 1:
                run = contract.functions.agentRuns(run_id).call()
                if run[3]:  # run[3] is is_finished field, according to ABI
                    break
        except:
            pass

    cprint("=============== Agent run final result ===============", "yellow")
    cprint(prompts[len(prompts) - 1], "blue")
    cprint(f"Time elapsed: {time.time() - start}, with {iteration_count} iterations.", "light_red")


def _get_run_id(tx_receipt) -> int:
    event_signature_hash = Web3.keccak(text="AgentRunCreated(uint256)").hex()
    for log in tx_receipt.logs:
        if log['topics'][0].hex() == event_signature_hash:
            # Not the best way to decode this data..
            run_id = int(tx_receipt.logs[1].topics[1].hex(), 0)
            cprint(f"Agent Run ID: {run_id}", "yellow")
            return run_id

    raise Exception(f"Failed to get run ID")


if __name__ == '__main__':
    main()
