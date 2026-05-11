"""
Import extracted_events.json into Google Calendar.
- One calendar per _permanent_identifier
- Event title, start/end date, URL in description
"""

import json
import os
from collections import defaultdict
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from env import TOKEN_FILE, SCOPES, CREDENTIALS_FILE, OUTPUT_FILE


def get_calendar_service():
    """Authenticate and return the Google Calendar service."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)


def find_or_create_calendar(service, summary, existing_calendars):
    """Return calendar ID, creating it if needed."""
    if summary in existing_calendars:
        return existing_calendars[summary]

    calendar_body = {"summary": summary, "timeZone": "America/Montreal"}
    created = service.calendars().insert(body=calendar_body).execute()
    cal_id = created["id"]
    existing_calendars[summary] = cal_id
    print(f"  Calendrier créé : {summary}")
    return cal_id


def get_existing_calendars(service):
    """Fetch all calendars the user owns, return {summary: id}."""
    calendars = {}
    page_token = None
    while True:
        result = service.calendarList().list(pageToken=page_token).execute()
        for cal in result.get("items", []):
            calendars[cal["summary"]] = cal["id"]
        page_token = result.get("nextPageToken")
        if not page_token:
            break
    return calendars


def get_existing_event_ids(service, calendar_id):
    """Fetch all event extendedProperties private 'uuid' in a calendar."""
    uuids = set()
    page_token = None
    while True:
        result = service.events().list(
            calendarId=calendar_id,
            privateExtendedProperty="source=mtl_import",
            maxResults=2500,
            pageToken=page_token,
        ).execute()
        for ev in result.get("items", []):
            props = ev.get("extendedProperties", {}).get("private", {})
            if "uuid" in props:
                uuids.add(props["uuid"])
        page_token = result.get("nextPageToken")
        if not page_token:
            break
    return uuids


def parse_date(value):
    """Parse a date value (unix timestamp or string) to YYYY-MM-DD."""
    if not value and value != 0:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value).strftime("%Y-%m-%d")
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(value).split("+")[0].split("Z")[0], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return str(value)[:10]


def main():
    # Load events
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        events = json.load(f)

    # Group by _permanent_identifier
    groups = defaultdict(list)
    for ev in events:
        key = ev.get("_permanent_identifier") or "MTL – Sans catégorie"
        groups[key].append(ev)

    print(f"{len(events)} événements répartis dans {len(groups)} calendrier(s)\n")

    service = get_calendar_service()
    existing_calendars = get_existing_calendars(service)

    total_created = 0
    total_skipped = 0

    for identifier, group_events in groups.items():
        cal_name = f"MTL – {identifier}"
        cal_id = find_or_create_calendar(service, cal_name, existing_calendars)

        # Get already-imported UUIDs to avoid duplicates
        imported_uuids = get_existing_event_ids(service, cal_id)

        created = 0
        skipped = 0
        print(f"Importation dans '{cal_name}' ({len(group_events)} événements) :")
        for ev in group_events:
            uuid = ev.get("uuid")
            if uuid in imported_uuids:
                skipped += 1
                print(f"  - {ev.get('title', 'Sans titre')} (UUID: {uuid}) déjà présent, ignoré")
                continue
            print(f"  - {ev.get('title', 'Sans titre')} (UUID: {uuid})")
            start = parse_date(ev.get("_event_all_dates_first"))
            end = parse_date(ev.get("_event_all_dates_last"))
            if not start:
                skipped += 1
                print(f"    Ignoré (pas de date valide)")
                continue

            event_body = {
                "summary": ev.get("title", "Sans titre"),
                "description": ev.get("_url", ""),
                "start": {"date": start},
                "end": {"date": end or start},
                "extendedProperties": {
                    "private": {
                        "uuid": uuid or "",
                        "source": "mtl_import",
                    }
                },
            }

            service.events().insert(calendarId=cal_id, body=event_body).execute()
            created += 1

        total_created += created
        total_skipped += skipped
        print(f"  [{cal_name}] {created} créés, {skipped} ignorés (déjà présents ou sans date)")

    print(f"\nTerminé : {total_created} événements créés, {total_skipped} ignorés.")


if __name__ == "__main__":
    main()
