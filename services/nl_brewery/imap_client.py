import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime, parseaddr
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from typing import List, Dict, Optional, Tuple
import streamlit as st


IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993


class _HTMLStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._data = []

    def handle_data(self, data: str) -> None:
        if data:
            self._data.append(data)

    def get_data(self) -> str:
        return " ".join(self._data)


def _strip_html(html: str) -> str:
    stripper = _HTMLStripper()
    stripper.feed(html)
    text = stripper.get_data()
    return " ".join(text.split())


def _decode_header_value(value: Optional[str]) -> str:
    if not value:
        return ""
    decoded_parts = decode_header(value)
    chunks = []
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            try:
                chunks.append(part.decode(encoding or "utf-8", errors="replace"))
            except Exception:
                chunks.append(part.decode("utf-8", errors="replace"))
        else:
            chunks.append(part)
    return "".join(chunks).strip()


def _get_imap_credentials() -> Tuple[str, str]:
    candidates = [
        ("GMAIL_IMAP_USER", "GMAIL_IMAP_PASSWORD"),
        ("GMAIL_USER", "GMAIL_PASSWORD"),
        ("GMAIL_ADDRESS", "GMAIL_APP_PASSWORD"),
    ]
    for user_key, pass_key in candidates:
        if user_key in st.secrets and pass_key in st.secrets:
            return st.secrets[user_key], st.secrets[pass_key]
    raise ValueError(
        "Identifiants Gmail manquants dans st.secrets "
        "(GMAIL_IMAP_USER/GMAIL_IMAP_PASSWORD ou GMAIL_USER/GMAIL_PASSWORD)"
    )


def check_connection() -> bool:
    user, password = _get_imap_credentials()
    try:
        client = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        client.login(user, password)
        client.logout()
        return True
    except Exception:
        return False


def _extract_body(message: email.message.Message) -> Dict[str, str]:
    body_text = ""
    body_html = ""

    if message.is_multipart():
        for part in message.walk():
            content_type = part.get_content_type()
            content_disposition = part.get("Content-Disposition", "") or ""
            if "attachment" in content_disposition.lower():
                continue

            payload = part.get_payload(decode=True)
            if payload is None:
                continue
            charset = part.get_content_charset() or "utf-8"

            if content_type == "text/plain" and not body_text:
                body_text = payload.decode(charset, errors="replace")
            elif content_type == "text/html" and not body_html:
                body_html = payload.decode(charset, errors="replace")
    else:
        payload = message.get_payload(decode=True)
        if payload is not None:
            charset = message.get_content_charset() or "utf-8"
            content_type = message.get_content_type()
            if content_type == "text/html":
                body_html = payload.decode(charset, errors="replace")
            else:
                body_text = payload.decode(charset, errors="replace")

    if not body_text and body_html:
        body_text = _strip_html(body_html)

    return {
        "body_text": body_text.strip(),
        "body_html": body_html.strip(),
    }


def fetch_emails(last_hours: int, max_emails: Optional[int] = None) -> List[Dict[str, str]]:
    if last_hours <= 0:
        return []

    user, password = _get_imap_credentials()
    now_utc = datetime.now(timezone.utc)
    cutoff = now_utc - timedelta(hours=last_hours)
    since_date = cutoff.strftime("%d-%b-%Y")

    try:
        client = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        client.login(user, password)
        client.select("INBOX")

        status, data = client.search(None, f'(SINCE "{since_date}")')
        if status != "OK":
            client.logout()
            return []

        message_ids = data[0].split()
        if max_emails and max_emails > 0:
            message_ids = message_ids[-max_emails:]
        emails = []

        for msg_id in message_ids:
            status, msg_data = client.fetch(msg_id, "(RFC822)")
            if status != "OK" or not msg_data:
                continue
            raw_bytes = msg_data[0][1]
            if not raw_bytes:
                continue
            msg = email.message_from_bytes(raw_bytes)

            subject = _decode_header_value(msg.get("Subject"))
            sender = parseaddr(_decode_header_value(msg.get("From")))[1]
            to_value = _decode_header_value(msg.get("To"))
            date_raw = msg.get("Date")
            message_id = _decode_header_value(msg.get("Message-ID"))

            parsed_date = parsedate_to_datetime(date_raw) if date_raw else None
            if parsed_date is None:
                continue
            if parsed_date.tzinfo is None:
                parsed_date = parsed_date.replace(tzinfo=timezone.utc)

            if parsed_date < cutoff:
                continue

            bodies = _extract_body(msg)

            emails.append({
                "subject": subject,
                "sender": sender,
                "to": to_value,
                "date": parsed_date.astimezone(timezone.utc).isoformat(),
                "body_html": bodies["body_html"],
                "body_text": bodies["body_text"],
                "message_id": message_id,
            })

        client.logout()
        return emails
    except Exception as exc:
        raise RuntimeError(f"Erreur IMAP : {exc}") from exc
