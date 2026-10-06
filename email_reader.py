"""Read local test emails or a real IMAP mailbox without modifying messages."""

from dataclasses import dataclass
from email import policy
from email.header import decode_header, make_header
from email.parser import BytesParser
from email.utils import parseaddr
from html.parser import HTMLParser
import imaplib
import ssl
from pathlib import Path
from typing import Iterable

from email_settings import load_imap_settings


@dataclass
class EmailMessageData:
    message_id: str
    sender: str
    subject: str
    body: str
    source: str


class _HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def text(self):
        return "\n".join(part.strip() for part in self.parts if part.strip())


def _decode_subject(value: str) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def _message_body(message) -> str:
    plain_parts = []
    html_parts = []
    parts = message.walk() if message.is_multipart() else [message]

    for part in parts:
        if part.get_content_disposition() == "attachment":
            continue
        content_type = part.get_content_type()
        if content_type not in ("text/plain", "text/html"):
            continue
        try:
            content = part.get_content()
        except Exception:
            payload = part.get_payload(decode=True) or b""
            charset = part.get_content_charset() or "utf-8"
            content = payload.decode(charset, errors="replace")
        if content_type == "text/plain":
            plain_parts.append(content)
        else:
            html_parts.append(content)

    if plain_parts:
        return "\n".join(plain_parts).strip()
    if html_parts:
        parser = _HTMLTextExtractor()
        parser.feed("\n".join(html_parts))
        return parser.text().strip()
    return ""


def _from_email_message(message, source: str, fallback_id: str) -> EmailMessageData:
    sender = parseaddr(message.get("From", ""))[1]
    subject = _decode_subject(message.get("Subject", ""))
    message_id = (message.get("Message-ID") or fallback_id).strip()
    return EmailMessageData(message_id, sender, subject, _message_body(message), source)


def _parse_txt_email(path: Path) -> EmailMessageData:
    raw = path.read_text(encoding="utf-8")
    sender = ""
    subject = ""
    message_id = path.name
    body_lines = []
    in_headers = True

    for line in raw.splitlines():
        if in_headers and not line.strip():
            in_headers = False
            continue
        if in_headers and ":" in line:
            key, value = line.split(":", 1)
            key = key.strip().casefold()
            value = value.strip()
            if key == "from":
                sender = parseaddr(value)[1] or value
            elif key == "subject":
                subject = value
            elif key == "message-id":
                message_id = value
            else:
                body_lines.append(line)
        else:
            body_lines.append(line)

    return EmailMessageData(
        message_id=message_id,
        sender=sender,
        subject=subject,
        body="\n".join(body_lines).strip(),
        source=str(path),
    )


def read_local_inbox(inbox_dir: Path) -> list[EmailMessageData]:
    if not inbox_dir.exists():
        return []
    messages = []
    for path in sorted(inbox_dir.iterdir()):
        if path.suffix.lower() == ".txt":
            messages.append(_parse_txt_email(path))
        elif path.suffix.lower() == ".eml":
            message = BytesParser(policy=policy.default).parsebytes(path.read_bytes())
            messages.append(_from_email_message(message, str(path), path.name))
    return messages


def _open_imap_client():
    settings = load_imap_settings()
    context = ssl.create_default_context()
    client = imaplib.IMAP4_SSL(
        settings.host,
        settings.port,
        ssl_context=context,
        timeout=settings.timeout_seconds,
    )
    client.login(settings.user, settings.password)
    return client, settings


def test_imap_connection() -> dict:
    client, settings = _open_imap_client()
    try:
        status, data = client.select(settings.mailbox, readonly=True)
        if status != "OK":
            raise RuntimeError(f"Cannot open IMAP mailbox: {settings.mailbox}")
        message_count = 0
        if data and data[0]:
            try:
                message_count = int(data[0])
            except (TypeError, ValueError):
                pass
        return {
            "provider": settings.provider,
            "host": settings.host,
            "port": settings.port,
            "mailbox": settings.mailbox,
            "message_count": message_count,
            "readonly": True,
        }
    finally:
        try:
            client.logout()
        except Exception:
            pass


def read_imap_inbox() -> list[EmailMessageData]:
    client, settings = _open_imap_client()
    messages = []
    try:
        status, _ = client.select(settings.mailbox, readonly=True)
        if status != "OK":
            raise RuntimeError(f"Cannot open IMAP mailbox: {settings.mailbox}")

        status, data = client.uid("search", None, settings.search_query)
        if status != "OK":
            raise RuntimeError("IMAP search failed")

        uids = (data[0].split() if data and data[0] else [])[-settings.max_messages:]
        for uid in uids:
            status, fetched = client.uid("fetch", uid, "(BODY.PEEK[])")
            if status != "OK" or not fetched:
                continue
            raw = next((item[1] for item in fetched if isinstance(item, tuple)), None)
            if not raw:
                continue
            uid_text = uid.decode(errors="ignore")
            message = BytesParser(policy=policy.default).parsebytes(raw)
            messages.append(
                _from_email_message(
                    message,
                    source=f"imap:{settings.mailbox}:uid:{uid_text}",
                    fallback_id=f"imap-uid-{uid_text}",
                )
            )
        return messages
    finally:
        try:
            client.logout()
        except Exception:
            pass


def read_messages(source: str, inbox_dir: Path) -> Iterable[EmailMessageData]:
    source = source.strip().casefold()
    if source == "imap":
        return read_imap_inbox()
    if source == "local":
        return read_local_inbox(inbox_dir)
    raise ValueError("MAMOURART_EMAIL_SOURCE must be 'local' or 'imap'.")
