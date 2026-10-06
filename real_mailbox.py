"""Interactive real-mailbox setup, connection test and import for Mamourart."""

import argparse
from getpass import getpass
import json
import os
from pathlib import Path

from email_import import import_emails
from email_reader import test_imap_connection
from email_settings import PROVIDERS


BASE_DIR = Path(__file__).parent
MAILBOX_CONFIG = BASE_DIR / "config" / "mailbox.json"
CLIENTS_CONFIG = BASE_DIR / "config" / "clients.json"


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as file:
            value = json.load(file)
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(value, file, indent=2)
        file.write("\n")


def setup():
    print("Mamourart — Real Mailbox setup")
    print("Providers: gmail, ovh, infomaniak, outlook, custom")
    provider = input("Provider: ").strip().casefold() or "custom"
    if provider not in PROVIDERS:
        raise SystemExit("Unknown provider.")

    user = input("Mailbox email / username: ").strip()
    if not user:
        raise SystemExit("Mailbox email is required.")

    preset = PROVIDERS[provider]
    host = preset["host"]
    port = preset["port"]
    if provider == "custom":
        host = input("IMAP host: ").strip()
        if not host:
            raise SystemExit("IMAP host is required for custom provider.")
        raw_port = input("IMAP port [993]: ").strip()
        port = int(raw_port) if raw_port else 993

    mailbox = input("Mailbox folder [INBOX]: ").strip() or "INBOX"
    search = input("IMAP search [UNSEEN]: ").strip() or "UNSEEN"

    _save(
        MAILBOX_CONFIG,
        {
            "provider": provider,
            "user": user,
            "mailbox": mailbox,
            "search": search,
            "max_messages": 50,
            "host": host,
            "port": port,
        },
    )

    clients = _load(CLIENTS_CONFIG)
    senders = list(clients.get("authorized_senders", []))
    domains = list(clients.get("authorized_domains", []))

    print("\nSecurity filter: only authorized transport clients will be imported.")
    sender = input("Authorized sender email (optional): ").strip().casefold()
    domain = input("Authorized sender domain (optional, e.g. client.com): ").strip().casefold().lstrip("@")
    if sender and sender not in senders:
        senders.append(sender)
    if domain and domain not in domains:
        domains.append(domain)

    _save(
        CLIENTS_CONFIG,
        {
            "authorized_senders": senders,
            "authorized_domains": domains,
        },
    )

    print("\nConfiguration saved. No mailbox password was stored.")
    if provider == "outlook":
        print("Outlook/Microsoft 365 needs OAuth2; password-only IMAP is disabled in this MVP.")


def _prepare_secret():
    if os.environ.get("MAMOURART_IMAP_PASSWORD"):
        return
    secret = getpass("Mailbox app password / password (hidden, not saved): ")
    if not secret:
        raise SystemExit("A mailbox secret is required for this provider.")
    os.environ["MAMOURART_IMAP_PASSWORD"] = secret


def test():
    _prepare_secret()
    result = test_imap_connection()
    print("Connection OK")
    print(f"Provider: {result['provider']}")
    print(f"Server: {result['host']}:{result['port']}")
    print(f"Mailbox: {result['mailbox']}")
    print(f"Messages in mailbox: {result['message_count']}")
    print("Mode: READ ONLY")


def import_now():
    _prepare_secret()
    os.environ["MAMOURART_EMAIL_SOURCE"] = "imap"
    stats = import_emails("imap")
    print("Real mailbox import completed")
    for key, value in stats.items():
        print(f"{key}: {value}")


def show_providers():
    for name, details in PROVIDERS.items():
        print(f"{name}: {details['host'] or 'custom host'}:{details['port']} ({details['auth']})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("setup", "test", "import", "providers"))
    args = parser.parse_args()

    if args.command == "setup":
        setup()
    elif args.command == "test":
        test()
    elif args.command == "import":
        import_now()
    else:
        show_providers()


if __name__ == "__main__":
    main()
