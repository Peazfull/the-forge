import streamlit as st
from supabase import create_client, Client


def get_supabase_client() -> Client:
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_SERVICE_KEY"]
    )


def get_brew_items_stats() -> dict:
    """
    Return count, min_date, max_date from brew_items.
    """

    supabase = get_supabase_client()

    try:
        response = supabase.table("brew_items").select(
            "processed_at"
        ).execute()

        rows = response.data or []

        if not rows:
            return {
                "count": 0,
                "min_date": None,
                "max_date": None
            }

        dates = [r["processed_at"] for r in rows if r["processed_at"]]

        return {
            "count": len(rows),
            "min_date": min(dates) if dates else None,
            "max_date": max(dates) if dates else None
        }

    except Exception as e:
        return {
            "error": str(e)
        }
