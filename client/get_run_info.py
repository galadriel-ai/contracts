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


def main():
    run_id = 0
    prompts = contract.functions.getPrompts(run_id).call()
    responses = contract.functions.getResponses(run_id).call()
    cprint("prompts", "yellow")
    cprint(prompts, "green")
    cprint("responses", "yellow")
    cprint(responses, "green")


if __name__ == '__main__':
    main()
