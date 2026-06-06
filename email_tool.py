import argparse
import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()


def send_email():
    sender = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_APP_PASSWORD")
    recipient = os.getenv("RECIPIENT_EMAIL")

    msg = EmailMessage()
    msg["Subject"] = ""
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content("")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender, password)
        smtp.send_message(msg)

    print("Email sent")


def main():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("send")

    args = parser.parse_args()

    if args.command == "send":
        send_email()


if __name__ == "__main__":
    main()