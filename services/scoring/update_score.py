from datetime import datetime
from db.supabase_client import get_supabase
from typing import Dict


def update_item_score(item_id: str, score: int) -> Dict[str, object]:
    """
    Met à jour le score d'un item dans la table brew_items.
    
    Args:
        item_id: ID de l'item
        score: Score (0-100)
    
    Returns:
        {
            "status": "success" | "error",
            "message": str
        }
    """
    
    try:
        supabase = get_supabase()
        
        # Update le score dans la DB
        response = supabase.table("brew_items").update({
            "score_global": score,
            "processed_at": datetime.utcnow().isoformat()
        }).eq("id", item_id).execute()
        
        if response.data:
            return {
                "status": "success",
                "message": f"Score mis à jour: {score}/100"
            }
        else:
            return {
                "status": "error",
                "message": "Aucune donnée retournée par la DB"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erreur DB: {str(e)}"
        }
