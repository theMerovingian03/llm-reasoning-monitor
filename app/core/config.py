from dotenv import load_dotenv
from os import getenv as os_getenv

load_dotenv()

# Deepseek (Target LLM)
TARGET_MODEL_URL = os_getenv("TARGET_MODEL_URL", "")
TARGET_MODEL_PATH = os_getenv("TARGET_MODEL_PATH", "")

# Phi3 (Monitor LLM)
MONITOR_MODEL_URL = os_getenv("MONITOR_MODEL_URL", "")
MONITOR_MODEL_PATH = os_getenv("MONITOR_MODEL_PATH", "")

# PORT for main server
MAIN_PORT = int(os_getenv("MAIN_PORT", 8003))