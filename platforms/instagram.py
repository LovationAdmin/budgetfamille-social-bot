"""
Budget Famille - Instagram Poster
==================================
Module pour publier automatiquement sur Instagram.

Note: Instagram est plus strict sur l'automatisation.
Ce module utilise la version web (instagram.com).
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
    
    def _dismiss_popups(self):
        """Ferme les popups Instagram courants."""
        popups = [
            'button:has-text("Not Now")',
            'button:has-text("Pas maintenant")',
            'button:has-text("Plus tard")',
            'button:has-text("Cancel")',
            'button:has-text("Annuler")',
            '[aria-label="Close"]',
            '[aria-label="Fermer"]',
        ]
        
        for popup_selector in popups:
            try:
                popup = self.page.locator(popup_selector).first
                if popup.is_visible(timeout=1000):
                    popup.click()
                    self._random_delay(0.5, 1)
            except:
                continue
    
    def _check_logged_in(self) -> bool:
        """Vérifie si on est connecté à Instagram."""
        try:
            self.page.goto(self.HOME_URL, wait_until='networkidle')
            self._random_delay(2, 3)
            
            # Fermer les popups
            self._dismiss_popups()
            
            # Vérifier si on est sur la page de login
            if 'login' in self.page.url.lower():
                return False
            
            # Chercher des éléments qui indiquent une connexion
            indicators = [
                'svg[aria-label="New post"]',
                'svg[aria-label="Nouvelle publication"]',
                '[aria-label="Home"]',
                '[aria-label="Accueil"]',
                'a[href*="/direct/inbox"]',
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
            
            # Aller sur la page de login
            self.page.goto(self.LOGIN_URL)
            self.page.wait_for_load_state('networkidle')
            self._random_delay(2, 3)
            
            # Accepter les cookies si demandé
            cookie_buttons = [
                'button:has-text("Accept")',
                'button:has-text("Accepter")',
                'button:has-text("Allow")',
                'button:has-text("Autoriser")',
            ]
            
            for btn_selector in cookie_buttons:
                try:
                    btn = self.page.locator(btn_selector).first
                    if btn.is_visible(timeout=2000):
                        btn.click()
                        self._random_delay(1, 2)
                        break
                except:
                    continue
            
            # Remplir le nom d'utilisateur
            username_field = self.page.locator('input[name="username"]')
            username_field.click()
            self._random_delay(0.3, 0.5)
            username_field.type(self.username, delay=50)
            
            self._random_delay(0.5, 1)
            
            # Remplir le mot de passe
            password_field = self.page.locator('input[name="password"]')
            password_field.click()
            self._random_delay(0.3, 0.5)
            password_field.type(self.password, delay=50)
            
            self._random_delay(0.5, 1)
            
            # Cliquer sur "Se connecter"
            login_button = self.page.locator('button[type="submit"]')
            login_button.click()
            
            # Attendre la redirection
            self._random_delay(5, 8)
            self.page.wait_for_load_state('networkidle')
            
            # Gérer les vérifications de sécurité
            if 'challenge' in self.page.url.lower() or 'suspicious' in self.page.url.lower():
                logger.warning("⚠️ Vérification de sécurité Instagram détectée!")
                logger.warning("Connectez-vous manuellement d'abord pour valider l'appareil.")
                self._take_screenshot("security_challenge")
                return False
            
            # Fermer les popups post-login
            self._dismiss_popups()
            
            # Popup "Enregistrer les infos de connexion"
            self._random_delay(2, 3)
            save_info_buttons = [
                'button:has-text("Not Now")',
                'button:has-text("Pas maintenant")',
            ]
            
            for btn_selector in save_info_buttons:
                try:
                    btn = self.page.locator(btn_selector).first
                    if btn.is_visible(timeout=3000):
                        btn.click()
                        break
                except:
                    continue
            
            # Vérifier le succès
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
        """
        Publie un post sur Instagram.
        
        Note: Instagram REQUIERT une image ou une vidéo pour publier.
        """
        try:
            # Instagram nécessite un média
            media_path = image_path or video_path
            
            if not media_path:
                logger.error("Instagram requiert une image ou une vidéo!")
                return False
            
            if not Path(media_path).exists():
                logger.error(f"Fichier média non trouvé: {media_path}")
                return False
            
            logger.info("Publication sur Instagram...")
            
            # Aller sur l'accueil
            self.page.goto(self.HOME_URL)
            self.page.wait_for_load_state('networkidle')
            self._random_delay(2, 3)
            
            # Fermer les popups
            self._dismiss_popups()
            
            # Cliquer sur "Créer" / "New post"
            create_selectors = [
                'svg[aria-label="New post"]',
                'svg[aria-label="Nouvelle publication"]',
                '[aria-label="Create"]',
                '[aria-label="Créer"]',
                'a[href="/create/select/"]',
            ]
            
            clicked = False
            for selector in create_selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.is_visible(timeout=2000):
                        # Pour les SVG, cliquer sur le parent
                        if 'svg' in selector:
                            element = element.locator('xpath=..')
                        element.click()
                        clicked = True
                        break
                except:
                    continue
            
            if not clicked:
                # Essayer le menu latéral
                try:
                    menu_items = self.page.locator('span:has-text("Créer"), span:has-text("Create")')
                    if menu_items.count() > 0:
                        menu_items.first.click()
                        clicked = True
                except:
                    pass
            
            if not clicked:
                raise Exception("Bouton Créer non trouvé")
            
            self._random_delay(2, 3)
            
            # Le modal de création s'ouvre
            # Sélectionner "Post" si options multiples
            try:
                post_option = self.page.locator('button:has-text("Post"), button:has-text("Publication")').first
                if post_option.is_visible(timeout=2000):
                    post_option.click()
                    self._random_delay(1, 2)
            except:
                pass
            
            # Upload du fichier
            # Instagram utilise un input file caché
            file_input = self.page.locator('input[type="file"]').first
            
            # S'assurer que l'input accepte le type de fichier
            if video_path:
                file_input.evaluate('el => el.setAttribute("accept", "video/*")')
            
            file_input.set_input_files(media_path)
            
            # Attendre le chargement
            self._random_delay(3, 5)
            
            # Gérer le recadrage (cliquer sur "Suivant" / "Next")
            next_buttons = [
                'button:has-text("Next")',
                'button:has-text("Suivant")',
                '[aria-label="Next"]',
                '[aria-label="Suivant"]',
            ]
            
            # Premier "Suivant" (recadrage)
            for btn_selector in next_buttons:
                try:
                    btn = self.page.locator(btn_selector).first
                    if btn.is_visible(timeout=5000):
                        btn.click()
                        break
                except:
                    continue
            
            self._random_delay(2, 3)
            
            # Deuxième "Suivant" (filtres) - on peut sauter
            for btn_selector in next_buttons:
                try:
                    btn = self.page.locator(btn_selector).first
                    if btn.is_visible(timeout=3000):
                        btn.click()
                        break
                except:
                    continue
            
            self._random_delay(2, 3)
            
            # Ajouter la légende
            caption_selectors = [
                'textarea[aria-label*="caption"]',
                'textarea[aria-label*="légende"]',
                'textarea[placeholder*="Write a caption"]',
                'textarea[placeholder*="Écrivez une légende"]',
                '[contenteditable="true"]',
            ]
            
            caption_field = None
            for selector in caption_selectors:
                try:
                    field = self.page.locator(selector).first
                    if field.is_visible(timeout=3000):
                        caption_field = field
                        break
                except:
                    continue
            
            if caption_field:
                caption_field.click()
                self._random_delay(0.5, 1)
                caption_field.type(text, delay=30)
            else:
                logger.warning("Champ de légende non trouvé")
            
            self._random_delay(2, 3)
            
            # Cliquer sur "Partager" / "Share"
            share_selectors = [
                'button:has-text("Share")',
                'button:has-text("Partager")',
                '[aria-label="Share"]',
                '[aria-label="Partager"]',
            ]
            
            shared = False
            for btn_selector in share_selectors:
                try:
                    btn = self.page.locator(btn_selector).first
                    if btn.is_visible(timeout=3000):
                        btn.click()
                        shared = True
                        break
                except:
                    continue
            
            if not shared:
                raise Exception("Bouton Partager non trouvé")
            
            # Attendre la publication
            self._random_delay(5, 10)
            
            # Vérifier le succès (message ou redirection)
            try:
                success_indicators = [
                    'text="Your post has been shared"',
                    'text="Votre publication a été partagée"',
                    'text="Post shared"',
                ]
                
                for indicator in success_indicators:
                    if self.page.locator(indicator).is_visible(timeout=5000):
                        logger.info("✅ Publication Instagram réussie (message de confirmation)")
                        break
            except:
                pass
            
            self._take_screenshot("published")
            logger.info("✅ Publication Instagram terminée")
            return True
            
        except Exception as e:
            logger.error(f"Erreur publication Instagram: {e}")
            self._take_screenshot("publish_error")
            return False
