import threading
import time
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import streamlit as st

from db.supabase_client import get_supabase
from services.carousel.pea.carousel_pea_service import (
    insert_items_to_carousel_pea,
    get_carousel_pea_items,
    upsert_carousel_pea_cover,
)
from services.carousel.pea.carousel_image_service import (
    clear_image_files,
    generate_and_save_carousel_image,
    read_carousel_image,
)
from services.carousel.pea.carousel_slide_service import (
    clear_slide_files,
    generate_carousel_slide,
    generate_cover_slide,
    upload_slide_bytes,
)
from services.carousel.pea.generate_carousel_texts_service import (
    generate_carousel_text_for_item,
    generate_image_prompt_for_item,
)
from services.carousel.pea.generate_carousel_caption_service import (
    generate_caption_from_items,
    upload_caption_text,
)


class PeaCarouselJob:
    """
    Gère la génération complète d'un carrousel Pea en arrière-plan (threading).
    """

    def __init__(self, use_optimized: bool = True) -> None:
        self.state = "idle"  # idle, running, completed, failed, stopped
        self.total = 0
        self.current = 0
        self.processed = 0
        self.skipped = 0
        self.errors: List[str] = []
        self.last_log: str = ""
        self.current_item_title: str = ""
        self.just_completed: bool = False  # Flag pour notifier le frontend
        self.use_optimized = use_optimized  # Parallélisation activée par défaut

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
        # print(f"[PeaCarouselJob] {message}") # Pour debug en console

    def _run(self) -> None:
        """Dispatcher : Choix entre mode optimisé (parallèle) ou séquentiel."""
        if self.use_optimized:
            self._run_optimized()
        else:
            self._run_sequential()

    def _run_sequential(self) -> None:
        """Boucle principale de génération (dans le thread) - MODE SÉQUENTIEL."""
        try:
            self._log("🚀 Démarrage de la génération Pea...")

            # Étape 1 : Insertion des items (positions 1 à N)
            self._log("📤 Début insertion en DB...")
            result = insert_items_to_carousel_pea(self._items_to_process)

            if result["status"] != "success":
                raise Exception(f"Erreur insertion : {result.get('message', 'inconnue')}")
            self._log(f"✅ Insertion OK : {result.get('inserted', 0)} items")

            # Étape 2 : Créer la cover (position 0) basée sur l'item 1
            self._log("📥 Récupération items depuis DB...")
            carousel_data = get_carousel_pea_items()

            if carousel_data["status"] != "success" or carousel_data["count"] == 0:
                raise Exception("Erreur récupération ou 0 items")

            items = carousel_data["items"]

            self._log(f"✅ Récupérés : {len(items)} items")

            first_item = items[0]
            cover_result = upsert_carousel_pea_cover(
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
            carousel_data = get_carousel_pea_items()
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

    def _run_optimized(self) -> None:
        """Boucle optimisée avec parallélisation des prompts, images et slides."""
        try:
            self._log("🚀⚡ Démarrage génération Pea (MODE OPTIMISÉ)")
            
            # Étape 1 : Insertion items
            self._log("📤 Insertion items en DB...")
            result = insert_items_to_carousel_pea(self._items_to_process)
            if result.get("status") != "success":
                raise Exception(f"Erreur insertion: {result.get('message', 'Erreur inconnue')}")
            self._log(f"✅ {result.get('inserted', 0)} items insérés")
            
            # Étape 2 : Récupérer items
            carousel_data = get_carousel_pea_items()
            if carousel_data.get("status") != "success":
                raise Exception(f"Erreur get_items: {carousel_data.get('message', 'Erreur inconnue')}")
            
            all_items = carousel_data.get("items", [])
            if not all_items:
                raise Exception("Aucun item récupéré")
            
            self._log(f"✅ {len(all_items)} items récupérés")
            
            # Étape 3 : Génération textes carrousel (séquentiel)
            self._log("✍️ Génération textes carrousel...")
            
            try:
                content_items = [item for item in all_items if item.get("position", -1) > 0]
                
                for item in content_items:
                    if self._stop_event.is_set():
                        break
                    
                    if not isinstance(item, dict):
                        continue
                    
                    title = item.get("title", "")
                    content = item.get("content", "")
                    text_result = generate_carousel_text_for_item(title, content)
                    
                    if text_result.get("status") == "success":
                        supabase = get_supabase()
                        supabase.table("carousel_pea").update({
                            "title_carou": text_result.get("title_carou"),
                            "content_carou": text_result.get("content_carou")
                        }).eq("id", item["id"]).execute()
                
                self._log("✅ Textes générés")
                
            except Exception as e:
                raise Exception(f"Erreur génération textes: {str(e)}")
            
            # Étape 4 : Génération cover
            first_item = all_items[0] if all_items else None
            if not first_item:
                raise Exception("Aucun premier item")
            
            cover_result = upsert_carousel_pea_cover({
                "item_id": first_item.get("item_id", ""),
                "title": first_item.get("title", ""),
                "content": first_item.get("content", ""),
                "score_global": first_item.get("score_global", 0),
                "tags": first_item.get("tags", ""),
                "labels": first_item.get("labels", ""),
            })
            if cover_result.get("status") != "success":
                raise Exception(f"Erreur cover : {cover_result.get('message', '')}")
            self._log("✅ Cover créée")
            
            # Étape 5 : Nettoyer caches
            self._log("🧹 Nettoyage caches...")
            clear_slide_files()
            
            # Re-récupérer tous les items (maintenant avec la cover ajoutée)
            carousel_data = get_carousel_pea_items()
            all_items = carousel_data.get("items", [])
            
            # Calculer le total maintenant (avec cover incluse)
            # Total = nombre d'items × 3 phases (prompts + images + slides)
            self.total = len(all_items) * 3
            self._log(f"📊 Total à générer : {len(all_items)} items × 3 phases = {self.total}")
            
            # Étape 6 : GÉNÉRATION PROMPTS IMAGES EN PARALLÈLE ⚡
            self._log("🎨 Génération prompts images (parallèle)...")
            self._log(f"📊 {len(all_items)} items à traiter")
            
            if not all_items:
                raise Exception("Aucun item à traiter")
            
            # Callback pour mise à jour progression (incrémental global)
            def on_prompt_complete(item_id, position, success):
                self.current += 1
                status_icon = "✅" if success else "❌"
                self._log(f"  {status_icon} Prompt #{position} ({self.current}/{self.total})")
            
            # Import de la fonction parallèle
            from services.carousel.pea.generate_carousel_texts_service import generate_all_image_prompts_parallel
            
            prompts_result = generate_all_image_prompts_parallel(all_items, prompt_type="sunset", progress_callback=on_prompt_complete)
            if prompts_result.get("status") == "error":
                error_details = prompts_result.get("details", [])
                first_error = error_details[0].get("message", "Inconnue") if error_details else "Aucun détail"
                raise Exception(f"Échec génération prompts images: {first_error}")
            self._log(f"✅ {prompts_result.get('success')}/{prompts_result.get('total')} prompts générés")
            
            # Re-récupérer les items pour avoir les prompts fraîchement générés
            carousel_data = get_carousel_pea_items()
            all_items = carousel_data.get("items", [])
            
            # Étape 7 : GÉNÉRATION IMAGES EN PARALLÈLE ⚡
            self._log("🖼️ Génération images (parallèle)...")
            
            # Callback pour mise à jour progression (incrémental global)
            def on_image_complete(item_id, position, success):
                self.current += 1
                status_icon = "✅" if success else "❌"
                self._log(f"  {status_icon} Image #{position} ({self.current}/{self.total})")
            
            images_result = generate_images_parallel(all_items, aspect_ratio="5:4", progress_callback=on_image_complete)
            if images_result.get("status") == "error":
                raise Exception("Échec génération images")
            self._log(f"✅ {images_result.get('success')}/{images_result.get('total')} images générées")
            
            # Pas besoin de re-fetch : les slides lisent directement depuis Supabase Storage
            
            # Étape 8 : GÉNÉRATION SLIDES EN PARALLÈLE ⚡
            self._log("🎞️ Génération slides (parallèle)...")
            
            # Callback pour mise à jour progression (incrémental global)
            def on_slide_complete(item_id, position, success):
                self.current += 1
                status_icon = "✅" if success else "❌"
                self._log(f"  {status_icon} Slide #{position} ({self.current}/{self.total})")
            
            slides_result = generate_slides_parallel(all_items, progress_callback=on_slide_complete)
            if slides_result.get("status") == "error":
                raise Exception("Échec génération slides")
            self._log(f"✅ {slides_result.get('success')}/{slides_result.get('total')} slides générées")
            
            # Étape 9 : Upload outro
            self._log("📤 Upload outro...")
            import os
            outro_path = os.path.join(
                os.path.dirname(__file__),
                "..", "..", "..", "front", "layout", "assets", "carousel", "pea", "outro_pea.png"
            )
            if os.path.exists(outro_path):
                from services.carousel.pea.carousel_slide_service import upload_slide_bytes
                with open(outro_path, "rb") as f:
                    upload_slide_bytes("slide_outro.png", f.read())
            
            # Étape 10 : Génération caption
            self._log("📝 Génération caption...")
            content_items = [item for item in all_items if item.get("position", -1) > 0]
            self._generate_caption(content_items)
            
            self.state = "completed"
            self.just_completed = True
            self.processed = len(all_items)
            self._log(f"🎉 TERMINÉ ! {self.processed} items générés (optimisé)")
            
        except Exception as e:
            self.state = "failed"
            error_msg = f"Erreur critique : {str(e)[:200]}"
            self.errors.append(error_msg)
            self._log(f"❌ {error_msg}")
        finally:
            if self._stop_event.is_set():
                self.state = "stopped"

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
                supabase.table("carousel_pea").update(
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
                supabase.table("carousel_pea").update(
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
        outro_path = "front/layout/assets/carousel/pea/outro_pea.png"
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


# ═════════════════════════════════════════════════════════════════════════
# FONCTIONS PARALLÈLES (UTILISÉES PAR _run_optimized)
# ═════════════════════════════════════════════════════════════════════════

def generate_images_parallel(all_items: List[Dict], aspect_ratio: str = "5:4", progress_callback=None) -> Dict:
    """
    Génère toutes les images en parallèle (6 threads max).
    Lit les prompts depuis la DB, génère et upload dans Supabase Storage.
    """
    MAX_WORKERS_IMAGES = 6
    success_count = 0
    error_count = 0
    results = []
    
    def generate_one_image(item):
        """Génère une seule image pour un item."""
        item_id = item.get("id")
        position = item.get("position")
        image_prompt = item.get("prompt_image_1")
        
        if not image_prompt:
            return {"success": False, "item_id": item_id, "position": position, "message": "Pas de prompt"}
        
        try:
            result = generate_and_save_carousel_image(
                image_prompt,
                position,
                item_id=item_id,
                aspect_ratio=aspect_ratio
            )
            success = result.get("status") == "success"
            if progress_callback:
                progress_callback(item_id, position, success)
            return {
                "success": success,
                "item_id": item_id,
                "position": position,
                "message": result.get("message", "OK") if success else result.get("message", "Erreur inconnue")
            }
        except Exception as e:
            if progress_callback:
                progress_callback(item_id, position, False)
            return {"success": False, "item_id": item_id, "position": position, "message": str(e)}
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS_IMAGES) as executor:
        futures = {executor.submit(generate_one_image, item): item for item in all_items}
        
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            if result["success"]:
                success_count += 1
            else:
                error_count += 1
    
    return {
        "status": "success" if error_count == 0 else "partial" if success_count > 0 else "error",
        "total": len(all_items),
        "success": success_count,
        "errors": error_count,
        "details": results
    }


def generate_slides_parallel(all_items: List[Dict], progress_callback=None) -> Dict:
    """
    Génère toutes les slides en parallèle (8 threads max).
    Lit les images depuis Supabase Storage, génère et upload les slides.
    """
    MAX_WORKERS_SLIDES = 8
    success_count = 0
    error_count = 0
    results = []
    supabase = get_supabase()
    
    def generate_one_slide(item):
        """Génère une seule slide pour un item."""
        item_id = item.get("id")
        position = item.get("position")
        title_carou = item.get("title_carou", "")
        content_carou = item.get("content_carou", "")
        
        try:
            # Récupérer l'image depuis Supabase Storage
            bucket_name = "carousel-pea"
            filename = f"image_{item_id}.png"
            
            try:
                image_bytes = supabase.storage.from_(bucket_name).download(filename)
            except Exception:
                # Fallback : essayer de lire depuis le cache local
                image_bytes = read_carousel_image(position)
            
            if not image_bytes:
                raise Exception("Image introuvable")
            
            # Générer la slide
            if position == 0:
                slide_bytes = generate_cover_slide(image_bytes=image_bytes)
            else:
                if not title_carou or not content_carou:
                    raise Exception("Titre/contenu manquant")
                slide_bytes = generate_carousel_slide(
                    title=title_carou,
                    content=content_carou,
                    image_bytes=image_bytes
                )
            
            # Upload
            upload_slide_bytes(f"slide_{position}.png", slide_bytes)
            
            if progress_callback:
                progress_callback(item_id, position, True)
            
            return {"success": True, "item_id": item_id, "position": position}
            
        except Exception as e:
            if progress_callback:
                progress_callback(item_id, position, False)
            return {"success": False, "item_id": item_id, "position": position, "message": str(e)}
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS_SLIDES) as executor:
        futures = {executor.submit(generate_one_slide, item): item for item in all_items}
        
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            if result["success"]:
                success_count += 1
            else:
                error_count += 1
    
    return {
        "status": "success" if error_count == 0 else "partial" if success_count > 0 else "error",
        "total": len(all_items),
        "success": success_count,
        "errors": error_count,
        "details": results
    }


# Instance globale
_pea_carousel_job: Optional[PeaCarouselJob] = None


def get_pea_carousel_job() -> PeaCarouselJob:
    """Retourne l'instance globale du job (avec optimisation activée par défaut)."""
    global _pea_carousel_job
    if _pea_carousel_job is None:
        _pea_carousel_job = PeaCarouselJob(use_optimized=True)
    return _pea_carousel_job


def reset_pea_carousel_job() -> None:
    """Réinitialise l'instance globale (pour debug)."""
    global _pea_carousel_job
    _pea_carousel_job = None
