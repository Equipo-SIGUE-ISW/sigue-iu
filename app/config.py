import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class AppConfig:
    api_base_url: str = os.getenv("API_BASE_URL", "http://140.84.169.148:25630")

CONFIG = AppConfig()
