from typing import Dict, List, Optional
from db.supabase_client import get_supabase
from services.enrichment.analyze_item import analyze_metadata
from services.enrichment.update_metadata import update_item_metadata
import time


def fetch_items_to_enrich(limit: Optional[int] = None, force_all: bool = False) -> List[Dict]:
    """
    Récupère les items à enrichir.
    
    Args:
        limit: Nombre max d'items à récupérer (None = tous)
        force_all: Si True, récupère TOUS les items (même déjà enrichis)
                   Si False (défaut), uniquement ceux avec labels IS NULL
    
    Returns:
        Liste d'items avec id, title, content
    """
    try:
        supabase = get_supabase()
        
        query = supabase.table("brew_items").select("id, title, content")
        
        # Si force_all = False, filtrer uniquement les non-enrichis
        if not force_all:
            query = query.is_("labels", "null")
        
        if limit:
            query = query.limit(limit)
        
        response = query.execute()
        return response.data or []
        
    except Exception as e:
        print(f"Erreur fetch items: {e}")
        return []


def enrich_single_item(item_id: str, title: str, content: str) -> Dict[str, object]:
    """
    Enrichit un seul item.
    
    Returns:
        {
            "status": "success" | "error",
            "item_id": str,
            "metadata": {...},
            "message": str
        }
    """
    
    # Analyser avec l'IA
    analysis = analyze_metadata(title, content)
    
    if analysis["status"] == "error":
        # Logger l'erreur en DB
        update_item_metadata(
            item_id=item_id,
            tags=None,
            labels=None,
            entities=None,
            zone=None,
            country=None,
            error_message=analysis.get("message", "Erreur inconnue")
        )
        return {
            "status": "error",
            "item_id": item_id,
            "message": analysis.get("message", "Erreur analyse")
        }
    
    # Mettre à jour en DB
    update_result = update_item_metadata(
        item_id=item_id,
        tags=analysis["tags"],
        labels=analysis["labels"],
        entities=analysis["entities"],
        zone=analysis["zone"],
        country=analysis["country"]
    )
    
    if update_result["status"] == "error":
        return {
            "status": "error",
            "item_id": item_id,
            "message": update_result.get("message", "Erreur UPDATE")
        }
    
    return {
        "status": "success",
        "item_id": item_id,
        "metadata": {
            "tags": analysis["tags"],
            "labels": analysis["labels"],
            "entities": analysis["entities"],
            "zone": analysis["zone"],
            "country": analysis["country"]
        },
        "message": "Enrichissement réussi"
    }


def enrich_items_batch(limit: Optional[int] = None) -> Dict[str, object]:
    """
    Enrichit un batch d'items (avec limit optionnel).
    
    Args:
        limit: Nombre max d'items à traiter (None = tous)
    
    Returns:
        {
            "status": "success" | "error",
            "total": int,
            "success": int,
            "errors": int,
            "duration": float,
            "details": [...]
        }
    """
    
    start_time = time.time()
    
    # Récupérer les items à enrichir
    items = fetch_items_to_enrich(limit=limit)
    
    if not items:
        return {
            "status": "success",
            "total": 0,
            "success": 0,
            "errors": 0,
            "duration": 0,
            "details": [],
            "message": "Aucun item à enrichir"
        }
    
    total = len(items)
    success_count = 0
    error_count = 0
    details = []
    
    # Traiter chaque item
    for idx, item in enumerate(items, start=1):
        item_id = item.get("id")
        title = item.get("title", "")
        content = item.get("content", "")
        
        print(f"[{idx}/{total}] Traitement item {item_id}...")
        
        result = enrich_single_item(item_id, title, content)
        
        if result["status"] == "success":
            success_count += 1
        else:
            error_count += 1
        
        details.append(result)
    
    duration = time.time() - start_time
    
    return {
        "status": "success" if error_count == 0 else "partial",
        "total": total,
        "success": success_count,
        "errors": error_count,
        "duration": round(duration, 2),
        "details": details
    }


def enrich_all_items() -> Dict[str, object]:
    """
    Enrichit TOUS les items non enrichis (sans limit).
    """
    return enrich_items_batch(limit=None)


def get_enrichment_stats() -> Dict[str, object]:
    """
    Récupère les statistiques d'enrichissement.
    
    Returns:
        {
            "total_items": int,
            "enriched_items": int,
            "not_enriched": int,
            "by_tags": {"ECO": X, "BOURSE": Y, "CRYPTO": Z},
            "by_labels": {...},
            "by_zone": {...}
        }
    """
    
    try:
        supabase = get_supabase()
        
        # Total items
        total_response = supabase.table("brew_items").select("id", count="exact").execute()
        total_items = total_response.count or 0
        
        # Items enrichis
        enriched_response = supabase.table("brew_items").select("id", count="exact").not_.is_("labels", "null").execute()
        enriched_items = enriched_response.count or 0
        
        # Items par tags
        tags_response = supabase.table("brew_items").select("tags").not_.is_("tags", "null").execute()
        tags_data = tags_response.data or []
        by_tags = {}
        for item in tags_data:
            tag = item.get("tags")
            if tag:
                by_tags[tag] = by_tags.get(tag, 0) + 1
        
        # Items par labels
        labels_response = supabase.table("brew_items").select("labels").not_.is_("labels", "null").execute()
        labels_data = labels_response.data or []
        by_labels = {}
        for item in labels_data:
            label = item.get("labels")
            if label:
                by_labels[label] = by_labels.get(label, 0) + 1
        
        # Items par zone
        zone_response = supabase.table("brew_items").select("zone").not_.is_("zone", "null").execute()
        zones_data = zone_response.data or []
        by_zone = {}
        for item in zones_data:
            zone = item.get("zone")
            if zone:
                by_zone[zone] = by_zone.get(zone, 0) + 1
        
        return {
            "status": "success",
            "total_items": total_items,
            "enriched_items": enriched_items,
            "not_enriched": total_items - enriched_items,
            "by_tags": by_tags,
            "by_labels": by_labels,
            "by_zone": by_zone
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erreur stats: {str(e)}"
        }
