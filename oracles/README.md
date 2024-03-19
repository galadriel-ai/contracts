# Galadriel Oracle

## Prerequisites

### Dependencies 
- Docker and Docker Compose (for Docker setup only)
- Python 3.11+ (for Manual setup)
- [A deployed smart contract address](https://github.com/galadriel-ai/contracts/blob/main/contracts/README.md)
- [Serper API key](https://serper.dev) - required by `web_search` tool
- [OpenAI API key](https://openai.com) - LLM inference

Ensure all necessary API keys are acquired and the Oracle smart contract is deployed. Have your private key ready for deploying the Oracle.

### Configuration

Create a `.env` file in the project root with the content updated to your values:

```plaintext
PRIVATE_KEY="[private key for oracle contract deployment]"
ORACLE_ADDRESS="[oracle smart contract address]"
OPEN_AI_API_KEY="[openai api key]"
SERPER_API_KEY="[serper api key]"
```

For more configuration parameters, see [template.env](https://github.com/galadriel-ai/contracts/blob/kresimir/oracle_readme/oracles/template.env)

## Running in Docker container

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

```python
python oracle.py
```

## Troubleshooting

Verify your API keys and network connectivity if encountering issues with Serper or OpenAI APIs. For Docker or Python setup errors, ensure all prerequisites are correctly installed.