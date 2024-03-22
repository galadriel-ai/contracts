from dotenv import load_dotenv
import os

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
SERVE_METRICS = os.getenv("SERVE_METRICS", "False").lower() == "true"

OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

CHAIN_ID = os.getenv("CHAIN_ID", "696969")
WEB3_RPC_URL = os.getenv("WEB3_RPC_URL", "https://testnet.galadriel.com")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
ORACLE_ADDRESS = os.getenv("ORACLE_ADDRESS")
ORACLE_ABI_PATH = os.getenv("ORACLE_ABI_PATH", "abi/ChatOracle.json")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "galadriel-assets")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
