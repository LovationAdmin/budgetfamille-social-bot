"""
Budget Famille - Instagram Poster (Fixed)
==========================================
Module pour publier automatiquement sur Instagram.
Meilleure gestion des cookies et timeouts.
"""

import os
import time
from pathlib import Path
from .base import BasePoster
from utils.logger import get_logger

logger = get_logger(__name__)


class InstagramPoster(BasePoster):
    """Poster pour Instagram via la version web."""
    
    PLATFORM_NAME = "instagram"
    LOGIN_URL = "https://www.instagram.com/accounts/login/"
    HOME_URL = "https://www.instagram.com/"
    
    def __init__(self, headless: bool = True):
        super().__init__(headless)
        self.username = os.getenv('INSTAGRAM_USER')
        self.password = os.getenv('INSTAGRAM_PASS')
    
    def _handle_cookie_popup(self):
        """Gère le popup de cookies Instagram."""
        cookie_selectors = [
            'button:has-text("Allow all cookies")',
            'button:has-text("Autoriser tous les cookies")',
            'button:has-text("Accept All")',
            'button:has-text("Tout accepter")',
            'button:has-text("Accept")',
            'button:has-text("Accepter")',
            'button:has-text("Allow essential and optional cookies")',
        ]
        
        for selector in cookie_selectors:
            try:
                btn = self.page.locator(selector).first
                if btn.is_visible(timeout=3000):
                    btn.click(force=True)
                    self._random_delay(2, 3)
                    logger.info("Popup cookies Instagram fermé")
                    return True
            except:
                continue
        return False
    
    def _dismiss_popups(self):
        """Ferme les popups Instagram courants."""
        self._handle_cookie_popup()
        
        popups = [
            'button:has-text("Not Now")',
            'button:has-text("Pas maintenant")',
            'button:has-text("Plus tard")',
            'button:has-text("Cancel")',
            '[aria-label="Close"]',
            '[aria-label="Fermer"]',
        ]
        
        for popup_selector in popups:
            try:
                popup = self.page.locator(popup_selector).first
                if popup.is_visible(timeout=2000):
                    popup.click(force=True)
                    self._random_delay(0.5, 1)
            except:
                continue
    
    def _check_logged_in(self) -> bool:
        """Vérifie si on est connecté à Instagram."""
        try:
            self.page.goto(self.HOME_URL, wait_until='domcontentloaded', timeout=60000)
            self._random_delay(3, 4)
            
            self._handle_cookie_popup()
            self._dismiss_popups()
            
            if 'login' in self.page.url.lower():
                return False
            
            indicators = [
                'svg[aria-label="New post"]',
                'svg[aria-label="Nouvelle publication"]',
                '[aria-label="Home"]',
                '[aria-label="Accueil"]',
            ]
            
            for indicator in indicators:
                try:
                    if self.page.locator(indicator).count() > 0:
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur vérification connexion Instagram: {e}")
            return False
    
    def _login(self) -> bool:
        """Se connecte à Instagram."""
        try:
            logger.info("Connexion à Instagram...")
            
            self.page.goto(self.LOGIN_URL, wait_until='domcontentloaded', timeout=60000)
            self._random_delay(3, 4)
            
            # Gérer les cookies EN PREMIER
            self._handle_cookie_popup()
            self._random_delay(1, 2)
            
            # Attendre le formulaire
            self.page.wait_for_selector('input[name="username"]', state='visible', timeout=15000)
            
            # Remplir le nom d'utilisateur
            username_field = self.page.locator('input[name="username"]')
            username_field.click(force=True)
            self._random_delay(0.3, 0.5)
            username_field.type(self.username, delay=50)
            
            self._random_delay(0.5, 1)
            
            # Remplir le mot de passe
            password_field = self.page.locator('input[name="password"]')
            password_field.click(force=True)
            self._random_delay(0.3, 0.5)
            password_field.type(self.password, delay=50)
            
            self._random_delay(0.5, 1)
            
            # Se connecter
            login_button = self.page.locator('button[type="submit"]')
            login_button.click(force=True)
            
            self._random_delay(5, 8)
            
            # Vérifier les challenges
            if 'challenge' in self.page.url.lower() or 'suspicious' in self.page.url.lower():
                logger.warning("⚠️ Vérification de sécurité Instagram détectée!")
                logger.warning("Connectez-vous manuellement d'abord.")
                self._take_screenshot("security_challenge")
                return False
            
            # Fermer les popups post-login
            self._dismiss_popups()
            
            self._random_delay(2, 3)
            
            if self._check_logged_in():
                logger.info("✅ Connexion Instagram réussie")
                return True
            
            logger.error("Échec de la connexion Instagram")
            return False
            
        except Exception as e:
            logger.error(f"Erreur connexion Instagram: {e}")
            self._take_screenshot("login_error")
            return False
    
    def _publish(self, text: str, image_path: str = None, video_path: str = None) -> bool:
        """Publie un post sur Instagram."""
        try:
            media_path = image_path or video_path
            
            if not media_path:
                logger.error("Instagram requiert une image ou une vidéo!")
                return False
            
            if not Path(media_path).exists():
                logger.error(f"Fichier média non trouvé: {media_path}")
                return False
            
            logger.info("Publication sur Instagram...")
            
            self.page.goto(self.HOME_URL, wait_until='domcontentloaded', timeout=60000)
            self._random_delay(2, 3)
            
            self._dismiss_popups()
            
            # Cliquer sur "Créer"
            create_selectors = [
                'svg[aria-label="New post"]',
                'svg[aria-label="Nouvelle publication"]',
                '[aria-label="Create"]',
                '[aria-label="Créer"]',
            ]
            
            clicked = False
            for selector in create_selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.is_visible(timeout=3000):
                        parent = element.locator('xpath=..')
                        parent.click(force=True)
                        clicked = True
                        break
                except:
                    continue
            
            if not clicked:
                # Essayer le menu latéral
                try:
                    self.page.locator('span:has-text("Créer"), span:has-text("Create")').first.click(force=True)
                    clicked = True
                except:
                    pass
            
            if not clicked:
                raise Exception("Bouton Créer non trouvé")
            
            self._random_delay(2, 3)
            
            # Upload du fichier
            file_input = self.page.locator('input[type="file"]').first
            file_input.set_input_files(media_path)
            
            self._random_delay(3, 5)
            
            # Cliquer sur "Suivant" (recadrage)
            next_btn = self.page.locator('button:has-text("Next"), button:has-text("Suivant")').first
            if next_btn.is_visible(timeout=5000):
                next_btn.click(force=True)
            
            self._random_delay(2, 3)
            
            # Cliquer sur "Suivant" (filtres)
            next_btn = self.page.locator('button:has-text("Next"), button:has-text("Suivant")').first
            if next_btn.is_visible(timeout=3000):
                next_btn.click(force=True)
            
            self._random_delay(2, 3)
            
            # Ajouter la légende
            caption_selectors = [
                'textarea[aria-label*="caption"]',
                'textarea[aria-label*="légende"]',
                '[contenteditable="true"]',
            ]
            
            for selector in caption_selectors:
                try:
                    field = self.page.locator(selector).first
                    if field.is_visible(timeout=3000):
                        field.click(force=True)
                        self._random_delay(0.5, 1)
                        field.type(text, delay=30)
                        break
                except:
                    continue
            
            self._random_delay(2, 3)
            
            # Partager
            share_btn = self.page.locator('button:has-text("Share"), button:has-text("Partager")').first
            if share_btn.is_visible(timeout=3000):
                share_btn.click(force=True)
            
            self._random_delay(5, 10)
            
            self._take_screenshot("published")
            logger.info("✅ Publication Instagram terminée")
            return True
            
        except Exception as e:
            logger.error(f"Erreur publication Instagram: {e}")
            self._take_screenshot("publish_error")
            return False
