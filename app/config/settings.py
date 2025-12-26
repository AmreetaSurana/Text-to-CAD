from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"

JSON_DIR = DATA_DIR / "json"
CADQUERY_DIR = DATA_DIR / "cadquery"
STL_DIR = DATA_DIR / "stl"

for d in [JSON_DIR, CADQUERY_DIR, STL_DIR]:
    d.mkdir(parents=True, exist_ok=True)

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")

print(AZURE_OPENAI_API_VERSION)