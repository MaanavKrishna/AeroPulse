"""Runtime settings, read from the environment (or a local .env file).

Secrets only ever come from here. Nothing secret is committed; see .env.example.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_DIR = PACKAGE_DIR.parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="AEROPULSE_",
                                      extra="ignore")

    #: "development" allows the demo provider. "production" refuses to start with it.
    env: str = "development"
    database_url: str = f"sqlite:///{REPO_DIR / 'aeropulse.db'}"
    site_url: str = "http://localhost:8000"

    #: Comma-separated provider names to collect from, in priority order.
    providers: str = "ignav"
    basket_path: Path = REPO_DIR / "basket.yaml"
    festivals_path: Path = REPO_DIR / "data" / "festivals.yaml"
    export_dir: Path = REPO_DIR / "exports"

    #: Hard cap per provider per day. Collection stops at the cap and says so in the run log.
    max_calls_per_day: int = 200
    http_timeout: float = 30.0
    #: Lets production collect from a provider whose terms are not yet marked reviewed.
    #: For a private trial only; the site shows a notice while it is on.
    allow_unreviewed_terms: bool = False

    ignav_api_key: SecretStr | None = None
    travelpayouts_token: SecretStr | None = None

    #: Required for /v1/admin/*. If unset, admin endpoints are disabled.
    admin_token: SecretStr | None = None
    #: Requests per minute per client IP on the public API.
    rate_limit: int = 120

    @field_validator("env")
    @classmethod
    def _env(cls, v: str) -> str:
        v = v.lower()
        if v not in {"development", "production", "test"}:
            raise ValueError("AEROPULSE_ENV must be development, production or test")
        return v

    @property
    def provider_list(self) -> list[str]:
        return [p.strip().lower() for p in self.providers.split(",") if p.strip()]

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    def check(self) -> None:
        """Refuse configurations that would publish something untrue."""
        if self.is_production and "demo" in self.provider_list:
            raise RuntimeError(
                "The demo provider generates synthetic fares and cannot run in production. "
                "Remove 'demo' from AEROPULSE_PROVIDERS or set AEROPULSE_ENV=development.")


@lru_cache
def get_settings() -> Settings:
    return Settings()
