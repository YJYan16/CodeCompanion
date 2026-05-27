from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    zhipu_api_key: str = ""
    chromadb_path: str = "./kb_data"
    local_model_url: str = "http://localhost:11434/api/generate"
    local_model_name: str = "qwen2.5:0.5b"
    use_local_model: bool = False
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache()
def get_settings() -> Settings:
    return Settings()