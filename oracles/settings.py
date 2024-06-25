from dotenv import load_dotenv
import os

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "local")

OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

SERPER_API_KEY = os.getenv("SERPER_API_KEY")

CHAIN_ID = os.getenv("CHAIN_ID", "696969")
WEB3_RPC_URL = os.getenv("WEB3_RPC_URL", "https://devnet.galadriel.com")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
ORACLE_ADDRESS = os.getenv("ORACLE_ADDRESS")
ORACLE_ABI_PATH = os.getenv("ORACLE_ABI_PATH", "abi/ChatOracle.json")

GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "galadriel-assets")
SERVE_METRICS = os.getenv("SERVE_METRICS", "False").lower() == "true"
E2B_API_KEY = os.getenv("E2B_API_KEY")
PINATA_API_JWT = os.getenv("PINATA_API_JWT")
PINATA_GATEWAY_TOKEN = os.getenv("PINATA_GATEWAY_TOKEN")

KNOWLEDGE_BASE_MAX_SIZE_BYTES = int(
    os.getenv("KNOWLEDGE_BASE_MAX_SIZE_BYTES", 10485760)
)
KNOWLEDGE_BASE_CACHE_MAX_SIZE = int(os.getenv("KNOWLEDGE_BASE_CACHE_MAX_SIZE", 100))
