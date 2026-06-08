import argparse
import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

from config import load_config, save_config
from duedate_content import add_duedate_content, get_duedate_html
from weather_content import add_weather, get_weather_html
from news_content import get_news_html

load_dotenv()


def list_content():
    config = load_config()
    content = config.get("content", [])

    if not content:
        print("No email content has been added yet.")
        return

    print("Email content:")

    for index, item in enumerate(content, start=1):
        if item["type"] == "weather":
            print(
                f"{index}. Weather ({item['location_name']})"
            )

        elif item["type"] == "duedate":
            print(
                f"{index}. {item['title']}"
            )

        elif item["type"] == "news":
            print(
                f"{index}. {item['title']} "
                f"({item.get('category', 'general')})"
            )

        else:
            print(f"{index}. Unknown content type: {item}")


def delete_content(index):
    config = load_config()
    content = config.get("content", [])

    if index < 1 or index > len(content):
        print(f"Invalid content number: {index}")
        return

    removed = content.pop(index - 1)
    config["content"] = content
    save_config(config)

    if removed["type"] == "weather":
        print(f"Deleted weather content for {removed['location_name']}")
    elif removed["type"] == "duedate":
        print(f"Deleted due date content: {removed['title']}")
    else:
        print("Deleted content")


def build_email_html():
    config = load_config()
    sections = []

    for item in config.get("content", []):
        if item["type"] == "weather":
            sections.append(get_weather_html(item))
        elif item["type"] == "duedate":
            sections.append(get_duedate_html(item))

        elif item["type"] == "duedate":
            sections.append(get_duedate_html(item))

        elif item["type"] == "news":
            sections.append(get_news_html(item))

    content_html = "\n".join(sections)

    return f"""
    <html>
        <body style="font-family:Arial, sans-serif; padding:20px; color:#222;">
            <h1 style="font-size:22px; margin-bottom:20px;">
                Your Email Tool Update
            </h1>
            {content_html}
        </body>
    </html>
    """


def send_email():
    sender = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_APP_PASSWORD")
    recipient = os.getenv("RECIPIENT_EMAIL")

    if not sender:
        raise ValueError("Missing EMAIL_ADDRESS in .env")

    if not password:
        raise ValueError("Missing EMAIL_APP_PASSWORD in .env")

    if not recipient:
        raise ValueError("Missing RECIPIENT_EMAIL in .env")

    html_body = build_email_html()

    msg = EmailMessage()
    msg["Subject"] = "Your Email Tool Update"
    msg["From"] = sender
    msg["To"] = recipient

    msg.set_content(
        "This email contains HTML content. "
        "Please view it in an HTML-compatible email client."
    )
    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender, password)
        smtp.send_message(msg)

    print("Email sent")


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("send")
    subparsers.add_parser("content")
    subparsers.add_parser("add-duedates")

    delete_parser = subparsers.add_parser("delete-content")
    delete_parser.add_argument("index", type=int)

    weather_parser = subparsers.add_parser("add-weather")
    weather_parser.add_argument("--lat", type=float)
    weather_parser.add_argument("--lon", type=float)
    weather_parser.add_argument("--name")

    args = parser.parse_args()

    if args.command == "send":
        send_email()

    elif args.command == "content":
        list_content()

    elif args.command == "delete-content":
        delete_content(args.index)

    elif args.command == "add-weather":
        config = load_config()
        message = add_weather(config, args.lat, args.lon, args.name)
        save_config(config)
        print(message)

    elif args.command == "add-duedates":
        config = load_config()
        message = add_duedate_content(config)
        save_config(config)
        print(message)


if __name__ == "__main__":
    main()
