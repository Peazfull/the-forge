from typing import Dict, Optional
from db.supabase_client import get_supabase


def update_item_metadata(
    item_id: str,
    tags: Optional[str],
    labels: Optional[str],
    entities: Optional[str],
    zone: Optional[str],
    country: Optional[str],
    error_message: Optional[str] = None
) -> Dict[str, object]:
    """
    Met à jour les métadonnées d'un item dans brew_items.
    
    Args:
        item_id: UUID de l'item
        tags: Valeur du tag (ECO, BOURSE, CRYPTO)
        labels: Valeur du label (Eco_GeoPol, PEA, Action_USA, Action)
        entities: Entités (ex: "Apple, Trump")
        zone: Zone géographique (Europe, USA, ASIA, OCEANIA)
        country: Pays d'origine
        error_message: Message d'erreur si échec de l'analyse
    
    Returns:
        {"status": "success" | "error", "message": str}
    """
    
    try:
        supabase = get_supabase()
        
        # Construire l'objet de mise à jour
        update_data = {
            "tags": tags,
            "labels": labels,
            "entities": entities,
            "zone": zone,
            "country": country,
        }
        
        # Ajouter error_message si présent
        if error_message:
            update_data["error_message"] = error_message
        
        # Exécuter l'UPDATE
        response = supabase.table("brew_items").update(update_data).eq("id", item_id).execute()
        
        if not response.data:
            return {
                "status": "error",
                "message": f"Aucune ligne mise à jour pour l'item {item_id}"
            }
        
        return {
            "status": "success",
            "message": f"Item {item_id} mis à jour avec succès"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erreur UPDATE DB: {str(e)}"
        }


def batch_update_metadata(items_metadata: list) -> Dict[str, object]:
    """
    Met à jour plusieurs items en batch (optimisation).
    
    Args:
        items_metadata: Liste de dicts avec structure:
            [
                {
                    "id": "uuid",
                    "tags": "ECO",
                    "labels": "Eco_GeoPol",
                    "entities": "Trump",
                    "zone": "USA",
                    "country": "USA"
                },
                ...
            ]
    
    Returns:
        {
            "status": "success" | "error",
            "updated": int,
            "errors": int,
            "details": [...]
        }
    """
    
    updated_count = 0
    error_count = 0
    details = []
    
    for item in items_metadata:
        item_id = item.get("id")
        if not item_id:
            error_count += 1
            details.append({"id": "unknown", "status": "error", "message": "ID manquant"})
            continue
        
        result = update_item_metadata(
            item_id=item_id,
            tags=item.get("tags"),
            labels=item.get("labels"),
            entities=item.get("entities"),
            zone=item.get("zone"),
            country=item.get("country"),
            error_message=item.get("error_message")
        )
        
        if result["status"] == "success":
            updated_count += 1
        else:
            error_count += 1
        
        details.append({
            "id": item_id,
            "status": result["status"],
            "message": result.get("message", "")
        })
    
    return {
        "status": "success" if error_count == 0 else "partial",
        "updated": updated_count,
        "errors": error_count,
        "details": details
    }
