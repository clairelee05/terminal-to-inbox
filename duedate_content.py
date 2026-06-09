import os
from datetime import date, datetime, timedelta

import requests


def add_duedate_content(config):
    for item in config.get("content", []):
        if item["type"] == "duedate":
            return "Due date content already exists."

    config["content"].append(
        {
            "type": "duedate",
            "title": "Assignments",
        }
    )

    return "Added due date content: Assignments"


def get_sunday_of_current_week(today):
    days_until_sunday = 6 - today.weekday()
    return today + timedelta(days=days_until_sunday)

def format_day_name(date_string):
    due_date = datetime.fromisoformat(date_string).date()
    return due_date.strftime("%A")

def get_date_only(date_string):
    return date_string.split("T")[0]

def is_complete(status):
    return status.strip().lower() == "done"


def get_text_from_property(prop):
    prop_type = prop.get("type")

    if prop_type == "title":
        return "".join(part["plain_text"] for part in prop["title"])

    if prop_type == "rich_text":
        return "".join(part["plain_text"] for part in prop["rich_text"])

    if prop_type == "select":
        return prop["select"]["name"] if prop["select"] else ""

    if prop_type == "status":
        return prop["status"]["name"] if prop["status"] else ""

    return ""

def format_assignment_line(assignment):
    line = f"<strong>{assignment['course']}</strong>: {assignment['name']}"

    if assignment.get("notes"):
        line += f" ({assignment['notes']})"

    return line


def fetch_notion_due_dates():
    token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_DUEDATE_DATABASE_ID")

    if not token:
        raise ValueError("Missing NOTION_TOKEN in .env")

    if not database_id:
        raise ValueError("Missing NOTION_DUEDATE_DATABASE_ID in .env")

    today = date.today()
    sunday = get_sunday_of_current_week(today)

    url = f"https://api.notion.com/v1/databases/{database_id}/query"

    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }

    payload = {
        "filter": {
            "and": [
                {
                    "property": "Due",
                    "date": {"on_or_after": today.isoformat()},
                },
                {
                    "property": "Due",
                    "date": {"on_or_before": sunday.isoformat()},
                },
            ]
        },
        "sorts": [
            {
                "property": "Due",
                "direction": "ascending",
            }
        ],
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    assignments = []

    for page in response.json()["results"]:
        properties = page["properties"]

        status = ""
        if "Status" in properties:
            status = get_text_from_property(properties["Status"])

        if is_complete(status):
            continue

        course = get_text_from_property(properties["Course"])
        name = get_text_from_property(properties["Name"])
        due_date = get_date_only(properties["Due"]["date"]["start"])

        notes = ""
        if "Notes" in properties:
            notes = get_text_from_property(properties["Notes"])

        assignments.append(
            {
                "course": course,
                "name": name,
                "due_date": due_date,
                "notes": notes,
                "status": status,
            }
        )

    return assignments


def get_duedate_html(item):
    today = date.today().isoformat()
    assignments = fetch_notion_due_dates()

    due_today = [
        assignment for assignment in assignments if assignment["due_date"] == today
    ]

    due_this_week = [
        assignment for assignment in assignments if assignment["due_date"] != today
    ]

    html = f"""
    <div style="border:1px solid #ddd; border-radius:12px; padding:18px; margin-bottom:20px; font-family:Arial, sans-serif;">
        <h2 style="margin-top:0; margin-bottom:12px; font-size:18px;">
            📝{item["title"]}
        </h2>

        <h3 style="font-size:15px; margin-bottom:8px;">Due Today:</h3>
    """

    if due_today:
        html += "<ul style='font-size:13px;'>"
        for assignment in due_today:
            html += f"""
            <li>
                {format_assignment_line(assignment)}
            </li>
            """
        html += "</ul>"
    else:
        html += "<p style='font-size:13px;'>Nothing due today.</p>"

    html += """
        <h3 style="font-size:15px; margin-top:18px; margin-bottom:8px;">Due This Week:</h3>
    """

    if due_this_week:
        grouped = {}

        for assignment in due_this_week:
            grouped.setdefault(assignment["due_date"], []).append(assignment)

        for due_date, items in grouped.items():
            html += f"""
            <p style="font-size:13px; margin-bottom:4px;"><strong>{format_day_name(due_date)}:</strong></p>
            <ul style="font-size:13px;">
            """

            for assignment in items:
                html += f"""
                <li>
                    {format_assignment_line(assignment)}
                </li>
                """

            html += "</ul>"
    else:
        html += "<p style='font-size:13px;'>Nothing else due this week.</p>"

    html += "</div>"

    return html
