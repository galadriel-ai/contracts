from dotenv import load_dotenv
import os

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "local")

OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")

CHAIN_ID = os.getenv("CHAIN_ID")
WEB3_RPC_URL = os.getenv("WEB3_RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
ORACLE_ADDRESS = os.getenv("ORACLE_ADDRESS")
ORACLE_ABI_PATH = os.getenv("ORACLE_ABI_PATH")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "galadriel-assets")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
