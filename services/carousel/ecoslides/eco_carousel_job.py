import threading
import time
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from db.supabase_client import get_supabase
from services.carousel.ecoslides.carousel_eco_service import (
    insert_items_to_carousel_eco,
    get_carousel_eco_items,
    upsert_carousel_eco_cover,
)
from services.carousel.ecoslides.carousel_slide_service import clear_slide_files
from services.carousel.ecoslides.generate_carousel_texts_service import (
    generate_carousel_text_for_item,
    generate_image_prompt_for_item,
    generate_all_image_prompts_parallel,
)
from services.carousel.ecoslides.carousel_image_service import generate_and_save_carousel_image


MAX_WORKERS_IMAGES = 6  # Parallélisation pour génération images
MAX_WORKERS_SLIDES = 8  # Parallélisation pour génération slides


class EcoCarouselJob:
    """Job de génération de carrousel Eco en threading pour éviter les timeouts Streamlit."""
    
    def __init__(self, use_optimized: bool = True):  # Activé par défaut pour EcoSlides
        self.state = "idle"  # idle, running, completed, failed, stopped
        self.current = 0
        self.total = 0
        self.processed = 0
        self.errors: List[str] = []
        self.last_log = ""
        self.current_item_title = ""
        self.just_completed = False  # Flag pour notifier le frontend
        self.use_optimized = use_optimized  # Active la version optimisée
        
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
            "just_completed": self.just_completed,
        }
    
    def _log(self, message: str) -> None:
        """Ajoute un log."""
        self.last_log = message
    
    def _run(self) -> None:
        """Méthode principale d'exécution."""
        if self.use_optimized:
            self._run_optimized()
        else:
            self._run_sequential()
    
    def _run_optimized(self) -> None:
        """Exécution optimisée avec parallélisation (NOUVELLE VERSION)."""
        try:
            self.state = "running"
            self.current = 0
            self.processed = 0
            self.errors = []
            
            # Étape 1 : Insertion items (accepte des IDs)
            self._log("📥 Insertion des items sélectionnés...")
            result = insert_items_to_carousel_eco(self._items)
            if result.get("status") != "success":
                raise Exception(f"Erreur insertion : {result.get('message', '')}")
            self._log(f"✅ {len(self._items)} items insérés")
            
            # Étape 2 : Récupérer les items depuis la DB (objets complets)
            self._log("📦 Récupération items depuis DB...")
            carousel_data = get_carousel_eco_items()
            
            if not isinstance(carousel_data, dict):
                raise Exception(f"carousel_data invalide (type: {type(carousel_data)})")
            
            if carousel_data.get("status") != "success":
                raise Exception(f"Erreur get_items: {carousel_data.get('message', 'Erreur inconnue')}")
            
            all_items = carousel_data.get("items", [])
            if not all_items:
                raise Exception("Aucun item récupéré")
            
            self._log(f"✅ {len(all_items)} items récupérés")
            self.total = len(all_items)
            
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
                        supabase.table("carousel_eco").update({
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
            
            cover_result = upsert_carousel_eco_cover({
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
            
            # Étape 6 : GÉNÉRATION PROMPTS IMAGES EN PARALLÈLE ⚡
            self._log("🎨 Génération prompts images (parallèle)...")
            self._log(f"📊 Debug: {len(all_items)} items à traiter")
            
            if not all_items:
                raise Exception("Aucun item à traiter")
            
            prompts_result = generate_all_image_prompts_parallel(all_items, prompt_type="sunset")
            if prompts_result.get("status") == "error":
                error_details = prompts_result.get("details", [])
                first_error = error_details[0].get("message", "Inconnue") if error_details else "Aucun détail"
                raise Exception(f"Échec génération prompts images: {first_error}")
            self._log(f"✅ {prompts_result.get('success')}/{prompts_result.get('total')} prompts générés")
            
            # Étape 7 : GÉNÉRATION IMAGES EN PARALLÈLE ⚡
            self._log("🖼️ Génération images (parallèle)...")
            images_result = generate_images_parallel(all_items, aspect_ratio="5:4")
            if images_result.get("status") == "error":
                raise Exception("Échec génération images")
            self._log(f"✅ {images_result.get('success')}/{images_result.get('total')} images générées")
            
            # Étape 8 : GÉNÉRATION SLIDES EN PARALLÈLE ⚡
            self._log("🎞️ Génération slides (parallèle)...")
            slides_result = generate_slides_parallel(all_items)
            if slides_result.get("status") == "error":
                raise Exception("Échec génération slides")
            self._log(f"✅ {slides_result.get('success')}/{slides_result.get('total')} slides générées")
            
            # Étape 9 : Upload outro
            self._log("📤 Upload outro...")
            import os
            outro_path = os.path.join(
                os.path.dirname(__file__),
                "..", "..", "..", "front", "layout", "assets", "carousel", "eco", "outro_eco.png"
            )
            if os.path.exists(outro_path):
                from services.carousel.ecoslides.carousel_slide_service import upload_slide_bytes
                with open(outro_path, "rb") as f:
                    upload_slide_bytes("slide_outro.png", f.read())
            
            # Étape 10 : Génération caption
            self._log("📝 Génération caption...")
            self._generate_caption()
            
            self.state = "completed"
            self.just_completed = True
            self.processed = len(all_items)
            self._log(f"🎉 TERMINÉ ! {self.processed} items générés (optimisé)")
            
        except Exception as e:
            self.state = "failed"
            error_msg = f"Erreur critique : {str(e)[:200]}"
            self.errors.append(error_msg)
            self._log(f"❌ {error_msg}")
    
    def _run_sequential(self) -> None:
        """Exécution séquentielle (VERSION ORIGINALE)."""
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
                # Générer les slides finales composites
                self._log("🖼️ Génération des slides finales...")
                self._generate_final_slides()
                
                # Générer la caption Instagram
                self._log("📝 Génération caption Instagram...")
                self._generate_caption()
                
                self.state = "completed"
                self.just_completed = True  # Notifier le frontend
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
            self._log(f"  🎨 Génération image cover (5:4)...")
            img_result = generate_and_save_carousel_image(
                prompt_result["image_prompt"],
                position=0,
                item_id=item_id,
                aspect_ratio="5:4"  # Format 5:4 pour la cover (1080×864)
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
                self._log(f"  🎨 Génération image (5:4)...")
                img_result = generate_and_save_carousel_image(
                    prompt_1_result["image_prompt"],
                    position,
                    item_id=item_id,
                    aspect_ratio="5:4"  # Format 5:4 pour les slides 1-N (1080×864)
                )
                
                if img_result["status"] == "success":
                    model_used = img_result.get("model_used", "inconnu")
                    self._log(f"  ✅ Image générée ({model_used})")
                else:
                    raise Exception(f"Image échec : {img_result.get('message', '')}")
            else:
                self._log(f"  ⚠️ Pas de prompt image valide")
    
    def _generate_final_slides(self) -> None:
        """Génère les slides composites finales (image + texte + overlay)."""
        import os
        from services.carousel.ecoslides.carousel_slide_service import (
            generate_carousel_slide,
            generate_cover_slide,
            upload_slide_bytes,
        )
        from services.carousel.ecoslides.carousel_image_service import read_carousel_image
        
        supabase = get_supabase()
        
        # Récupérer tous les items
        carousel_data = supabase.table("carousel_eco").select("*").order("position").execute()
        items = carousel_data.data if carousel_data.data else []
        
        for item in items:
            position = item["position"]
            item_id = item["id"]
            
            try:
                if position == 0:
                    # Cover
                    image_url = item.get("image_url")
                    image_bytes = None if image_url else read_carousel_image(position)
                    
                    if image_url or image_bytes:
                        slide_bytes = generate_cover_slide(
                            image_url=image_url,
                            image_bytes=image_bytes
                        )
                        upload_slide_bytes(f"slide_{position}.png", slide_bytes)
                        self._log(f"  ✅ Slide cover générée")
                
                else:
                    # Items normaux
                    title_carou = item.get("title_carou")
                    content_carou = item.get("content_carou")
                    image_url = item.get("image_url")
                    image_bytes = None if image_url else read_carousel_image(position)
                    
                    if title_carou and content_carou and (image_url or image_bytes):
                        slide_bytes = generate_carousel_slide(
                            title=title_carou,
                            content=content_carou,
                            image_url=image_url,
                            image_bytes=image_bytes
                        )
                        upload_slide_bytes(f"slide_{position}.png", slide_bytes)
                        self._log(f"  ✅ Slide #{position} générée")
            
            except Exception as e:
                error_msg = f"Erreur slide {position}: {str(e)[:100]}"
                self.errors.append(error_msg)
                self._log(f"  ⚠️ {error_msg}")
        
        # Upload outro
        outro_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..", "front", "layout", "assets", "carousel", "eco", "outro_eco.png"
        )
        if os.path.exists(outro_path):
            try:
                with open(outro_path, "rb") as f:
                    upload_slide_bytes("slide_outro.png", f.read())
                self._log("  ✅ Slide outro ajoutée")
            except Exception:
                pass
    
    def _generate_caption(self) -> None:
        """Génère automatiquement la caption Instagram."""
        from services.carousel.ecoslides.generate_carousel_caption_service import (
            generate_caption_from_items,
            upload_caption_text,
        )
        
        supabase = get_supabase()
        
        try:
            # Récupérer les items (sans la cover et l'outro)
            carousel_data = supabase.table("carousel_eco").select("*").order("position").execute()
            items = carousel_data.data if carousel_data.data else []
            
            # Filtrer : uniquement positions 1-N (pas 0 ni 999)
            items_for_caption = [
                item for item in items
                if item.get("position") not in [0, 999]
            ]
            
            if not items_for_caption:
                self._log("  ⚠️ Pas d'items pour la caption")
                return
            
            # Générer le texte de la caption
            self._log("  📝 Génération du texte de la caption...")
            result = generate_caption_from_items(items_for_caption)
            
            if result.get("status") != "success":
                error_msg = result.get("message", "Erreur inconnue")
                self._log(f"  ❌ Génération caption KO : {error_msg[:80]}")
                self.errors.append(f"Caption génération : {error_msg[:80]}")
                return
            
            caption = result["caption"]
            self._log(f"  ✅ Texte caption généré ({len(caption)} chars)")
            
            # Upload avec retry logic
            self._log("  📤 Upload de la caption vers Storage...")
            upload_result = upload_caption_text(caption)
            
            if upload_result.get("status") != "success":
                error_msg = upload_result.get("message", "Erreur inconnue")
                self._log(f"  ❌ Upload caption KO : {error_msg[:80]}")
                self.errors.append(f"Caption upload : {error_msg[:80]}")
                return
            
            self._log("  ✅ Caption Instagram générée et uploadée")
        
        except Exception as e:
            error_msg = f"Erreur caption : {str(e)[:100]}"
            self._log(f"  ❌ {error_msg}")
            self.errors.append(error_msg)


# Instance globale
_eco_carousel_job: Optional[EcoCarouselJob] = None


def get_eco_carousel_job() -> EcoCarouselJob:
    """Retourne l'instance globale du job."""
    global _eco_carousel_job
    if _eco_carousel_job is None:
        _eco_carousel_job = EcoCarouselJob()
    return _eco_carousel_job


def generate_images_parallel(items: List[Dict], aspect_ratio: str = "5:4") -> Dict[str, object]:
    """
    Génère toutes les images en parallèle (OPTIMISÉ).
    
    Args:
        items: Liste des items avec id, image_prompt
        aspect_ratio: Ratio d'image (5:4, 16:9, etc.)
    
    Returns:
        {
            "status": "success" | "partial" | "error",
            "total": int,
            "success": int,
            "errors": int,
            "details": [...]
        }
    """
    
    def process_single_image(item):
        """Génère une image pour un item."""
        item_id = item.get("id")
        image_prompt = item.get("image_prompt", "")
        position = item.get("position", 0)
        
        try:
            result = generate_and_save_carousel_image(
                item_id=item_id,
                image_prompt=image_prompt,
                is_cover=(position == 0),
                aspect_ratio=aspect_ratio
            )
            
            if result.get("status") == "success":
                return {
                    "item_id": item_id,
                    "position": position,
                    "status": "success",
                    "image_url": result.get("image_url")
                }
            else:
                return {
                    "item_id": item_id,
                    "position": position,
                    "status": "error",
                    "message": result.get("message", "Erreur inconnue")
                }
        except Exception as e:
            return {
                "item_id": item_id,
                "position": position,
                "status": "error",
                "message": f"Erreur: {str(e)}"
            }
    
    # Génération parallèle
    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS_IMAGES) as executor:
        futures = {executor.submit(process_single_image, item): item for item in items}
        
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({
                    "status": "error",
                    "message": f"Thread error: {str(e)}"
                })
    
    # Agréger
    total = len(items)
    success_count = sum(1 for r in results if r.get("status") == "success")
    error_count = total - success_count
    
    if success_count == total:
        status = "success"
    elif success_count > 0:
        status = "partial"
    else:
        status = "error"
    
    return {
        "status": status,
        "total": total,
        "success": success_count,
        "errors": error_count,
        "details": results
    }


def generate_slides_parallel(items: List[Dict]) -> Dict[str, object]:
    """
    Génère toutes les slides en parallèle (OPTIMISÉ).
    
    Args:
        items: Liste des items avec id, title_carou, content_carou, etc.
    
    Returns:
        {
            "status": "success" | "partial" | "error",
            "total": int,
            "success": int,
            "errors": int,
            "details": [...]
        }
    """
    import os
    from services.carousel.ecoslides.carousel_slide_service import (
        generate_carousel_slide,
        generate_cover_slide,
        upload_slide_bytes,
    )
    from services.carousel.ecoslides.carousel_image_service import read_carousel_image
    
    def process_single_slide(item):
        """Génère une slide pour un item."""
        item_id = item.get("id")
        position = item.get("position", 0)
        title = item.get("title_carou") or item.get("title", "")
        content = item.get("content_carou") or item.get("content", "")
        
        try:
            # Lire l'image depuis Supabase Storage (carousel-eco bucket)
            supabase = get_supabase()
            storage_path = f"{item_id}.png"
            
            try:
                image_bytes = supabase.storage.from_("carousel-eco").download(storage_path)
            except Exception:
                # Fallback : essayer depuis session_state/disque
                image_result = read_carousel_image(position)
                if not image_result:
                    return {
                        "item_id": item_id,
                        "position": position,
                        "status": "error",
                        "message": "Image non trouvée"
                    }
                image_bytes = image_result
            
            # Générer la slide
            if position == 0:
                slide_bytes = generate_cover_slide(image_bytes=image_bytes)
                slide_filename = "slide_0.png"
            else:
                slide_bytes = generate_carousel_slide(
                    image_bytes=image_bytes,
                    title=title,
                    content=content
                )
                slide_filename = f"slide_{position}.png"
            
            # Upload
            upload_slide_bytes(slide_filename, slide_bytes)
            
            return {
                "item_id": item_id,
                "position": position,
                "status": "success",
                "filename": slide_filename
            }
            
        except Exception as e:
            return {
                "item_id": item_id,
                "position": position,
                "status": "error",
                "message": f"Erreur: {str(e)}"
            }
    
    # Génération parallèle
    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS_SLIDES) as executor:
        futures = {executor.submit(process_single_slide, item): item for item in items}
        
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({
                    "status": "error",
                    "message": f"Thread error: {str(e)}"
                })
    
    # Agréger
    total = len(items)
    success_count = sum(1 for r in results if r.get("status") == "success")
    error_count = total - success_count
    
    if success_count == total:
        status = "success"
    elif success_count > 0:
        status = "partial"
    else:
        status = "error"
    
    return {
        "status": status,
        "total": total,
        "success": success_count,
        "errors": error_count,
        "details": results
    }
