# Enrichment Module
# Analyse et enrichit les brew_items avec des métadonnées (tag, label, entities, zone, country)

from services.enrichment.enrichment_service import (
    enrich_all_items,
    enrich_items_batch,
    get_enrichment_stats,
)

__all__ = [
    "enrich_all_items",
    "enrich_items_batch",
    "get_enrichment_stats",
]
