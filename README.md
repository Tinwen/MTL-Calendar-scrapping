# MTL Events Importer

A Python project to extract events from the Montreal cultural events API (Algolia) and import them into Google Calendar.

## Overview

This project consists of two main components:

1. **`extract_data_from_site.py`** - Extracts cultural events from the Montreal events database via Algolia API
2. **`gcal_import.py`** - Imports the extracted events into Google Calendar with automatic calendar organization by category

## Features

- **Event Extraction**: Fetches events (playlists, stories, products) from Algolia API
- **Duplicate Prevention**: Tracks imported events by UUID to avoid re-importing
- **Smart Organization**: Creates separate Google Calendars per event category (`_permanent_identifier`)
- **Date Handling**: Supports multiple date formats and creates all-day events in Google Calendar
- **OAuth 2.0 Authentication**: Secure Google Calendar API integration with token refresh

## Prerequisites

- Python 3.7+
- Google Cloud Console project with Calendar API enabled
- OAuth 2.0 credentials file (see Setup section)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd mtl
```

2. Create a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install requests google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

## Setup

### Google Calendar API Configuration

1. **Create a project** in [Google Cloud Console](https://console.cloud.google.com/)
2. **Enable Calendar API**
3. **Create OAuth 2.0 credentials** (Desktop application)
4. **Download credentials** as JSON and save to project root as `credentials.json`

The app will handle token generation automatically on first run.

## Configuration

Edit `env.py` to configure:

```python
URL = "https://xgnqmfepvy-dsn.algolia.net/1/indexes/*/queries"
OUTPUT_FILE = "extracted_events.json"
TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/calendar"]

HEADERS = {
    "x-algolia-api-key": "your-api-key",
    "x-algolia-application-id": "your-app-id",
    # ...
}
```

## Usage

### Step 1: Extract Events

Extract events from the Algolia database:

```bash
python extract_data_from_site.py
```

This will:
- Fetch events from the Montreal events API
- Parse pagination to get all results
- Filter duplicates based on UUID
- Save to `extracted_events.json`

**Output**: JSON file with event data including title, URL, dates, and category

### Step 2: Import to Google Calendar

Import extracted events to Google Calendar:

```bash
python gcal_import.py
```

First run will prompt for Google authentication. This will:
- Create one calendar per event category (identified by `_permanent_identifier`)
- Skip already-imported events (tracked by UUID in extended properties)
- Create all-day events with event URL in description
- Save authentication token for future runs

## Data Structure

### Extracted Events (`extracted_events.json`)

```json
{
  "uuid": "event-uuid",
  "title": "Event Title",
  "_url": "https://www.mtl.org/events/event-slug",
  "_event_all_dates_first": 1234567890,
  "_event_all_dates_last": 1234567890,
  "_permanent_identifier": "category-name"
}
```

### Google Calendar Event Properties

- **Summary**: Event title
- **Description**: Link to event on MTL.org
- **Date**: All-day event (start and end dates)
- **Extended Property**: UUID and source tracking to prevent duplicates

## File Descriptions

| File | Purpose |
|------|---------|
| `extract_data_from_site.py` | Fetches and processes events from Algolia API |
| `gcal_import.py` | Authenticates with Google and imports events to Calendar |
| `env.py` | Configuration file with API keys and settings |
| `extracted_events.json` | Cache of extracted events |
| `credentials.json` | OAuth credentials (ignored by git) |
| `token.json` | OAuth access token (ignored by git) |

## Error Handling

- **API Errors**: Check Algolia credentials and network connectivity
- **Google Auth**: Delete `token.json` to re-authenticate
- **Missing Dates**: Events without valid dates are skipped with a warning
- **Duplicates**: Events already in calendar are automatically skipped

## Security Notes

- **Never commit** `credentials.json` or `token.json`
- API keys in `env.py` are public (Algolia) or project-specific (Google)
- Use `.gitignore` to exclude sensitive files

## Troubleshooting

1. **"Erreur API (400)"** - Check Algolia API key and search parameters
2. **Google authentication fails** - Delete `token.json` and re-run
3. **No events imported** - Verify `extracted_events.json` exists and contains valid data
4. **Events not showing in calendar** - Check calendar timezone (set to "America/Montreal")

## Author

Created for managing Montreal cultural events.

