"""
Budget Famille - LinkedIn Poster (Fixed)
=========================================
Module pour publier automatiquement sur LinkedIn.
Meilleure gestion des cookies et timeouts.
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
    
    def _handle_cookie_popup(self):
        """Gère le popup de cookies LinkedIn."""
        cookie_selectors = [
            'button:has-text("Accept & Join")',
            'button:has-text("Accepter et rejoindre")',
            'button:has-text("Accept")',
            'button:has-text("Accepter")',
            'button[action-type="ACCEPT"]',
            '.artdeco-global-alert__action',
        ]
        
        for selector in cookie_selectors:
            try:
                btn = self.page.locator(selector).first
                if btn.is_visible(timeout=2000):
                    btn.click(force=True)
                    self._random_delay(1, 2)
                    logger.info("Popup cookies LinkedIn fermé")
                    return True
            except:
                continue
        return False
    
    def _check_logged_in(self) -> bool:
        """Vérifie si on est connecté à LinkedIn."""
        try:
            self.page.goto(self.FEED_URL, wait_until='domcontentloaded', timeout=60000)
            self._random_delay(2, 3)
            
            self._handle_cookie_popup()
            
            if 'login' in self.page.url.lower() or 'checkpoint' in self.page.url.lower():
                return False
            
            logged_in = self.page.locator('button[aria-label*="Start a post"], button[aria-label*="Commencer un post"], .share-box-feed-entry__trigger').count() > 0
            
            return logged_in
            
        except Exception as e:
            logger.error(f"Erreur vérification connexion: {e}")
            return False
    
    def _login(self) -> bool:
        """Se connecte à LinkedIn."""
        try:
            logger.info("Connexion à LinkedIn...")
            
            if 'login' not in self.page.url.lower():
                self.page.goto(self.LOGIN_URL, wait_until='domcontentloaded', timeout=60000)
                self._random_delay(2, 3)
            
            self._handle_cookie_popup()
            
            # Attendre le formulaire
            self.page.wait_for_selector('#username', state='visible', timeout=10000)
            
            # Remplir email
            email_field = self.page.locator('#username')
            email_field.click(force=True)
            email_field.fill('')
            self._random_delay(0.5, 1)
            email_field.type(self.email, delay=50)
            
            self._random_delay(0.5, 1)
            
            # Remplir mot de passe
            password_field = self.page.locator('#password')
            password_field.click(force=True)
            password_field.fill('')
            self._random_delay(0.5, 1)
            password_field.type(self.password, delay=50)
            
            self._random_delay(0.5, 1.5)
            
            # Se connecter
            self.page.click('button[type="submit"]', force=True)
            
            self._random_delay(5, 8)
            
            # Vérifier les challenges
            if 'checkpoint' in self.page.url.lower() or 'challenge' in self.page.url.lower():
                logger.warning("⚠️ Challenge de sécurité détecté!")
                logger.warning("Connectez-vous manuellement d'abord sur LinkedIn, puis réessayez.")
                self._take_screenshot("security_challenge")
                return False
            
            if 'feed' in self.page.url.lower():
                logger.info("✅ Connexion LinkedIn réussie")
                return True
            
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
            
            self.page.goto(self.FEED_URL, wait_until='domcontentloaded', timeout=60000)
            self._random_delay(2, 4)
            
            # Cliquer sur "Commencer un post"
            start_post_selectors = [
                'button[aria-label*="Start a post"]',
                'button[aria-label*="Commencer un post"]',
                '.share-box-feed-entry__trigger',
            ]
            
            clicked = False
            for selector in start_post_selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.is_visible(timeout=5000):
                        element.click(force=True)
                        clicked = True
                        break
                except:
                    continue
            
            if not clicked:
                raise Exception("Bouton 'Commencer un post' non trouvé")
            
            self._random_delay(2, 3)
            
            # Trouver l'éditeur
            editor = self.page.locator('.ql-editor, [role="textbox"]').first
            editor.wait_for(state='visible', timeout=10000)
            
            editor.click(force=True)
            self._random_delay(0.5, 1)
            editor.type(text, delay=30)
            
            self._random_delay(1, 2)
            
            # Ajouter une image
            if image_path and Path(image_path).exists():
                logger.info(f"Ajout de l'image: {image_path}")
                
                try:
                    file_input = self.page.locator('input[type="file"]').first
                    if file_input.count() > 0:
                        file_input.set_input_files(image_path)
                        self._random_delay(3, 5)
                        logger.info("Image ajoutée")
                except Exception as e:
                    logger.warning(f"Échec ajout image: {e}")
            
            self._random_delay(2, 3)
            
            # Publier
            publish_selectors = [
                'button.share-actions__primary-action',
                'button:has-text("Post")',
                'button:has-text("Publier")',
            ]
            
            for selector in publish_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if btn.is_visible() and btn.is_enabled():
                        btn.click(force=True)
                        break
                except:
                    continue
            
            self._random_delay(3, 5)
            
            self._take_screenshot("published")
            logger.info("✅ Publication LinkedIn terminée")
            return True
            
        except Exception as e:
            logger.error(f"Erreur publication LinkedIn: {e}")
            self._take_screenshot("publish_error")
            return False
