# config.py
import os
from functools import lru_cache
from pathlib import Path
import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine


# Function to load yaml file
def load_yaml_config(file_path: Path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Expand environment variables in the YAML content
    content = os.path.expandvars(content)
    return yaml.safe_load(content)

# Define the Pydantic models for nested configurations
class DatabaseSettings(BaseSettings):
    host: str
    port: int
    driver: str
    database: str
    user: str
    password: str
    # mysql+pymysql://user:password@localhost:3306/dbname



class AppSettings(BaseSettings):
    SOCAT_VERSION: str
    dsg_file_dir: str
    dec_dsg_file_dir: str
    database: DatabaseSettings

    # Allows pydantic to pick up values from a dictionary
    # instead of just environment variables
    model_config = SettingsConfigDict(env_nested_delimiter='__')

yaml_config = load_yaml_config(Path(__file__).parent / "config.yaml")
settings = AppSettings(**yaml_config)


# Removed the get_settings() call as it is not defined in the snippet.
engine = create_engine(f"{settings.database.driver}://{settings.database.user}:{settings.database.password}@{settings.database.host}:{settings.database.port}/{settings.database.database}")


