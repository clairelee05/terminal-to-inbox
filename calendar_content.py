import os
from datetime import datetime, time
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
TIMEZONE = "America/Los_Angeles"


def add_calendar_content(config):
    for item in config.get("content", []):
        if item["type"] == "calendar":
            return "Calendar content already exists."

    config["content"].append(
        {
            "type": "calendar",
            "title": "Calendar",
        }
    )

    return "Added calendar content."


def get_calendar_service():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                raise FileNotFoundError(
                    "Missing credentials.json. Download it from Google Cloud Console."
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES,
            )

            creds = flow.run_local_server(
                port=8080,
                open_browser=False,
            )

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def fetch_today_events():
    tz = ZoneInfo(TIMEZONE)
    today = datetime.now(tz).date()

    start = datetime.combine(today, time.min, tzinfo=tz)
    end = datetime.combine(today, time.max, tzinfo=tz)

    service = get_calendar_service()

    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=start.isoformat(),
            timeMax=end.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    events = events_result.get("items", [])

    return [
        event
        for event in events
        if not is_declined_event(event)
    ]


def is_declined_event(event):
    attendees = event.get("attendees", [])

    for attendee in attendees:
        if attendee.get("self") and attendee.get("responseStatus") == "declined":
            return True

    return False


def parse_event_datetime(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def format_time(dt):
    # %-I works on macOS/Linux.
    # %#I works on Windows.
    try:
        return dt.strftime("%-I:%M %p")
    except ValueError:
        return dt.strftime("%#I:%M %p")


def format_event_range(event):
    start = event["start"]
    end = event["end"]

    if "date" in start:
        return "All day"

    start_time = parse_event_datetime(start["dateTime"])
    end_time = parse_event_datetime(end["dateTime"])

    return f"{format_time(start_time)} - {format_time(end_time)}"


def get_next_event(events):
    now = datetime.now(ZoneInfo(TIMEZONE))

    timed_events = []

    for event in events:
        start = event["start"]

        if "dateTime" not in start:
            continue

        start_time = parse_event_datetime(start["dateTime"])

        if start_time >= now:
            timed_events.append(event)

    if not timed_events:
        return None

    return timed_events[0]


def get_event_location_html(event):
    location = event.get("location", "")

    if not location:
        return ""

    return f"""
        <br>
        <span style="color:#666;">📍 {location}</span>
    """


def get_calendar_html(item):
    events = fetch_today_events()
    next_event = get_next_event(events)

    html = f"""
    <div style="border:1px solid #ddd; border-radius:12px; padding:18px; margin-bottom:20px; font-family:Arial, sans-serif;">
        <h2 style="margin-top:0; margin-bottom:12px; font-size:18px;">
            📅 {item["title"]}
        </h2>
    """

    if next_event:
        next_time = format_event_range(next_event)
        next_summary = next_event.get("summary", "Untitled Event")

        html += f"""
        <div style="background:#f6f8fa; border-radius:10px; padding:12px; margin-bottom:16px;">
            <div style="font-size:13px; color:#666; margin-bottom:4px;">
                Next Up
            </div>
            <div style="font-size:14px;">
                <strong>{next_time}</strong>: {next_summary}
                {get_event_location_html(next_event)}
            </div>
        </div>
        """

    html += """
        <h3 style="font-size:15px; margin-bottom:8px;">Today's Schedule:</h3>
    """

    if not events:
        html += "<p style='font-size:13px;'>No events today.</p>"
    else:
        html += "<ul style='font-size:13px; padding-left:20px;'>"

        for event in events:
            time_range = format_event_range(event)
            summary = event.get("summary", "Untitled Event")
            location_html = get_event_location_html(event)

            html += f"""
            <li style="margin-bottom:10px;">
                <strong>{time_range}</strong>: {summary}
                {location_html}
            </li>
            """

        html += "</ul>"

    html += "</div>"

    return html