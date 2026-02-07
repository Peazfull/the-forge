import threading
import time
from typing import Dict, List, Optional
import streamlit as st

from db.supabase_client import get_supabase
from services.carousel.crypto.carousel_crypto_service import (
    insert_items_to_carousel_crypto,
    get_carousel_crypto_items,
    upsert_carousel_crypto_cover,
)
from services.carousel.crypto.carousel_image_service import (
    clear_image_files,
    generate_and_save_carousel_image,
)
from services.carousel.crypto.carousel_slide_service import (
    clear_slide_files,
    generate_carousel_slide,
    generate_cover_slide,
    upload_slide_bytes,
)
from services.carousel.crypto.generate_carousel_texts_service import (
    generate_carousel_text_for_item,
    generate_image_prompt_for_item,
)
from services.carousel.crypto.generate_carousel_caption_service import (
    generate_caption_from_items,
    upload_caption_text,
)


class CryptoCarouselJob:
    """
    Gère la génération complète d'un carrousel Crypto en arrière-plan (threading).
    """

    def __init__(self) -> None:
        self.state = "idle"  # idle, running, completed, failed, stopped
        self.total = 0
        self.current = 0
        self.processed = 0
        self.skipped = 0
        self.errors: List[str] = []
        self.last_log: str = ""
        self.current_item_title: str = ""
        self.just_completed: bool = False  # Flag pour notifier le frontend

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._items_to_process: List[Dict] = []

    def start(self, selected_items: List[Dict]) -> None:
        if self.state == "running":
            return

        self.reset()
        self._items_to_process = selected_items
        self.total = len(selected_items) + 1  # +1 pour la cover
        self.state = "running"
        self._stop_event.clear()

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self.state == "running":
            self.state = "stopped"
            self._log("⏹️ Job stoppé")

    def reset(self) -> None:
        self.state = "idle"
        self.total = 0
        self.current = 0
        self.processed = 0
        self.skipped = 0
        self.errors = []
        self.last_log = ""
        self.current_item_title = ""
        self.just_completed = False
        self._stop_event.clear()
        self._items_to_process = []

    def get_status(self) -> Dict[str, object]:
        return {
            "state": self.state,
            "total": self.total,
            "current": self.current,
            "processed": self.processed,
            "skipped": self.skipped,
            "errors": self.errors,
            "last_log": self.last_log,
            "current_item_title": self.current_item_title,
            "just_completed": self.just_completed,
        }

    def _log(self, message: str) -> None:
        self.last_log = message
        # print(f"[CryptoCarouselJob] {message}") # Pour debug en console

    def _run(self) -> None:
        """Boucle principale de génération (dans le thread)."""
        try:
            self._log("🚀 Démarrage de la génération Crypto...")

            # Étape 1 : Insertion des items (positions 1 à N)
            self._log("📤 Début insertion en DB...")
            result = insert_items_to_carousel_crypto(self._items_to_process)

            if result["status"] != "success":
                raise Exception(f"Erreur insertion : {result.get('message', 'inconnue')}")
            self._log(f"✅ Insertion OK : {result.get('inserted', 0)} items")

            # Étape 2 : Créer la cover (position 0) basée sur l'item 1
            self._log("📥 Récupération items depuis DB...")
            carousel_data = get_carousel_crypto_items()

            if carousel_data["status"] != "success" or carousel_data["count"] == 0:
                raise Exception("Erreur récupération ou 0 items")

            items = carousel_data["items"]

            self._log(f"✅ Récupérés : {len(items)} items")

            first_item = items[0]
            cover_result = upsert_carousel_crypto_cover(
                {
                    "item_id": first_item["item_id"],
                    "title": first_item["title"],
                    "content": first_item["content"],
                    "score_global": first_item["score_global"],
                    "tags": first_item["tags"],
                    "labels": first_item["labels"],
                }
            )

            if cover_result.get("status") != "success":
                raise Exception(f"Erreur cover : {cover_result.get('message', '')}")
            self._log("✅ Cover créée")

            # Étape 3 : Nettoyer le storage
            self._log("🧹 Nettoyage des caches images et slides...")
            clear_image_files()
            clear_slide_files()

            # Étape 4 : Récupérer TOUS les items (cover + items normaux)
            carousel_data = get_carousel_crypto_items()
            all_items = carousel_data["items"]
            self.total = len(all_items)  # Ajuster le total si des items ont été ajoutés/retirés

            # Étape 5 : Générer la cover (position 0)
            self._log("━━━ GÉNÉRATION COVER (position 0) ━━━")
            self.current = 1
            cover_item = next((item for item in all_items if item["position"] == 0), None)

            if cover_item:
                self.current_item_title = cover_item.get("title", "")[:40]
                self._generate_item(cover_item, is_cover=True)
                self.processed += 1

            # Étape 6 : Générer les items normaux (positions 1-N)
            content_items = [item for item in all_items if item["position"] > 0]
            content_items.sort(key=lambda x: x["position"])

            for item in content_items:
                if self._stop_event.is_set():
                    break
                self.current += 1
                self.current_item_title = item.get("title", "")[:40]
                self._log(f"━━━ GÉNÉRATION ITEM #{item['position']} ━━━")
                self._generate_item(item, is_cover=False)
                self.processed += 1
            
            if not self._stop_event.is_set():
                # Étape 7 : Générer les slides composites finales
                self._log("🖼️ Génération des slides composites...")
                self._generate_final_slides(all_items)
                self._log("✅ Slides composites générées")

                # Étape 8 : Générer la caption Instagram
                self._log("📝 Génération de la caption Instagram...")
                self._generate_caption(content_items)
                self._log("✅ Caption Instagram générée")

        except Exception as e:
            self.state = "failed"
            error_msg = f"Erreur critique : {str(e)[:200]}"
            self.errors.append(error_msg)
            self._log(f"❌ {error_msg}")
        finally:
            # Terminé
            if self._stop_event.is_set():
                self.state = "stopped"
            else:
                self.state = "completed"
                self.just_completed = True  # Notifier le frontend
                self._log(f"✅ Génération terminée ! {self.processed} items traités")

    def _generate_item(self, item: Dict, is_cover: bool) -> None:
        """Génère un item (textes + image)."""
        item_id = item["id"]
        position = item["position"]
        title = item.get("title", "")
        content = item.get("content", "")
        supabase = get_supabase()

        try:
            if is_cover:
                # Cover : seulement générer le prompt image + image (pas de textes)
                self._log("  ⏳ Génération prompt image cover...")
                prompt_result = generate_image_prompt_for_item(title, content, prompt_type="sunset")

                if prompt_result.get("status") != "success":
                    raise Exception(f"Prompt cover KO: {prompt_result.get('message', '')}")
                self._log("  ✅ Prompt image généré")

                # Sauvegarder le prompt en DB
                supabase.table("carousel_crypto").update(
                    {"prompt_image_1": prompt_result.get("image_prompt")}
                ).eq("id", item_id).execute()

                # Générer l'image
                self._log("  🎨 Génération image cover...")
                img_result = generate_and_save_carousel_image(
                    prompt_result["image_prompt"], position=0, item_id=item_id
                )

                if img_result["status"] == "success":
                    model_used = img_result.get("model_used", "inconnu")
                    self._log(f"  ✅ Image cover générée ({model_used})")
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
                supabase.table("carousel_crypto").update(
                    {
                        "title_carou": text_result["title_carou"],
                        "content_carou": text_result["content_carou"],
                        "prompt_image_1": prompt_1_result.get("image_prompt"),
                        "prompt_image_2": prompt_2_result.get("image_prompt"),
                    }
                ).eq("id", item_id).execute()
                self._log(f"  ✅ Sauvegarde DB OK")

                # Générer image
                if prompt_1_result.get("status") == "success":
                    self._log(f"  🎨 Génération image...")
                    img_result = generate_and_save_carousel_image(
                        prompt_1_result["image_prompt"], position, item_id=item_id
                    )

                    if img_result["status"] == "success":
                        model_used = img_result.get("model_used", "inconnu")
                        self._log(f"  ✅ Image générée ({model_used})")
                    else:
                        raise Exception(f"Image échec : {img_result.get('message', '')}")
                else:
                    self._log(f"  ⚠️ Pas de prompt image valide")

        except Exception as e:
            error_msg = f"Erreur item {position} : {str(e)[:120]}"
            self.errors.append(error_msg)
            self._log(f"❌ {error_msg}")
            self.skipped += 1

    def _generate_final_slides(self, all_items: List[Dict]) -> None:
        """Génère les slides composites (image + texte) et les upload."""
        supabase = get_supabase()
        
        items_sorted = sorted(
            all_items,
            key=lambda i: (0 if i.get("position") == 0 else 1, i.get("position", 999))
        )
        
        for item in items_sorted:
            item_id = item["id"]
            position = item["position"]
            title_carou = item.get("title_carou") or ""
            content_carou = item.get("content_carou") or ""
            image_url = item.get("image_url")
            
            if not image_url:
                self._log(f"⚠️ Slide {position} : URL image manquante, skip.")
                continue
            
            try:
                if position == 0:
                    slide_bytes = generate_cover_slide(image_url=image_url)
                else:
                    if not title_carou or not content_carou:
                        self._log(f"⚠️ Slide {position} : Titre ou contenu manquant, skip.")
                        continue
                    slide_bytes = generate_carousel_slide(
                        title=title_carou,
                        content=content_carou,
                        image_url=image_url
                    )
                
                upload_slide_bytes(f"slide_{position}.png", slide_bytes)
                self._log(f"✅ Slide {position} générée et uploadée.")
            except Exception as e:
                self._log(f"❌ Erreur génération slide {position}: {str(e)[:100]}")
                self.errors.append(f"Slide {position} : {str(e)[:100]}")
        
        # Upload outro slide
        outro_path = "layout/assets/carousel/crypto/outro.png"
        try:
            with open(f"/Users/gaelpons/Desktop/The Forge/{outro_path}", "rb") as f:
                outro_bytes = f.read()
            upload_slide_bytes("slide_outro.png", outro_bytes)
            self._log("✅ Slide outro uploadée.")
        except FileNotFoundError:
            self._log(f"⚠️ Slide outro non trouvée à {outro_path}")
        except Exception as e:
            self._log(f"❌ Erreur upload slide outro: {str(e)[:100]}")
            self.errors.append(f"Slide outro : {str(e)[:100]}")

    def _generate_caption(self, content_items: List[Dict]) -> None:
        """Génère la caption Instagram et l'upload."""
        try:
            # Filtrer les items sans la cover
            items_for_caption = [
                item for item in content_items
                if item.get("position") not in [0, 999]
            ]
            
            if not items_for_caption:
                self._log("⚠️ Pas d'items pour générer la caption.")
                return

            self._log("📝 Génération du texte de la caption...")
            result = generate_caption_from_items(items_for_caption)
            
            if result.get("status") != "success":
                error_msg = result.get("message", "Erreur inconnue")
                self._log(f"❌ Génération caption KO : {error_msg[:80]}")
                self.errors.append(f"Caption génération : {error_msg[:80]}")
                return
            
            caption = result["caption"]
            self._log(f"✅ Texte caption généré ({len(caption)} chars)")
            
            # Upload avec retry logic
            self._log("📤 Upload de la caption vers Storage...")
            upload_result = upload_caption_text(caption)
            
            if upload_result.get("status") != "success":
                error_msg = upload_result.get("message", "Erreur inconnue")
                self._log(f"❌ Upload caption KO : {error_msg[:80]}")
                self.errors.append(f"Caption upload : {error_msg[:80]}")
                return
            
            self._log("✅ Caption Instagram générée et uploadée")
            
        except Exception as e:
            error_msg = f"Caption : {str(e)[:150]}"
            self._log(f"❌ {error_msg}")
            self.errors.append(error_msg)


# Instance globale
_crypto_carousel_job: Optional[CryptoCarouselJob] = None


def get_crypto_carousel_job() -> CryptoCarouselJob:
    """Retourne l'instance globale du job."""
    global _crypto_carousel_job
    if _crypto_carousel_job is None:
        _crypto_carousel_job = CryptoCarouselJob()
    return _crypto_carousel_job
