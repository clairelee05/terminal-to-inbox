import os
from datetime import date, timedelta

import requests


def add_todo_content(config):
    for item in config.get("content", []):
        if item["type"] == "todo":
            return "To Do content already exists."

    config["content"].append(
        {
            "type": "todo",
            "title": "To Do",
        }
    )

    return "Added To Do content."


def get_today_day_name():
    return date.today().strftime("%A")


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


def is_active_status(status):
    return status.strip().lower() in {
        "to do",
        "todo",
        "in progress",
    }


def fetch_today_todos():
    token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_TODO_DATABASE_ID")

    if not token:
        raise ValueError("Missing NOTION_TOKEN in .env")

    if not database_id:
        raise ValueError("Missing NOTION_TODO_DATABASE_ID in .env")

    today_day = get_today_day_name()

    url = f"https://api.notion.com/v1/databases/{database_id}/query"

    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }

    payload = {
        "filter": {
            "property": "Day of the Week",
            "select": {
                "equals": today_day,
            },
        },
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        print(response.status_code)
        print(response.text)

    response.raise_for_status()

    todos = []

    for page in response.json()["results"]:
        properties = page["properties"]

        name = get_text_from_property(properties["Task"])
        status = get_text_from_property(properties["Status"])

        notes = ""
        if "Notes" in properties:
            notes = get_text_from_property(properties["Notes"])

        # Skip rows that are effectively empty
        if not name.strip() and not notes.strip():
            continue

        if not is_active_status(status):
            continue

        todos.append(
            {
                "name": name,
                "notes": notes,
                "status": status,
            }
        )

    return todos


def get_todo_html(item):
    todos = fetch_today_todos()

    html = f"""
    <div style="border:1px solid #ddd; border-radius:12px; padding:18px; margin-bottom:20px; font-family:Arial, sans-serif;">
        <h2 style="margin-top:0; margin-bottom:12px; font-size:18px;">
            ✅ {item.get("title", "To Do")}
        </h2>
    """

    if not todos:
        html += "<p style='font-size:13px;'>Nothing to do today.</p>"
    else:
        html += "<ul style='font-size:13px; padding-left:20px;'>"

        for todo in todos:
            html += f"""
            <li style="margin-bottom:8px;">
                <strong>{todo["name"]}</strong>
                <span style="color:#666;"> — {todo["status"]}</span>
            """

            if todo.get("notes"):
                html += f"""
                <br>
                <span style="color:#666;">{todo["notes"]}</span>
                """

            html += f"""
                <br>
                <span style="color:#666;">{todo["status"]}</span>
            </li>
            """

        html += "</ul>"

    html += "</div>"

    return html