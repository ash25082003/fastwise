#config/settings.py
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class DatabaseConfig:
    uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username: str = os.getenv("NEO4J_USER", "neo4j")
    password: str = os.getenv("NEO4J_PASSWORD", "password")

@dataclass
class AppConfig:
    data_file_path: str = os.getenv("DATA_FILE", "data/questions.json")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    max_recommendations: int = int(os.getenv("MAX_RECOMMENDATIONS", "20"))

# Global config instances
db_config = DatabaseConfig()
app_config = AppConfig()