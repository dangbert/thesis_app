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
import config
from pydantic_settings import BaseSettings, SettingsConfigDict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.dirname(SCRIPT_DIR)

logger = config.get_logger(__name__)


class Settings(BaseSettings):
    # https://docs.pydantic.dev/latest/concepts/pydantic_settings/
    # model_config = SettingsConfigDict(env_file="test.env", extra="ignore")
    model_config = SettingsConfigDict()
    env: Literal["TEST", "DEV", "PRD"]

    @property
    def is_production(self) -> bool:
        return self.env == "PRD"

    api_v1_str: str = "/api/v1"
    server_name: str  # e.g. "http://localhost:8000" or "example.com"
    support_email: Optional[str] = None  # to include in email alerts

    # only allow user signups with a valid invite code
    invite_only_signup: bool = True

    @property
    def site_url(self):
        if self.server_name.startswith("http"):
            if not self.server_name.startswith("https://") and self.env == "PRD":
                logger.warning(f"server_name '{self.server_name}' is not https")
            return self.server_name
        return f"https://{self.server_name}"

    # files
    file_dir: Path = Path("/files")

    # session management
    secret_key: str
    session_expiration_secs: int = 60 * 60 * 24 * 14

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
    # auth0 connection type to use for login
    auth0_connection: Literal["google-oauth2", "email"] = "google-oauth2"

    # OpenAI
    openai_api_key: str
    gpt_model: str
    gpt_temperature: float = 0.5
    gpt_max_tokens: int = 1000

    # AWS
    aws_region: str

    # email to send notifications from (should match terraform/instances/common/main.tf:from_email)
    #   omit to disable sending emails
    email_from: Optional[str] = None
    support_email: Optional[str] = None  # email to send support emails to

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
