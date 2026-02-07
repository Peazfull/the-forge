import threading
import time
from typing import List, Dict, Optional

from db.supabase_client import get_supabase
from services.carousel.eco.carousel_eco_service import (
    insert_items_to_carousel_eco,
    get_carousel_eco_items,
    upsert_carousel_eco_cover,
)
from services.carousel.eco.carousel_slide_service import clear_slide_files
from services.carousel.eco.generate_carousel_texts_service import (
    generate_carousel_text_for_item,
    generate_image_prompt_for_item,
)
from services.carousel.eco.carousel_image_service import generate_and_save_carousel_image


class EcoCarouselJob:
    """Job de génération de carrousel Eco en threading pour éviter les timeouts Streamlit."""
    
    def __init__(self):
        self.state = "idle"  # idle, running, completed, failed, stopped
        self.current = 0
        self.total = 0
        self.processed = 0
        self.errors: List[str] = []
        self.last_log = ""
        self.current_item_title = ""
        
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._items: List[Dict] = []
    
    def start(self, selected_items: List[Dict]) -> None:
        """Lance la génération en thread daemon."""
        if self.state == "running":
            return
        
        self._items = selected_items
        self.total = len(selected_items) + 1  # +1 pour la cover
        self.current = 0
        self.processed = 0
        self.errors = []
        self.last_log = ""
        self.current_item_title = ""
        self.state = "running"
        self._stop_event.clear()
        
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
    
    def stop(self) -> None:
        """Arrête le job."""
        self._stop_event.set()
        if self.state == "running":
            self.state = "stopped"
            self._log("⏹️ Job stoppé")
    
    def get_status(self) -> Dict:
        """Retourne l'état actuel du job."""
        return {
            "state": self.state,
            "current": self.current,
            "total": self.total,
            "processed": self.processed,
            "errors": self.errors,
            "last_log": self.last_log,
            "current_item_title": self.current_item_title,
        }
    
    def _log(self, message: str) -> None:
        """Ajoute un log."""
        self.last_log = message
    
    def _run(self) -> None:
        """Boucle principale de génération (dans le thread)."""
        try:
            # Étape 1 : Insertion des items en DB
            self._log("📤 Insertion des items en DB...")
            result = insert_items_to_carousel_eco(self._items)
            if result["status"] != "success":
                raise Exception(f"Erreur insertion : {result.get('message', 'inconnue')}")
            self._log(f"✅ {result.get('inserted', 0)} items insérés")
            
            # Étape 2 : Récupérer les items depuis DB
            self._log("📥 Récupération des items depuis DB...")
            carousel_data = get_carousel_eco_items()
            if carousel_data["status"] != "success" or carousel_data["count"] == 0:
                raise Exception("Erreur récupération ou 0 items")
            
            items = carousel_data["items"]
            self._log(f"✅ {len(items)} items récupérés")
            
            # Étape 3 : Créer la cover (position 0)
            self._log("🎨 Création de la cover...")
            first_item = items[0]
            cover_result = upsert_carousel_eco_cover({
                "item_id": first_item["item_id"],
                "title": first_item["title"],
                "content": first_item["content"],
                "score_global": first_item["score_global"],
                "tags": first_item["tags"],
                "labels": first_item["labels"],
            })
            
            if cover_result.get("status") != "success":
                raise Exception(f"Erreur cover : {cover_result.get('message', '')}")
            self._log("✅ Cover créée")
            
            # Étape 4 : Nettoyer le storage
            self._log("🧹 Nettoyage des caches...")
            clear_slide_files()
            
            # Étape 5 : Récupérer TOUS les items (cover + items normaux)
            carousel_data = get_carousel_eco_items()
            all_items = carousel_data["items"]
            
            # Étape 6 : Générer la cover (position 0)
            self._log("━━━ GÉNÉRATION COVER (position 0) ━━━")
            self.current = 1
            cover_item = next((item for item in all_items if item["position"] == 0), None)
            
            if cover_item:
                self.current_item_title = cover_item.get("title", "")[:40]
                self._generate_item(cover_item, is_cover=True)
                self.processed += 1
            
            # Étape 7 : Générer les items normaux (positions 1-N)
            content_items = [item for item in all_items if item["position"] > 0]
            content_items.sort(key=lambda x: x["position"])
            
            for item in content_items:
                if self._stop_event.is_set():
                    break
                
                self.current += 1
                self.current_item_title = item.get("title", "")[:40]
                position = item["position"]
                
                self._log(f"━━━ ITEM #{position} ({self.current}/{self.total}) ━━━")
                
                try:
                    self._generate_item(item, is_cover=False)
                    self.processed += 1
                except Exception as e:
                    error_msg = f"Erreur item #{position}: {str(e)[:100]}"
                    self.errors.append(error_msg)
                    self._log(f"❌ {error_msg}")
            
            # Terminé
            if self._stop_event.is_set():
                self.state = "stopped"
            else:
                self.state = "completed"
                self._log(f"✅ Génération terminée ! {self.processed} items traités")
        
        except Exception as e:
            self.state = "failed"
            error_msg = f"Erreur critique : {str(e)[:200]}"
            self.errors.append(error_msg)
            self._log(f"❌ {error_msg}")
    
    def _generate_item(self, item: Dict, is_cover: bool) -> None:
        """Génère un item (textes + image)."""
        supabase = get_supabase()
        item_id = item["id"]
        position = item["position"]
        title = item.get("title", "")
        content = item.get("content", "")
        
        if is_cover:
            # Cover : seulement prompt + image
            self._log(f"  ⏳ Génération prompt image cover...")
            prompt_result = generate_image_prompt_for_item(title, content, prompt_type="sunset")
            
            if prompt_result.get("status") != "success":
                raise Exception(f"Prompt cover KO: {prompt_result.get('message', '')}")
            
            self._log(f"  ✅ Prompt image généré")
            
            # Sauvegarder le prompt
            supabase.table("carousel_eco").update({
                "prompt_image_1": prompt_result.get("image_prompt")
            }).eq("id", item_id).execute()
            
            # Générer l'image
            self._log(f"  🎨 Génération image cover...")
            img_result = generate_and_save_carousel_image(
                prompt_result["image_prompt"],
                position=0,
                item_id=item_id
            )
            
            if img_result["status"] == "success":
                model_used = img_result.get("model_used", "inconnu")
                self._log(f"  ✅ Cover générée ({model_used})")
            else:
                raise Exception(f"Image cover échec : {img_result.get('message', '')}")
        
        else:
            # Item normal : textes + prompts + image
            self._log(f"  ⏳ Génération textes...")
            text_result = generate_carousel_text_for_item(title, content)
            
            if text_result.get("status") != "success":
                raise Exception(f"Textes KO: {text_result.get('message', '')}")
            
            self._log(f"  ✅ Textes générés")
            
            # Générer prompts images
            self._log(f"  ⏳ Génération prompts images...")
            prompt_1_result = generate_image_prompt_for_item(title, content, prompt_type="sunset")
            prompt_2_result = generate_image_prompt_for_item(title, content, prompt_type="studio")
            self._log(f"  ✅ Prompts images générés")
            
            # Sauvegarder en DB
            self._log(f"  💾 Sauvegarde en DB...")
            supabase.table("carousel_eco").update({
                "title_carou": text_result["title_carou"],
                "content_carou": text_result["content_carou"],
                "prompt_image_1": prompt_1_result.get("image_prompt"),
                "prompt_image_2": prompt_2_result.get("image_prompt"),
            }).eq("id", item_id).execute()
            self._log(f"  ✅ Sauvegarde DB OK")
            
            # Générer image
            if prompt_1_result.get("status") == "success":
                self._log(f"  🎨 Génération image...")
                img_result = generate_and_save_carousel_image(
                    prompt_1_result["image_prompt"],
                    position,
                    item_id=item_id
                )
                
                if img_result["status"] == "success":
                    model_used = img_result.get("model_used", "inconnu")
                    self._log(f"  ✅ Image générée ({model_used})")
                else:
                    raise Exception(f"Image échec : {img_result.get('message', '')}")
            else:
                self._log(f"  ⚠️ Pas de prompt image valide")


# Instance globale
_eco_carousel_job: Optional[EcoCarouselJob] = None


def get_eco_carousel_job() -> EcoCarouselJob:
    """Retourne l'instance globale du job."""
    global _eco_carousel_job
    if _eco_carousel_job is None:
        _eco_carousel_job = EcoCarouselJob()
    return _eco_carousel_job
