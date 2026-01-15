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
# ERASE ALL BREW ITEMS
# ======================================================

def brew_items_erase() -> dict:
    """
    Delete all rows from brew_items table.
    Use with caution.
    """

    supabase = get_supabase_client()

    try:
        # Supprime toutes les lignes
        response = (
    supabase
    .table("brew_items")
    .delete()
    .is_("id", "not_null")
    .execute()
)



        return {
            "status": "success",
            "deleted": len(response.data) if response.data else 0
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
