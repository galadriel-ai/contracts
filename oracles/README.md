# Galadriel Oracle

## Environment setup

### 1. Prerequisites

- Python 3.11+
- A [deployed smart contract address](https://github.com/galadriel-ai/contracts/blob/main/contracts/README.md)
- [Serper API key](https://serper.dev) - required by `web_search` tool
- [OpenAI API key](https://openai.com) - LLM inference

Ensure you have Python installed and Oracle smart contract deployed. 
The Oracle also relies on the Serper and OpenAI API for functionality.

### 2. Install required Python libraries:

```shell
pip install -r requirements.
```

### 3. Create a `.env` file in the project root with the following content, updated with your values:

```plaintext
PRIVATE_KEY="0xxxxx"
ORACLE_ADDRESS="0x5FbDB2315678afecb367f032d93F642f64180aa3"
OPEN_AI_API_KEY="sk-xxxxxxx"
SERPER_API_KEY="xxxx"
```

## Running the oracle

To run the oracle, execute:

```python
python oracle.py
```

## Troubleshooting

If you encounter any issues with the serper or OpenAI APIs, verify your API keys and network connectivity.
Ensure the smart contract address is correctly entered in the .env file.
