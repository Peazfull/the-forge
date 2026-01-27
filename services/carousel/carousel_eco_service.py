from typing import List, Dict
from db.supabase_client import get_supabase


def clear_carousel_eco() -> Dict[str, object]:
    """
    Vide la table carousel_eco (supprime tous les items).
    
    Returns:
        {"status": "success" | "error", "deleted": int, "message": str}
    """
    try:
        supabase = get_supabase()
        
        # Supprimer tous les items
        response = supabase.table("carousel_eco").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        
        return {
            "status": "success",
            "deleted": len(response.data) if response.data else 0,
            "message": "Carousel Eco vidé avec succès"
        }
    except Exception as e:
        return {
            "status": "error",
            "deleted": 0,
            "message": f"Erreur lors du vidage : {str(e)}"
        }


def insert_items_to_carousel_eco(item_ids: List[str]) -> Dict[str, object]:
    """
    Insère les items sélectionnés dans carousel_eco.
    L'ordre dans la liste item_ids détermine la position (1 à N).
    
    Args:
        item_ids: Liste de 1 à 8 UUIDs d'items (dans l'ordre du carousel)
    
    Returns:
        {"status": "success" | "error", "inserted": int, "message": str}
    """
    
    if len(item_ids) < 1 or len(item_ids) > 8:
        return {
            "status": "error",
            "inserted": 0,
            "message": f"Entre 1 et 8 items requis (reçu {len(item_ids)})"
        }
    
    try:
        supabase = get_supabase()
        
        # 1. Vider la table avant insertion
        clear_result = clear_carousel_eco()
        if clear_result["status"] == "error":
            return clear_result
        
        # 2. Récupérer les détails complets des items depuis brew_items
        response = supabase.table("brew_items").select(
            "id, title, content, tags, labels, score_global"
        ).in_("id", item_ids).execute()
        
        items_data = response.data or []
        
        if len(items_data) != len(item_ids):
            return {
                "status": "error",
                "inserted": 0,
                "message": f"Erreur : {len(items_data)} items trouvés sur {len(item_ids)}"
            }
        
        # 3. Créer un dict pour retrouver les items par ID
        items_dict = {item["id"]: item for item in items_data}
        
        # 4. Préparer les insertions (avec position selon l'ordre)
        carousel_items = []
        for position, item_id in enumerate(item_ids, start=1):
            item = items_dict.get(item_id)
            if not item:
                continue
            
            carousel_items.append({
                "item_id": item_id,
                "position": position,
                "title": item.get("title"),
                "content": item.get("content"),
                "score_global": item.get("score_global"),
                "tags": item.get("tags"),
                "labels": item.get("labels"),
                # Les champs IA restent NULL pour l'instant
                "title_carou": None,
                "content_carou": None,
                "prompt_image": None,
                "image_url": None
            })
        
        # 5. Insérer en batch
        insert_response = supabase.table("carousel_eco").insert(carousel_items).execute()
        
        return {
            "status": "success",
            "inserted": len(insert_response.data) if insert_response.data else 0,
            "message": f"✅ {len(carousel_items)} items insérés dans Carousel Eco"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "inserted": 0,
            "message": f"Erreur DB : {str(e)}"
        }


def get_carousel_eco_items() -> Dict[str, object]:
    """
    Récupère tous les items du carousel eco, triés par position.
    
    Returns:
        {"status": "success" | "error", "items": [...], "count": int}
    """
    try:
        supabase = get_supabase()
        
        response = supabase.table("carousel_eco").select(
            "*"
        ).order("position", desc=False).execute()
        
        items = response.data or []
        
        return {
            "status": "success",
            "items": items,
            "count": len(items)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "items": [],
            "count": 0,
            "message": f"Erreur DB : {str(e)}"
        }
