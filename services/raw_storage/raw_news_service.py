import uuid
from datetime import datetime, date
from typing import Optional
import streamlit as st
from supabase import create_client, Client


# ======================================================
# SUPABASE CLIENT
# ======================================================

def get_supabase_client() -> Client:
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_SERVICE_KEY"]
    )


# ======================================================
# ENRICH RAW ITEMS (TECHNICAL METADATA)
# ======================================================

def enrich_raw_items(
    items: list,
    *,
    flow: str,
    source_type: str,
    source_name: Optional[str] = None,
    source_link: Optional[str] = None,
    source_date: Optional[str] = None,
    source_raw: Optional[str] = None,
) -> list:
    """
    Enrich editorial items with technical metadata.
    No AI. No business logic. Deterministic only.
    """

    now = datetime.utcnow().isoformat()
    batch_date = date.today().isoformat()

    enriched_items = []

    for item in items:
        enriched_items.append({
            # --- SYSTEM ---
            "flow": flow,
            "status": "draft",
            "processed_at": now,
            "batch_date": batch_date,

            # --- SOURCE ---
            "source_type": source_type,
            "source_name": source_name,
            "source_link": source_link,
            "source_date": source_date,
            "source_raw": source_raw,

            # --- CONTENT ---
            "title": item.get("title"),
            "content": item.get("content"),
        })

    return enriched_items


# ======================================================
# INSERT RAW NEWS
# ======================================================

def insert_raw_news(items: list) -> dict:
    """
    Insert raw news items into Supabase.
    One row per item.
    """

    if not items:
        return {
            "status": "error",
            "message": "No items to insert"
        }

    supabase = get_supabase_client()

    try:
        response = supabase.table("brew_items").insert(items).execute()

        return {
            "status": "success",
            "inserted": len(items),
            "data": response.data
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
