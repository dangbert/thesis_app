"""
All application settings are defined here.

Usage:

from app.settings import settings

Settings are loaded from environment variables upon import! So any
changes in environment variables should be done before import (e.g.
load_dotenv).
"""

import os
from pathlib import Path
from typing import Literal, Optional

import dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.dirname(SCRIPT_DIR)


class Settings(BaseSettings):
    # https://docs.pydantic.dev/latest/concepts/pydantic_settings/
    # model_config = SettingsConfigDict(env_file="test.env", extra="ignore")
    model_config = SettingsConfigDict()
    env: Literal["TEST", "DEV", "PRD"]
    api_v1_str: str = "/api/v1"

    # files
    file_dir: Path = Path("/files")

    # session management
    secret_key: str
    session_expiration_secs: int = 60 * 60 * 24 * 7

    # https://docs.python.org/3/library/logging.html#levels
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # database
    db_pass: str
    db_user: str = "postgres"  # TODO for now
    db_name: str = "thesis"
    db_host: str = "db"
    db_port: int = 5432
    auto_migrate: bool = True  # auto migrate database on startup

    # auth0
    auth0_domain: str
    auth0_client_id: str
    auth0_client_secret: str

    @property
    def db_uri(self):
        return self._db_uri(omit_pass=False)

    @property
    def db_uri_print_safe(self):
        return self._db_uri(omit_pass=True)

    def _db_uri(self, omit_pass: bool, include_db_name: bool = True) -> str:
        password = "********" if omit_pass else self.db_pass
        base_uri = (
            f"postgresql://{self.db_user}:{password}@{self.db_host}:{self.db_port}"
        )
        return f"{base_uri}/{self.db_name}" if include_db_name else base_uri


def get_settings() -> Settings:
    return Settings()  # type: ignore [call-arg]
