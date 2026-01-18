from typing import List, Dict, Set, Tuple
from db.supabase_client import get_supabase
from services.nl_brewery.imap_client import check_connection, fetch_emails
from services.nl_brewery.process_newsletter import process_newsletter


TABLE_RECIPIENTS = "nl_recipients"


def load_recipients() -> List[str]:
    try:
        supabase = get_supabase()
        resp = supabase.table(TABLE_RECIPIENTS).select("email").order("id").execute()
        data = resp.data or []
        recipients = []
        for item in data:
            if isinstance(item, dict) and item.get("email"):
                recipients.append(item["email"])
        return recipients
    except Exception:
        return []


def add_recipient(email: str) -> bool:
    if not email:
        return False
    try:
        supabase = get_supabase()
        supabase.table(TABLE_RECIPIENTS).insert({"email": email}).execute()
        return True
    except Exception:
        return False


def remove_recipient(email: str) -> bool:
    if not email:
        return False
    try:
        supabase = get_supabase()
        supabase.table(TABLE_RECIPIENTS).delete().eq("email", email).execute()
        return True
    except Exception:
        return False


def check_gmail_connection() -> Dict[str, str]:
    try:
        ok = check_connection()
        if ok:
            return {"status": "success", "message": "Gmail connecté"}
        return {"status": "error", "message": "Connexion IMAP impossible"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def _match_recipient(to_value: str, recipients: List[str]) -> bool:
    if not recipients:
        return True
    to_lower = (to_value or "").lower()
    for r in recipients:
        if r.lower() in to_lower:
            return True
    return False


def _dedupe_key(email_data: Dict[str, str]) -> Tuple[str, str, str]:
    return (
        email_data.get("message_id", "") or "",
        email_data.get("sender", "") or "",
        email_data.get("subject", "") or "",
    )


def fetch_and_process_newsletters(last_hours: int) -> Dict[str, object]:
    recipients = load_recipients()
    emails = fetch_emails(last_hours)

    unique_keys: Set[Tuple[str, str, str]] = set()
    items = []
    errors = []
    raw_texts = []

    for email_data in emails:
        if not _match_recipient(email_data.get("to", ""), recipients):
            continue
        key = _dedupe_key(email_data)
        if key in unique_keys:
            continue
        unique_keys.add(key)

        body_text = (email_data.get("body_text") or "").strip()
        if body_text:
            raw_texts.append(
                f"=== EMAIL ===\nFrom: {email_data.get('sender','')}\n"
                f"To: {email_data.get('to','')}\n"
                f"Subject: {email_data.get('subject','')}\n"
                f"Date: {email_data.get('date','')}\n\n{body_text}\n"
            )

        result = process_newsletter(email_data)
        if result.get("status") != "success":
            errors.append(result.get("message", "Erreur inconnue"))
            continue

        for item in result.get("items", []):
            if isinstance(item, dict):
                item["source_name"] = "Newsletter"
                item["source_link"] = email_data.get("sender")
                item["source_date"] = email_data.get("date")
                item["source_raw"] = None
                items.append(item)

    return {
        "status": "success",
        "email_count": len(emails),
        "raw_preview": "\n\n".join(raw_texts),
        "items": items,
        "errors": errors,
    }
