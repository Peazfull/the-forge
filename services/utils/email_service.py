import smtplib
from email.message import EmailMessage
import streamlit as st


def send_email_with_attachments(to_email: str, subject: str, body: str, attachments: list[tuple[str, bytes, str]]):
    """
    Envoie un email avec pièces jointes via Gmail SMTP.
    attachments: [(filename, bytes, mimetype), ...]
    """
    user = st.secrets.get("GMAIL_IMAP_USER")
    password = st.secrets.get("GMAIL_IMAP_PASSWORD")
    if not user or not password:
        raise RuntimeError("GMAIL_IMAP_USER/GMAIL_IMAP_PASSWORD manquants dans secrets")
    
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_email
    msg.set_content(body)
    
    for filename, data, mimetype in attachments:
        maintype, subtype = mimetype.split("/", 1)
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)
