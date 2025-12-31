import datetime
import re
import threading
from typing import Dict, List, Optional, Sequence

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth import default as google_auth_default
from google.oauth2.credentials import Credentials as UserCredentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials

from .config import Settings

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


class SheetsClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._lock = threading.Lock()
        self._cached_rows: List[Dict[str, str]] = []
        self._last_fetched: Optional[datetime.datetime] = None

    @property
    def last_fetched(self) -> Optional[datetime.datetime]:
        return self._last_fetched

    def _load_credentials(self):
        if self.settings.credentials_json or self.settings.credentials_path:
            info = self.settings.google_credentials_info()
            if not info:
                raise ValueError("Google credentials could not be loaded.")
            if info.get("type") == "service_account":
                return ServiceAccountCredentials.from_service_account_info(
                    info, scopes=SCOPES
                )
            return UserCredentials.from_authorized_user_info(info, scopes=SCOPES)
        credentials, _ = google_auth_default(scopes=SCOPES)
        return credentials

    def _extract_sheet_id(self, url: str) -> str:
        match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", url)
        if not match:
            raise ValueError(f"Could not extract spreadsheet ID from URL: {url}")
        return match.group(1)

    def _normalize_header(self, header: str, index: int) -> str:
        cleaned = re.sub(r"[^\w]+", "_", header).strip("_").lower()
        if not cleaned:
            cleaned = f"column_{index + 1}"
        return cleaned

    def _normalize_rows(
        self, sheet_title: str, sheet_url: str, rows: Sequence[Sequence[str]]
    ) -> List[Dict[str, str]]:
        if not rows:
            return []
        headers = [
            self._normalize_header(header or "", idx) for idx, header in enumerate(rows[0])
        ]
        normalized_rows = []
        for row in rows[1:]:
            row_data = {headers[idx]: (value or "") for idx, value in enumerate(row)}
            row_data["source_sheet"] = sheet_title
            row_data["source_url"] = sheet_url
            normalized_rows.append(row_data)
        return normalized_rows

    def _merge_rows(self, rows: List[List[Dict[str, str]]]) -> List[Dict[str, str]]:
        merged = []
        unified_headers = set()
        for sheet_rows in rows:
            for row in sheet_rows:
                unified_headers.update(row.keys())
        for sheet_rows in rows:
            for row in sheet_rows:
                normalized_row = {header: row.get(header, "") for header in unified_headers}
                merged.append(normalized_row)
        return merged

    def _fetch_sheet_rows(self, service, sheet_url: str) -> List[Dict[str, str]]:
        spreadsheet_id = self._extract_sheet_id(sheet_url)
        spreadsheet = (
            service.spreadsheets()
            .get(spreadsheetId=spreadsheet_id, includeGridData=False)
            .execute()
        )
        sheets = spreadsheet.get("sheets", [])
        if not sheets:
            raise ValueError(f"No sheets found in spreadsheet: {sheet_url}")
        sheet_title = sheets[0]["properties"]["title"]
        value_range = self.settings.value_range or f"'{sheet_title}'"
        values_response = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=value_range)
            .execute()
        )
        rows = values_response.get("values", [])
        return self._normalize_rows(sheet_title, sheet_url, rows)

    def fetch_combined_rows(self, force: bool = False) -> List[Dict[str, str]]:
        with self._lock:
            if (
                not force
                and self._cached_rows
                and self._last_fetched
                and (
                    datetime.datetime.utcnow() - self._last_fetched
                ).total_seconds()
                < self.settings.cache_ttl_seconds
            ):
                return self._cached_rows

            if not self.settings.sheet_urls:
                raise ValueError("No sheet URLs configured.")

            credentials = self._load_credentials()
            service = build("sheets", "v4", credentials=credentials, cache_discovery=False)
            try:
                sheet_rows = [
                    self._fetch_sheet_rows(service, sheet_url)
                    for sheet_url in self.settings.sheet_urls
                ]
            except HttpError as exc:
                raise RuntimeError(f"Error fetching sheet data: {exc}") from exc

            self._cached_rows = self._merge_rows(sheet_rows)
            self._last_fetched = datetime.datetime.utcnow()
            return self._cached_rows
