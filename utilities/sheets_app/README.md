# Sheets Aggregation Utility

Lightweight FastAPI service that merges data from multiple Google Sheets into a unified response and serves a small UI for browsing and filtering combined rows.

## Features

- Authenticates with Google Sheets via service account or OAuth client credentials.
- Fetches multiple sheets, normalizes headers, and merges rows into one schema.
- REST endpoints:
  - `GET /combined` – merged data.
  - `POST /refresh` – force a re-fetch from Google Sheets.
  - `GET /health` – health and configuration status.
- Static frontend that lists rows, shows source sheet metadata, and supports filtering.

## Prerequisites

- Python 3.11+
- Google Sheets API enabled on your Google Cloud project.
- Service account key JSON **or** OAuth client/authorized user credentials JSON with Sheets API access.

## Configuration

Environment variables:

| Variable | Description |
| --- | --- |
| `SHEETS_APP_SHEET_URLS` | Comma-separated Google Sheet URLs to read (e.g., the two provided sheet URLs). |
| `SHEETS_APP_GOOGLE_CREDENTIALS_PATH` | Path to credentials JSON on disk (optional if using JSON string). |
| `SHEETS_APP_GOOGLE_CREDENTIALS_JSON` | Raw credentials JSON string (optional if using a path). |
| `SHEETS_APP_CACHE_TTL_SECONDS` | Cache lifetime for fetched rows (default: `300`). |
| `SHEETS_APP_VALUE_RANGE` | Optional Sheets API range (defaults to the first sheet title). |

At least one of `SHEETS_APP_GOOGLE_CREDENTIALS_PATH` or `SHEETS_APP_GOOGLE_CREDENTIALS_JSON` should be provided unless you rely on Application Default Credentials.

### Obtaining credentials

1. In Google Cloud Console, enable the **Google Sheets API**.
2. Create a **service account** with the Sheets scope or download an **OAuth client/authorized user** credential JSON.
3. If using a service account, share the target sheets with the service account email.
4. Provide the credential JSON via `SHEETS_APP_GOOGLE_CREDENTIALS_PATH` or `SHEETS_APP_GOOGLE_CREDENTIALS_JSON`.

## Installation

```bash
cd utilities/sheets_app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the service

```bash
export SHEETS_APP_SHEET_URLS="https://docs.google.com/spreadsheets/d/<id1>,https://docs.google.com/spreadsheets/d/<id2>"
export SHEETS_APP_GOOGLE_CREDENTIALS_PATH="/path/to/credentials.json"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000` to use the UI. The static assets are available under `/public`.

## API contract

- `GET /combined` → `200 OK` with JSON array of merged rows. Each row includes normalized column keys plus `source_sheet` and `source_url`.
- `POST /refresh` → `202 Accepted` and forces a refetch. Returns `{ status, rows, last_fetched }`.
- `GET /health` → `200 OK` with `{ status, last_fetched, configured_sheets }`.

Errors return JSON with a `detail` field and appropriate HTTP status codes (`400` for configuration issues, `502` for upstream errors).

## Docker (optional)

Build and run with:

```bash
docker build -t sheets-app .
docker run --rm -p 8000:8000 \
  -e SHEETS_APP_SHEET_URLS="https://docs.google.com/spreadsheets/d/<id1>,https://docs.google.com/spreadsheets/d/<id2>" \
  -e SHEETS_APP_GOOGLE_CREDENTIALS_JSON="$(cat /path/to/credentials.json)" \
  sheets-app
```

## Make targets (optional)

```bash
make install   # create venv and install deps
make serve     # run uvicorn in reload mode
```
