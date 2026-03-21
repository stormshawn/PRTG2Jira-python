import json
import os
from typing import Any, Dict, List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str = "Development"
    host: str = "0.0.0.0" # A starting host
    port: int = 5000 # A starting port
    key_vault: Optional[str] = None # The value is unknown when defining, so starting at None
    allowed_ips: List[str] = ["127.0.0.1", "127.0.0.2"] # Just a dummy list to start
    instances: Dict[str, Any] = {}

    class Config:
        env_prefix = "PRTG2JIRA_"


_settings: Optional[Settings] = None # Usually defined as None
_config_data: Dict[str, Any] = {}

def load_config() -> Dict[str, Any]:
    global _config_data
    env: str = os.getenv("PRTG2JIRA_ENVIRONMENT", "development")
    config_path: str = "config/settings.json"
    env_config_path: str = f"config/settings.{env}.json"
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            _config_data = json.load(f)
    if os.path.exists(env_config_path):
        with open(env_config_path, "r") as f:
            env_config: Dict[str, Any] = json.load(f)
            _config_data.update(env_config)
    return _config_data



def get_settings()->Settings:
    global _settings
    if _settings is None:
        load_config()
        _settings = Settings(
            environment=os.getenv("PRTG2JIRA_ENVIRONMENT", "development"),
            allowed_ips=_config_data.get("AllowedIPs", ["127.0.0.1"]), 
            instances=_config_data.get("Instances", {})
        )
    return _settings

def get_config_value(key: str, default: Optional[str] = None)-> Optional[str]:
    env_key: str = f"PRTG2JIRA_{key.upper().replace('-', '_')}"
    env_value: Optional[str] = os.getenv(env_key)
    if env_value:
        return env_value
    return _config_data.get(key, default)

def get_instance_config(instance: str, key: str)->Optional[Any]:
    instance_key: str = f"{instance}-{key}"
    final_value: Optional[str] = get_config_value(instance_key)
    if final_value:
        return final_value
    if instance != "default":
        return get_config_value(f"default-{key}")
    return None