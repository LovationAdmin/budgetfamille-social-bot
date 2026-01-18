"""
Budget Famille - Facebook Poster
=================================
Module pour publier automatiquement sur Facebook.

Supporte la publication sur:
- Profil personnel
- Page Facebook
"""

import os
import time
from pathlib import Path
from .base import BasePoster
from utils.logger import get_logger

logger = get_logger(__name__)


class FacebookPoster(BasePoster):
    """Poster pour Facebook."""
    
    PLATFORM_NAME = "facebook"
    LOGIN_URL = "https://www.facebook.com/login"
    HOME_URL = "https://www.facebook.com/"
    
    def __init__(self, headless: bool = True):
        super().__init__(headless)
        self.email = os.getenv('FACEBOOK_EMAIL')
        self.password = os.getenv('FACEBOOK_PASS')
        self.page_name = os.getenv('FACEBOOK_PAGE_NAME')
    
    def _dismiss_popups(self):
        """Ferme les popups Facebook courants."""
        popups = [
            'button[data-cookiebanner="accept_button"]',
            'button:has-text("Allow")',
            'button:has-text("Autoriser")',
            'button:has-text("Not Now")',
            'button:has-text("Pas maintenant")',
            '[aria-label="Close"]',
            '[aria-label="Fermer"]',
            'div[aria-label="Close"]',
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
        """Vérifie si on est connecté à Facebook."""
        try:
            self.page.goto(self.HOME_URL, wait_until='networkidle')
            self._random_delay(2, 3)
            
            # Fermer les popups
            self._dismiss_popups()
            
            # Vérifier si on est sur la page de login
            current_url = self.page.url.lower()
            if 'login' in current_url or 'checkpoint' in current_url:
                return False
            
            # Chercher des éléments qui indiquent une connexion
            indicators = [
                '[aria-label="Create a post"]',
                '[aria-label="Créer une publication"]',
                '[aria-label="Your profile"]',
                '[aria-label="Votre profil"]',
                '[aria-label="Account"]',
                '[aria-label="Compte"]',
                'div[role="navigation"]',
            ]
            
            for indicator in indicators:
                try:
                    if self.page.locator(indicator).count() > 0:
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur vérification connexion Facebook: {e}")
            return False
    
    def _login(self) -> bool:
        """Se connecte à Facebook."""
        try:
            logger.info("Connexion à Facebook...")
            
            # Aller sur la page de login
            self.page.goto(self.LOGIN_URL)
            self.page.wait_for_load_state('networkidle')
            self._random_delay(2, 3)
            
            # Accepter les cookies
            cookie_buttons = [
                'button[data-cookiebanner="accept_button"]',
                'button:has-text("Accept All")',
                'button:has-text("Tout accepter")',
                'button:has-text("Allow")',
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
            
            # Remplir l'email
            email_field = self.page.locator('#email')
            email_field.click()
            self._random_delay(0.3, 0.5)
            email_field.type(self.email, delay=50)
            
            self._random_delay(0.5, 1)
            
            # Remplir le mot de passe
            password_field = self.page.locator('#pass')
            password_field.click()
            self._random_delay(0.3, 0.5)
            password_field.type(self.password, delay=50)
            
            self._random_delay(0.5, 1)
            
            # Cliquer sur "Se connecter"
            login_button = self.page.locator('button[name="login"], button[type="submit"], #loginbutton')
            login_button.click()
            
            # Attendre la redirection
            self._random_delay(5, 8)
            self.page.wait_for_load_state('networkidle')
            
            # Gérer les vérifications de sécurité
            current_url = self.page.url.lower()
            if 'checkpoint' in current_url or 'challenge' in current_url or 'two_step_verification' in current_url:
                logger.warning("⚠️ Vérification de sécurité Facebook détectée!")
                logger.warning("Connectez-vous manuellement d'abord pour valider l'appareil.")
                self._take_screenshot("security_challenge")
                return False
            
            # Fermer les popups post-login
            self._dismiss_popups()
            
            # Vérifier le succès
            self._random_delay(2, 3)
            
            if self._check_logged_in():
                logger.info("✅ Connexion Facebook réussie")
                return True
            
            logger.error("Échec de la connexion Facebook")
            return False
            
        except Exception as e:
            logger.error(f"Erreur connexion Facebook: {e}")
            self._take_screenshot("login_error")
            return False
    
    def _go_to_page(self) -> bool:
        """Navigue vers la page Facebook (si configurée)."""
        if not self.page_name:
            return True  # Pas de page configurée, poster sur le profil
        
        try:
            logger.info(f"Navigation vers la page: {self.page_name}")
            
            # Aller dans les pages
            self.page.goto('https://www.facebook.com/pages/?category=your_pages')
            self.page.wait_for_load_state('networkidle')
            self._random_delay(2, 3)
            
            # Chercher la page par son nom
            page_link = self.page.locator(f'a:has-text("{self.page_name}")').first
            
            if page_link.is_visible(timeout=5000):
                page_link.click()
                self._random_delay(2, 3)
                logger.info(f"Page '{self.page_name}' trouvée et sélectionnée")
                return True
            else:
                logger.warning(f"Page '{self.page_name}' non trouvée, publication sur le profil")
                self.page.goto(self.HOME_URL)
                return True
                
        except Exception as e:
            logger.warning(f"Impossible d'accéder à la page: {e}")
            self.page.goto(self.HOME_URL)
            return True
    
    def _publish(self, text: str, image_path: str = None, video_path: str = None) -> bool:
        """Publie un post sur Facebook."""
        try:
            logger.info("Publication sur Facebook...")
            
            # Aller sur la page si configurée
            self._go_to_page()
            
            self.page.wait_for_load_state('networkidle')
            self._random_delay(2, 3)
            
            # Fermer les popups
            self._dismiss_popups()
            
            # Cliquer sur "À quoi pensez-vous ?" / "What's on your mind?"
            create_post_selectors = [
                '[aria-label="Create a post"]',
                '[aria-label="Créer une publication"]',
                'div[role="button"]:has-text("What\'s on your mind")',
                'div[role="button"]:has-text("À quoi pensez-vous")',
                'div[role="button"]:has-text("Quoi de neuf")',
                'span:has-text("What\'s on your mind")',
                'span:has-text("À quoi pensez-vous")',
            ]
            
            clicked = False
            for selector in create_post_selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.is_visible(timeout=3000):
                        element.click()
                        clicked = True
                        break
                except:
                    continue
            
            if not clicked:
                raise Exception("Bouton de création de post non trouvé")
            
            self._random_delay(2, 3)
            
            # Attendre que le modal s'ouvre et trouver le champ de texte
            text_field_selectors = [
                'div[contenteditable="true"][role="textbox"]',
                'div[aria-label*="What\'s on your mind"]',
                'div[aria-label*="quoi pensez-vous"]',
                'div[data-contents="true"]',
            ]
            
            text_field = None
            for selector in text_field_selectors:
                try:
                    field = self.page.locator(selector).first
                    if field.is_visible(timeout=5000):
                        text_field = field
                        break
                except:
                    continue
            
            if not text_field:
                raise Exception("Champ de texte non trouvé")
            
            # Cliquer et taper le texte
            text_field.click()
            self._random_delay(0.5, 1)
            
            # Facebook utilise contenteditable, on doit taper caractère par caractère
            text_field.type(text, delay=30)
            
            self._random_delay(2, 3)
            
            # Ajouter une image si fournie
            if image_path and Path(image_path).exists():
                logger.info(f"Ajout de l'image: {image_path}")
                
                # Chercher le bouton photo/vidéo
                media_selectors = [
                    '[aria-label="Photo/video"]',
                    '[aria-label="Photo/vidéo"]',
                    'div[role="button"]:has(svg[mask*="photo"])',
                    'i[data-visualcompletion="css-img"]:has-text("")',
                ]
                
                media_clicked = False
                for selector in media_selectors:
                    try:
                        btn = self.page.locator(selector).first
                        if btn.is_visible(timeout=3000):
                            btn.click()
                            media_clicked = True
                            break
                    except:
                        continue
                
                if media_clicked:
                    self._random_delay(1, 2)
                    
                    # Upload du fichier
                    file_input = self.page.locator('input[type="file"][accept*="image"]').first
                    if not file_input.is_visible():
                        file_input = self.page.locator('input[type="file"]').first
                    
                    file_input.set_input_files(image_path)
                    
                    # Attendre le chargement
                    self._random_delay(3, 5)
                    
                    logger.info("Image ajoutée avec succès")
                else:
                    # Essayer via drag and drop ou autre méthode
                    logger.warning("Bouton média non trouvé, essai avec input direct")
                    file_input = self.page.locator('input[type="file"]').first
                    if file_input.count() > 0:
                        file_input.set_input_files(image_path)
                        self._random_delay(3, 5)
            
            # Ajouter une vidéo si fournie
            elif video_path and Path(video_path).exists():
                logger.info(f"Ajout de la vidéo: {video_path}")
                
                try:
                    file_input = self.page.locator('input[type="file"][accept*="video"]').first
                    if not file_input.is_visible():
                        file_input = self.page.locator('input[type="file"]').first
                    
                    file_input.set_input_files(video_path)
                    
                    # Les vidéos prennent plus de temps
                    self._random_delay(5, 10)
                    
                    logger.info("Vidéo ajoutée avec succès")
                except Exception as e:
                    logger.warning(f"Échec ajout vidéo: {e}")
            
            self._random_delay(2, 3)
            
            # Cliquer sur "Publier" / "Post"
            publish_selectors = [
                'div[aria-label="Post"][role="button"]',
                'div[aria-label="Publier"][role="button"]',
                'span:has-text("Post"):visible',
                'span:has-text("Publier"):visible',
            ]
            
            published = False
            for selector in publish_selectors:
                try:
                    # Chercher le bouton dans le modal
                    btn = self.page.locator(selector).last  # Souvent c'est le dernier
                    if btn.is_visible(timeout=3000):
                        btn.click()
                        published = True
                        break
                except:
                    continue
            
            if not published:
                # Essayer avec un sélecteur plus générique
                try:
                    all_buttons = self.page.locator('div[role="button"]')
                    for i in range(all_buttons.count()):
                        btn = all_buttons.nth(i)
                        text = btn.text_content()
                        if text and ('Post' in text or 'Publier' in text):
                            btn.click()
                            published = True
                            break
                except:
                    pass
            
            if not published:
                raise Exception("Bouton Publier non trouvé")
            
            # Attendre la publication
            self._random_delay(5, 8)
            self.page.wait_for_load_state('networkidle')
            
            self._take_screenshot("published")
            logger.info("✅ Publication Facebook terminée")
            return True
            
        except Exception as e:
            logger.error(f"Erreur publication Facebook: {e}")
            self._take_screenshot("publish_error")
            return False
