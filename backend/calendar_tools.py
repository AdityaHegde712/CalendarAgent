import os
import json
from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from googleapiclient.discovery import build
from langchain_core.tools import tool

from config import SCOPES, GOOGLE_CREDENTIALS_FILE, GOOGLE_TOKEN_FILE

# Holds a pending OAuth flow waiting for the user to paste a code
_pending_flow: Flow | None = None


def _token_file_is_valid() -> bool:
    """Return True only if token path exists AND is a file (not a dir)."""
    return os.path.isfile(GOOGLE_TOKEN_FILE)


def _save_token(creds: Credentials) -> None:
    """Write credentials to token file, removing any stale directory first."""
    if os.path.isdir(GOOGLE_TOKEN_FILE):
        import shutil
        shutil.rmtree(GOOGLE_TOKEN_FILE)
    with open(GOOGLE_TOKEN_FILE, "w") as f:
        f.write(creds.to_json())


def get_auth_url() -> str | None:
    """
    If not yet authenticated, start an OAuth flow and return the URL the user
    must visit. Returns None if already authenticated.
    """
    global _pending_flow

    if _token_file_is_valid():
        creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_FILE, SCOPES)
        if creds and creds.valid:
            return None
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            _save_token(creds)
            return None

    if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
        raise FileNotFoundError(
            f"Google credentials file not found at '{GOOGLE_CREDENTIALS_FILE}'. "
            "Please follow the README to set up Google Calendar API."
        )

    _pending_flow = InstalledAppFlow.from_client_secrets_file(
        GOOGLE_CREDENTIALS_FILE,
        SCOPES,
        redirect_uri="urn:ietf:wg:oauth:2.0:oob",  # console / copy-paste flow
    )
    auth_url, _ = _pending_flow.authorization_url(prompt="consent")
    return auth_url


def complete_auth(code: str) -> None:
    """Exchange the auth code the user pasted for a token and save it."""
    global _pending_flow
    if _pending_flow is None:
        raise RuntimeError("No pending OAuth flow. Call get_auth_url() first.")
    _pending_flow.fetch_token(code=code.strip())
    _save_token(_pending_flow.credentials)
    _pending_flow = None


def get_calendar_service():
    """Return an authenticated Google Calendar service, or raise if not authed."""
    if not _token_file_is_valid():
        raise PermissionError(
            "Not authenticated with Google Calendar. "
            "Please complete the OAuth flow via the /auth endpoints."
        )

    creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            _save_token(creds)
        else:
            raise PermissionError(
                "Google Calendar token is invalid or expired. "
                "Please re-authenticate via the /auth endpoints."
            )

    return build("calendar", "v3", credentials=creds)


def get_user_timezone() -> str:
    """Fetch the user's timezone from their Google Calendar settings."""
    try:
        service = get_calendar_service()
        settings = service.settings().get(setting="timezone").execute()
        return settings.get("value", "UTC")
    except Exception:
        return "UTC"


@tool
def list_events(start_date: str, end_date: str) -> str:
    """
    List all calendar events between start_date and end_date.
    Dates should be in ISO 8601 format: YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD.
    Returns a JSON string of events with their start/end times and summaries.
    """
    try:
        service = get_calendar_service()
        user_tz = get_user_timezone()
        tz = ZoneInfo(user_tz)

        # Normalize dates to full datetime with timezone
        if "T" not in start_date:
            start_date = f"{start_date}T00:00:00"
        if "T" not in end_date:
            end_date = f"{end_date}T23:59:59"

        start_dt = datetime.fromisoformat(start_date).replace(tzinfo=tz)
        end_dt = datetime.fromisoformat(end_date).replace(tzinfo=tz)

        events_result = service.events().list(
            calendarId="primary",
            timeMin=start_dt.isoformat(),
            timeMax=end_dt.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = events_result.get("items", [])
        simplified = []
        for e in events:
            start = e["start"].get("dateTime", e["start"].get("date"))
            end = e["end"].get("dateTime", e["end"].get("date"))
            simplified.append({
                "id": e["id"],
                "summary": e.get("summary", "(No title)"),
                "start": start,
                "end": end,
                "description": e.get("description", ""),
            })

        return json.dumps({"events": simplified, "timezone": user_tz})
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_free_slots(start_date: str, end_date: str, duration_minutes: int, work_hours_start: int = 9, work_hours_end: int = 21) -> str:
    """
    Find free time slots between start_date and end_date that fit duration_minutes.
    Only considers slots within work_hours_start to work_hours_end (24h format).
    Dates should be YYYY-MM-DD format.
    Returns a list of available slots.
    """
    try:
        service = get_calendar_service()
        user_tz = get_user_timezone()
        tz = ZoneInfo(user_tz)

        start_dt = datetime.fromisoformat(f"{start_date}T00:00:00").replace(tzinfo=tz)
        end_dt = datetime.fromisoformat(f"{end_date}T23:59:59").replace(tzinfo=tz)

        events_result = service.events().list(
            calendarId="primary",
            timeMin=start_dt.isoformat(),
            timeMax=end_dt.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = events_result.get("items", [])
        busy_slots = []
        for e in events:
            s = e["start"].get("dateTime")
            en = e["end"].get("dateTime")
            if s and en:
                busy_slots.append((
                    datetime.fromisoformat(s).astimezone(tz),
                    datetime.fromisoformat(en).astimezone(tz),
                ))

        # Walk day by day and find free slots
        free_slots = []
        current_day = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        now = datetime.now(tz=tz)

        while current_day.date() <= end_dt.date():
            day_start = current_day.replace(hour=work_hours_start, minute=0, second=0)
            day_end = current_day.replace(hour=work_hours_end, minute=0, second=0)

            # Don't suggest past slots
            if day_end < now:
                current_day += timedelta(days=1)
                continue
            if day_start < now:
                day_start = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

            # Collect busy periods for this day
            day_busy = sorted([
                (max(s, day_start), min(e, day_end))
                for s, e in busy_slots
                if s < day_end and e > day_start
            ])

            # Find gaps
            cursor = day_start
            for busy_start, busy_end in day_busy:
                if cursor + timedelta(minutes=duration_minutes) <= busy_start:
                    free_slots.append({
                        "start": cursor.isoformat(),
                        "end": busy_start.isoformat(),
                        "available_minutes": int((busy_start - cursor).total_seconds() / 60),
                    })
                cursor = max(cursor, busy_end)

            if cursor + timedelta(minutes=duration_minutes) <= day_end:
                free_slots.append({
                    "start": cursor.isoformat(),
                    "end": day_end.isoformat(),
                    "available_minutes": int((day_end - cursor).total_seconds() / 60),
                })

            current_day += timedelta(days=1)

        return json.dumps({"free_slots": free_slots, "timezone": user_tz, "duration_needed_minutes": duration_minutes})
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def create_calendar_events(events_json: str) -> str:
    """
    Create one or more calendar events. 
    events_json should be a JSON string with a list of events, each having:
    - summary: event title
    - start: ISO 8601 datetime string (e.g. 2024-11-15T10:00:00)
    - end: ISO 8601 datetime string
    - description: optional event description
    - timezone: IANA timezone string (e.g. America/Los_Angeles)
    Example: {"events": [{"summary": "Study session", "start": "2024-11-15T10:00:00", "end": "2024-11-15T12:00:00", "description": "Task ABC", "timezone": "America/Los_Angeles"}]}
    """
    try:
        service = get_calendar_service()
        data = json.loads(events_json)
        events_to_create = data.get("events", [])
        created = []

        for ev in events_to_create:
            tz = ev.get("timezone", "UTC")
            event_body = {
                "summary": ev["summary"],
                "description": ev.get("description", ""),
                "start": {"dateTime": ev["start"], "timeZone": tz},
                "end": {"dateTime": ev["end"], "timeZone": tz},
            }
            result = service.events().insert(calendarId="primary", body=event_body).execute()
            created.append({
                "id": result["id"],
                "summary": result["summary"],
                "start": result["start"]["dateTime"],
                "end": result["end"]["dateTime"],
                "link": result.get("htmlLink", ""),
            })

        return json.dumps({"created_events": created, "count": len(created)})
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_current_datetime() -> str:
    """Returns the current date and time with timezone info. Always call this first to know today's date."""
    user_tz = get_user_timezone()
    tz = ZoneInfo(user_tz)
    now = datetime.now(tz=tz)
    return json.dumps({
        "current_datetime": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
        "day_of_week": now.strftime("%A"),
        "timezone": user_tz,
    })


CALENDAR_TOOLS = [get_current_datetime, list_events, get_free_slots, create_calendar_events]
