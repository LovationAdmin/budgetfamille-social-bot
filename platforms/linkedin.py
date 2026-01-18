"""
Budget Famille - LinkedIn Poster
=================================
Module pour publier automatiquement sur LinkedIn.
"""

import os
import time
from pathlib import Path
from .base import BasePoster
from utils.logger import get_logger

logger = get_logger(__name__)


class LinkedInPoster(BasePoster):
    """Poster pour LinkedIn."""
    
    PLATFORM_NAME = "linkedin"
    LOGIN_URL = "https://www.linkedin.com/login"
    FEED_URL = "https://www.linkedin.com/feed/"
    
    def __init__(self, headless: bool = True):
        super().__init__(headless)
        self.email = os.getenv('LINKEDIN_EMAIL')
        self.password = os.getenv('LINKEDIN_PASS')
    
    def _check_logged_in(self) -> bool:
        """Vérifie si on est connecté à LinkedIn."""
        try:
            # Aller sur le feed
            self.page.goto(self.FEED_URL, wait_until='networkidle')
            self._random_delay(2, 3)
            
            # Vérifier si on est redirigé vers login
            if 'login' in self.page.url.lower() or 'checkpoint' in self.page.url.lower():
                return False
            
            # Vérifier la présence d'éléments authentifiés
            logged_in = self.page.locator('button[aria-label*="Start a post"]').count() > 0 or \
                       self.page.locator('.share-box-feed-entry__trigger').count() > 0
            
            return logged_in
            
        except Exception as e:
            logger.error(f"Erreur vérification connexion: {e}")
            return False
    
    def _login(self) -> bool:
        """Se connecte à LinkedIn."""
        try:
            logger.info("Connexion à LinkedIn...")
            
            # S'assurer d'être sur la page de login
            if 'login' not in self.page.url.lower():
                self.page.goto(self.LOGIN_URL)
                self._random_delay(2, 3)
            
            # Remplir email
            email_field = self.page.locator('#username')
            email_field.fill('')  # Clear first
            self._random_delay(0.5, 1)
            email_field.type(self.email, delay=50)
            
            self._random_delay(0.5, 1)
            
            # Remplir mot de passe
            password_field = self.page.locator('#password')
            password_field.fill('')
            self._random_delay(0.5, 1)
            password_field.type(self.password, delay=50)
            
            self._random_delay(0.5, 1.5)
            
            # Cliquer sur "Se connecter"
            self.page.click('button[type="submit"]')
            
            # Attendre la redirection
            self.page.wait_for_load_state('networkidle')
            self._random_delay(3, 5)
            
            # Gérer les éventuels challenges de sécurité
            if 'checkpoint' in self.page.url.lower() or 'challenge' in self.page.url.lower():
                logger.warning("⚠️ Challenge de sécurité détecté!")
                logger.warning("Veuillez vous connecter manuellement d'abord, puis réessayez.")
                self._take_screenshot("security_challenge")
                return False
            
            # Vérifier le succès
            if 'feed' in self.page.url.lower():
                logger.info("✅ Connexion LinkedIn réussie")
                return True
            
            # Vérifier s'il y a des erreurs
            error_element = self.page.locator('#error-for-username, #error-for-password, .form__label--error')
            if error_element.count() > 0:
                error_text = error_element.first.text_content()
                logger.error(f"Erreur de connexion: {error_text}")
                return False
            
            # Dernière vérification
            self._random_delay(2, 3)
            return self._check_logged_in()
            
        except Exception as e:
            logger.error(f"Erreur connexion LinkedIn: {e}")
            self._take_screenshot("login_error")
            return False
    
    def _publish(self, text: str, image_path: str = None, video_path: str = None) -> bool:
        """Publie un post sur LinkedIn."""
        try:
            logger.info("Publication sur LinkedIn...")
            
            # Aller sur le feed
            self.page.goto(self.FEED_URL)
            self.page.wait_for_load_state('networkidle')
            self._random_delay(2, 4)
            
            # Cliquer sur "Commencer un post"
            start_post_selectors = [
                'button[aria-label*="Start a post"]',
                'button[aria-label*="Commencer un post"]',
                '.share-box-feed-entry__trigger',
                '[data-control-name="share_box_feed"]',
            ]
            
            clicked = False
            for selector in start_post_selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.is_visible():
                        element.click()
                        clicked = True
                        break
                except:
                    continue
            
            if not clicked:
                # Essayer avec un sélecteur texte
                self.page.click('text="Commencer un post"', timeout=5000)
            
            self._random_delay(2, 3)
            
            # Attendre que le modal s'ouvre
            editor_selectors = [
                '.ql-editor',
                '[role="textbox"]',
                '.share-creation-state__text-editor',
                '[data-placeholder*="parler"]',
            ]
            
            editor = None
            for selector in editor_selectors:
                try:
                    editor = self.page.locator(selector).first
                    if editor.is_visible():
                        break
                    editor = None
                except:
                    continue
            
            if not editor:
                raise Exception("Impossible de trouver l'éditeur de texte")
            
            # Cliquer sur l'éditeur et taper le texte
            editor.click()
            self._random_delay(0.5, 1)
            
            # Taper le texte progressivement
            editor.type(text, delay=30)
            
            self._random_delay(1, 2)
            
            # Ajouter une image si fournie
            if image_path and Path(image_path).exists():
                logger.info(f"Ajout de l'image: {image_path}")
                
                media_button_selectors = [
                    'button[aria-label*="Add media"]',
                    'button[aria-label*="Ajouter un média"]',
                    'button[aria-label*="photo"]',
                    '[data-control-name="share_add_photo"]',
                ]
                
                media_clicked = False
                for selector in media_button_selectors:
                    try:
                        btn = self.page.locator(selector).first
                        if btn.is_visible():
                            btn.click()
                            media_clicked = True
                            break
                    except:
                        continue
                
                if media_clicked:
                    self._random_delay(1, 2)
                    
                    # Upload du fichier
                    file_input = self.page.locator('input[type="file"]').first
                    file_input.set_input_files(image_path)
                    
                    # Attendre le chargement
                    self._random_delay(3, 5)
                    
                    # Attendre que l'image soit chargée
                    self.page.wait_for_load_state('networkidle', timeout=30000)
                    
                    logger.info("Image ajoutée avec succès")
                else:
                    logger.warning("Bouton média non trouvé, publication sans image")
            
            # Ajouter une vidéo si fournie
            elif video_path and Path(video_path).exists():
                logger.info(f"Ajout de la vidéo: {video_path}")
                
                try:
                    # Cliquer sur le bouton vidéo
                    video_btn = self.page.locator('button[aria-label*="video"], button[aria-label*="vidéo"]').first
                    video_btn.click()
                    self._random_delay(1, 2)
                    
                    file_input = self.page.locator('input[type="file"]').first
                    file_input.set_input_files(video_path)
                    
                    # Les vidéos prennent plus de temps
                    self._random_delay(5, 10)
                    self.page.wait_for_load_state('networkidle', timeout=120000)
                    
                    logger.info("Vidéo ajoutée avec succès")
                except Exception as e:
                    logger.warning(f"Échec ajout vidéo: {e}")
            
            self._random_delay(2, 3)
            
            # Cliquer sur "Publier"
            publish_selectors = [
                'button.share-actions__primary-action',
                'button[aria-label*="Post"]',
                'button[aria-label*="Publier"]',
                'button:has-text("Publier")',
                'button:has-text("Post")',
            ]
            
            published = False
            for selector in publish_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if btn.is_visible() and btn.is_enabled():
                        btn.click()
                        published = True
                        break
                except:
                    continue
            
            if not published:
                raise Exception("Bouton Publier non trouvé ou désactivé")
            
            # Attendre la confirmation
            self._random_delay(3, 5)
            self.page.wait_for_load_state('networkidle')
            
            # Vérifier le succès (le modal se ferme)
            self._random_delay(2, 3)
            
            # Prendre un screenshot de confirmation
            self._take_screenshot("published")
            
            logger.info("✅ Publication LinkedIn terminée")
            return True
            
        except Exception as e:
            logger.error(f"Erreur publication LinkedIn: {e}")
            self._take_screenshot("publish_error")
            return False
