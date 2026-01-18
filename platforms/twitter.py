"""
Budget Famille - Twitter/X Poster
==================================
Module pour publier automatiquement sur X (Twitter).
"""

import os
import time
from pathlib import Path
from .base import BasePoster, PostContent
from utils.logger import get_logger

logger = get_logger(__name__)


class TwitterPoster(BasePoster):
    """Poster pour X (Twitter)."""
    
    PLATFORM_NAME = "twitter"
    LOGIN_URL = "https://x.com/i/flow/login"
    HOME_URL = "https://x.com/home"
    COMPOSE_URL = "https://x.com/compose/tweet"
    
    def __init__(self, headless: bool = True):
        super().__init__(headless)
        self.username = os.getenv('TWITTER_USER')
        self.password = os.getenv('TWITTER_PASS')
    
    def _dismiss_popups(self):
        """Ferme les popups X courants."""
        popups = [
            'div[data-testid="confirmationSheetConfirm"]',
            '[aria-label="Close"]',
            '[aria-label="Fermer"]',
            'button:has-text("Not now")',
            'button:has-text("Pas maintenant")',
            'button:has-text("Maybe later")',
            'button:has-text("Skip for now")',
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
        """Vérifie si on est connecté à X."""
        try:
            self.page.goto(self.HOME_URL, wait_until='networkidle')
            self._random_delay(2, 3)
            
            # Vérifier si on est redirigé vers login
            if 'login' in self.page.url.lower() or 'flow' in self.page.url.lower():
                return False
            
            # Chercher des éléments qui indiquent une connexion
            indicators = [
                '[data-testid="SideNav_NewTweet_Button"]',
                '[aria-label="Post"]',
                '[aria-label="Poster"]',
                '[data-testid="tweetTextarea_0"]',
                'a[href="/compose/tweet"]',
            ]
            
            for indicator in indicators:
                try:
                    if self.page.locator(indicator).count() > 0:
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur vérification connexion X: {e}")
            return False
    
    def _login(self) -> bool:
        """Se connecte à X (Twitter)."""
        try:
            logger.info("Connexion à X (Twitter)...")
            
            # Aller sur la page de login
            self.page.goto(self.LOGIN_URL)
            self.page.wait_for_load_state('networkidle')
            self._random_delay(3, 5)
            
            # Étape 1: Entrer le nom d'utilisateur
            username_selectors = [
                'input[autocomplete="username"]',
                'input[name="text"]',
                'input[type="text"]',
            ]
            
            username_field = None
            for selector in username_selectors:
                try:
                    field = self.page.locator(selector).first
                    if field.is_visible(timeout=5000):
                        username_field = field
                        break
                except:
                    continue
            
            if not username_field:
                raise Exception("Champ nom d'utilisateur non trouvé")
            
            username_field.click()
            self._random_delay(0.3, 0.5)
            username_field.type(self.username, delay=50)
            
            self._random_delay(1, 2)
            
            # Cliquer sur "Suivant"
            next_button = self.page.locator('button:has-text("Next"), button:has-text("Suivant"), div[role="button"]:has-text("Next")').first
            next_button.click()
            
            self._random_delay(2, 3)
            
            # Vérifier s'il y a une vérification supplémentaire (email ou téléphone)
            unusual_activity = self.page.locator('text="unusual login activity"')
            if unusual_activity.is_visible(timeout=2000):
                logger.warning("⚠️ X demande une vérification supplémentaire")
                verification_field = self.page.locator('input[data-testid="ocfEnterTextTextInput"]').first
                if verification_field.is_visible():
                    email = os.getenv('TWITTER_EMAIL', self.username)
                    verification_field.type(email, delay=50)
                    self._random_delay(1, 2)
                    next_button = self.page.locator('button:has-text("Next")').first
                    next_button.click()
                    self._random_delay(2, 3)
            
            # Étape 2: Entrer le mot de passe
            password_field = self.page.locator('input[type="password"]').first
            
            if not password_field.is_visible(timeout=10000):
                raise Exception("Champ mot de passe non trouvé")
            
            password_field.click()
            self._random_delay(0.3, 0.5)
            password_field.type(self.password, delay=50)
            
            self._random_delay(1, 2)
            
            # Cliquer sur "Se connecter"
            login_button = self.page.locator('button[data-testid="LoginForm_Login_Button"], button:has-text("Log in"), button:has-text("Se connecter")').first
            login_button.click()
            
            # Attendre la redirection
            self._random_delay(5, 8)
            self.page.wait_for_load_state('networkidle')
            
            # Gérer les vérifications de sécurité
            current_url = self.page.url.lower()
            if 'challenge' in current_url or 'verify' in current_url or 'suspicious' in current_url:
                logger.warning("⚠️ Vérification de sécurité X détectée!")
                logger.warning("Connectez-vous manuellement d'abord pour valider l'appareil.")
                self._take_screenshot("security_challenge")
                return False
            
            # Fermer les popups post-login
            self._dismiss_popups()
            
            # Vérifier le succès
            self._random_delay(2, 3)
            
            if self._check_logged_in():
                logger.info("✅ Connexion X réussie")
                return True
            
            logger.error("Échec de la connexion X")
            return False
            
        except Exception as e:
            logger.error(f"Erreur connexion X: {e}")
            self._take_screenshot("login_error")
            return False
    
    def _publish(self, text: str, image_path: str = None, video_path: str = None) -> bool:
        """Publie un tweet sur X."""
        try:
            logger.info("Publication sur X (Twitter)...")
            
            # Tronquer le texte si nécessaire (280 caractères)
            original_length = len(text)
            text = PostContent.truncate_for_twitter(text, 280)
            if len(text) < original_length:
                logger.info(f"Texte tronqué de {original_length} à {len(text)} caractères")
            
            # Aller sur la page de composition ou l'accueil
            self.page.goto(self.HOME_URL)
            self.page.wait_for_load_state('networkidle')
            self._random_delay(2, 3)
            
            # Fermer les popups
            self._dismiss_popups()
            
            # Chercher le champ de texte sur l'accueil ou cliquer sur le bouton "Post"
            tweet_box = self.page.locator('[data-testid="tweetTextarea_0"]').first
            
            if not tweet_box.is_visible(timeout=5000):
                # Cliquer sur le bouton de nouveau tweet
                new_tweet_btn = self.page.locator('[data-testid="SideNav_NewTweet_Button"], a[href="/compose/tweet"]').first
                if new_tweet_btn.is_visible():
                    new_tweet_btn.click()
                    self._random_delay(2, 3)
                    tweet_box = self.page.locator('[data-testid="tweetTextarea_0"]').first
            
            if not tweet_box.is_visible(timeout=5000):
                raise Exception("Zone de texte non trouvée")
            
            # Cliquer sur la zone de texte et taper
            tweet_box.click()
            self._random_delay(0.5, 1)
            
            # Taper le texte caractère par caractère
            tweet_box.type(text, delay=30)
            
            self._random_delay(1, 2)
            
            # Ajouter une image si fournie
            if image_path and Path(image_path).exists():
                logger.info(f"Ajout de l'image: {image_path}")
                
                # Chercher le bouton média
                media_btn = self.page.locator('[data-testid="fileInput"]').first
                
                if media_btn.count() == 0:
                    media_btn = self.page.locator('input[type="file"][accept*="image"]').first
                
                if media_btn.count() == 0:
                    media_btn = self.page.locator('input[type="file"]').first
                
                if media_btn.count() > 0:
                    media_btn.set_input_files(image_path)
                    
                    # Attendre le chargement de l'image
                    self._random_delay(3, 5)
                    
                    try:
                        self.page.wait_for_selector('[data-testid="attachments"]', timeout=10000)
                        logger.info("Image ajoutée avec succès")
                    except:
                        logger.warning("Image peut-être non chargée correctement")
                else:
                    logger.warning("Input file non trouvé, publication sans image")
            
            # Ajouter une vidéo si fournie
            elif video_path and Path(video_path).exists():
                logger.info(f"Ajout de la vidéo: {video_path}")
                
                try:
                    file_input = self.page.locator('input[type="file"]').first
                    file_input.set_input_files(video_path)
                    
                    # Les vidéos prennent plus de temps à charger
                    self._random_delay(5, 10)
                    
                    # Attendre le traitement de la vidéo
                    self.page.wait_for_selector('[data-testid="attachments"]', timeout=60000)
                    
                    logger.info("Vidéo ajoutée avec succès")
                except Exception as e:
                    logger.warning(f"Échec ajout vidéo: {e}")
            
            self._random_delay(2, 3)
            
            # Cliquer sur le bouton "Post" / "Poster"
            post_button_selectors = [
                '[data-testid="tweetButtonInline"]',
                '[data-testid="tweetButton"]',
                'button[data-testid="tweetButtonInline"]',
                'div[data-testid="tweetButtonInline"]',
            ]
            
            posted = False
            for selector in post_button_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if btn.is_visible(timeout=3000):
                        # Vérifier que le bouton est activé
                        if btn.is_enabled():
                            btn.click()
                            posted = True
                            break
                except:
                    continue
            
            if not posted:
                raise Exception("Bouton Post non trouvé ou désactivé")
            
            # Attendre la publication
            self._random_delay(3, 5)
            
            # Vérifier le succès (le champ de texte se vide)
            try:
                self.page.wait_for_selector('[data-testid="toast"]', timeout=5000)
                logger.info("Toast de confirmation détecté")
            except:
                pass
            
            self._take_screenshot("published")
            logger.info("✅ Publication X terminée")
            return True
            
        except Exception as e:
            logger.error(f"Erreur publication X: {e}")
            self._take_screenshot("publish_error")
            return False
