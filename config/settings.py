from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    zhipu_api_key: str = ""
    chromadb_path: str = "./kb_data"
    local_model_url: str = "http://localhost:11434/api/generate"
    local_model_name: str = "qwen2.5:7b"  # 使用Qwen2.5-7B量化模型
    use_local_model: bool = False
    
    # Redis配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    redis_enabled: bool = False  # 默认禁用Redis，避免安装要求
    redis_ttl: int = 3600
    
    # 缓存配置
    cache_namespace: str = "code_companion"
    lru_cache_maxsize: int = 1000
    lru_cache_ttl: int = 3600
    
    # 性能优化配置
    use_uvloop: bool = False  # Windows默认禁用
    use_orjson: bool = True
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache()
def get_settings() -> Settings:
    return Settings()
