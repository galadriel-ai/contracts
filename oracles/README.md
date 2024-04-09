# Galadriel Oracle

## Prerequisites

Before you begin, ensure you have the following prerequisites:

- **Docker and Docker Compose**: Required for the Docker setup method.
- **Python 3.11+**: Necessary for the manual setup approach.
- **A Funded Wallet and Corresponding Private Key**: Your wallet should be funded enough to cover transaction fees.
- **Deployed oracle contract address**: Make sure you have deployed the Oracle contract. For guidance, refer to the [Oracle contract deployment instructions](https://github.com/galadriel-ai/contracts/blob/main/contracts/README.md).
- **Serper API key**: Needed for the `web_search` tool. Obtain your key from [Serper](https://serper.dev).
- **OpenAI API key**: Required for Large Language Model (LLM) inference. Get your API key from [OpenAI](https://openai.com)

### Oracle smart contract and Whitelisting

Ensure that your Oracle smart contract is deployed and your wallet address is [whitelisted](https://github.com/galadriel-ai/contracts/blob/main/contracts/README.md#whitelisting-a-wallet-in-the-oracle-contract) to interact with it.


### Configuration

Create a `.env` file in the project root with the content updated to your values:

```plaintext
PRIVATE_KEY="[whitelisted wallet private key]"
ORACLE_ADDRESS="[oracle smart contract address]"
OPEN_AI_API_KEY="[openai api key]"
SERPER_API_KEY="[serper api key]"
```

For more configuration parameters, see [template.env](https://github.com/galadriel-ai/contracts/blob/main/oracles/template.env)

## Running in Docker

This setup simplifies running the oracle with Docker Compose, which requires Docker Compose installed.

1. With `.env` configured as described, start the oracle:
```shell
docker-compose up
```

## Manual setup

### 1. Install required Python libraries:
It's recommended to set up a Python virtual environment:

```shell
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2.  Running the oracle

With the virtual environment active, run:

```shell
python oracle.py
```

### Running unit tests
```
python -m pytest tests/unit
```

### Running integration tests
```
python -m pytest tests/integration
```

## Troubleshooting

Verify your API keys and network connectivity if encountering issues with Serper or OpenAI APIs. For Docker or Python setup errors, ensure all prerequisites are correctly installed.