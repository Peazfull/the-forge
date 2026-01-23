from db.supabase_client import get_supabase
from typing import List, Dict, Optional
from services.scoring.analyze_score import analyze_score
from services.scoring.update_score import update_item_score


def fetch_items_to_score(limit: Optional[int] = None, force_all: bool = True) -> List[Dict[str, str]]:
    """
    Récupère les items à scorer depuis la DB.
    
    Args:
        limit: Nombre max d'items à récupérer (None = tous)
        force_all: Si True, récupère tous les items enrichis (même déjà scorés)
                   Si False, récupère uniquement les items non scorés
    
    Returns:
        Liste d'items avec id, title, content, tags, labels, entities, source_type
    """
    
    try:
        supabase = get_supabase()
        
        # Récupérer les items enrichis (labels non null)
        query = supabase.table("brew_items").select(
            "id, title, content, tags, labels, entities, source_type"
        ).not_.is_("labels", "null")
        
        # Si force_all=False, ne prendre que les items non scorés
        if not force_all:
            query = query.is_("score_global", "null")
        
        query = query.order("processed_at", desc=True)
        
        if limit:
            query = query.limit(limit)
        
        response = query.execute()
        
        return response.data or []
        
    except Exception as e:
        print(f"Erreur fetch_items_to_score: {e}")
        return []


def score_single_item(
    item_id: str,
    title: str,
    content: str,
    tags: str = None,
    labels: str = None,
    entities: str = None,
    source_type: str = None
) -> Dict[str, object]:
    """
    Score un seul item et met à jour la DB.
    
    Returns:
        {
            "status": "success" | "error",
            "score": int,
            "message": str
        }
    """
    
    # Analyser avec l'IA
    result = analyze_score(title, content, tags, labels, entities, source_type)
    
    if result["status"] == "error":
        return result
    
    score = result["score"]
    
    # Mettre à jour la DB
    update_result = update_item_score(item_id, score)
    
    if update_result["status"] == "error":
        return {
            "status": "error",
            "message": f"Score calculé ({score}) mais erreur DB: {update_result['message']}",
            "score": score
        }
    
    return {
        "status": "success",
        "score": score,
        "message": f"Score attribué: {score}/100"
    }


def get_scoring_stats() -> Dict[str, object]:
    """
    Récupère les statistiques de scoring.
    
    Returns:
        {
            "status": "success" | "error",
            "total_items": int,
            "scored_items": int,
            "not_scored": int,
            "average_score": float,
            "by_range": {
                "0-19": int,
                "20-39": int,
                "40-59": int,
                "60-79": int,
                "80-100": int
            }
        }
    """
    
    try:
        supabase = get_supabase()
        
        # Total des items enrichis
        response_total = supabase.table("brew_items").select(
            "id", count="exact"
        ).not_.is_("labels", "null").execute()
        total_items = response_total.count or 0
        
        # Items scorés (score_global non null)
        response_scored = supabase.table("brew_items").select(
            "score_global"
        ).not_.is_("labels", "null").not_.is_("score_global", "null").execute()
        
        scored_items = len(response_scored.data) if response_scored.data else 0
        not_scored = total_items - scored_items
        
        # Calcul du score moyen et distribution
        scores = [item["score_global"] for item in (response_scored.data or []) if item.get("score_global") is not None]
        
        average_score = sum(scores) / len(scores) if scores else 0
        
        # Distribution par tranches
        by_range = {
            "0-19": len([s for s in scores if 0 <= s <= 19]),
            "20-39": len([s for s in scores if 20 <= s <= 39]),
            "40-59": len([s for s in scores if 40 <= s <= 59]),
            "60-79": len([s for s in scores if 60 <= s <= 79]),
            "80-100": len([s for s in scores if 80 <= s <= 100])
        }
        
        return {
            "status": "success",
            "total_items": total_items,
            "scored_items": scored_items,
            "not_scored": not_scored,
            "average_score": round(average_score, 1),
            "by_range": by_range
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erreur: {str(e)}",
            "total_items": 0,
            "scored_items": 0,
            "not_scored": 0,
            "average_score": 0,
            "by_range": {}
        }
