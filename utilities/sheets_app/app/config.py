import json
import os
from dataclasses import dataclass, field
from typing import List, Optional


def _parse_list(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass
class Settings:
    sheet_urls: List[str] = field(default_factory=list)
    credentials_path: Optional[str] = None
    credentials_json: Optional[str] = None
    cache_ttl_seconds: int = 300
    value_range: Optional[str] = None

    @classmethod
    def from_env(cls) -> "Settings":
        env_sheet_urls = _parse_list(os.getenv("SHEETS_APP_SHEET_URLS"))
        return cls(
            sheet_urls=env_sheet_urls,
            credentials_path=os.getenv("SHEETS_APP_GOOGLE_CREDENTIALS_PATH"),
            credentials_json=os.getenv("SHEETS_APP_GOOGLE_CREDENTIALS_JSON"),
            cache_ttl_seconds=int(os.getenv("SHEETS_APP_CACHE_TTL_SECONDS", "300")),
            value_range=os.getenv("SHEETS_APP_VALUE_RANGE"),
        )

    def google_credentials_info(self) -> Optional[dict]:
        """
        Return credential JSON as a dictionary, loaded from either the JSON env var
        or a path on disk.
        """
        if self.credentials_json:
            return json.loads(self.credentials_json)
        if self.credentials_path and os.path.exists(self.credentials_path):
            with open(self.credentials_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
