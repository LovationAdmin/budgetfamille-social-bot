"""
Budget Famille - Twitter/X Poster (Fixed)
==========================================
Module pour publier automatiquement sur X (Twitter).
Support de la connexion via Google.
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
    
    def __init__(self, headless: bool = True):
        super().__init__(headless)
        self.username = os.getenv('TWITTER_USER')
        self.password = os.getenv('TWITTER_PASS')
        self.google_email = os.getenv('GOOGLE_EMAIL')
        self.google_password = os.getenv('GOOGLE_PASS')
        self.use_google_login = os.getenv('TWITTER_USE_GOOGLE', 'false').lower() == 'true'
    
    def _handle_cookie_popup(self):
        """Gère les popups de cookies."""
        cookie_selectors = [
            'button:has-text("Accept all cookies")',
            'button:has-text("Accepter tous les cookies")',
            'button:has-text("Accept")',
            'button:has-text("Accepter")',
            '[data-testid="cookie-banner-accept"]',
        ]
        
        for selector in cookie_selectors:
            try:
                btn = self.page.locator(selector).first
                if btn.is_visible(timeout=2000):
                    btn.click(force=True)
                    self._random_delay(1, 2)
                    logger.info("Popup cookies fermé")
                    return True
            except:
                continue
        return False
    
    def _dismiss_popups(self):
        """Ferme les popups X courants."""
        self._handle_cookie_popup()
        
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
                    popup.click(force=True)
                    self._random_delay(0.5, 1)
            except:
                continue
    
    def _check_logged_in(self) -> bool:
        """Vérifie si on est connecté à X."""
        try:
            self.page.goto(self.HOME_URL, wait_until='domcontentloaded', timeout=60000)
            self._random_delay(2, 3)
            
            self._handle_cookie_popup()
            
            if 'login' in self.page.url.lower() or 'flow' in self.page.url.lower():
                return False
            
            indicators = [
                '[data-testid="SideNav_NewTweet_Button"]',
                '[aria-label="Post"]',
                '[aria-label="Poster"]',
                '[data-testid="tweetTextarea_0"]',
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
    
    def _login_with_google(self) -> bool:
        """Se connecte via Google."""
        try:
            logger.info("Connexion à X via Google...")
            
            # Chercher le bouton "Sign in with Google"
            google_btn_selectors = [
                'button:has-text("Sign in with Google")',
                'button:has-text("Se connecter avec Google")',
                'div[data-provider="google"]',
                '[aria-label="Sign in with Google"]',
            ]
            
            for selector in google_btn_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if btn.is_visible(timeout=3000):
                        btn.click()
                        break
                except:
                    continue
            
            self._random_delay(3, 5)
            
            # Une nouvelle fenêtre/popup Google s'ouvre
            # Attendre et basculer vers elle
            with self.page.context.expect_page() as new_page_info:
                pass  # Le clic a déjà été fait
            
            google_page = new_page_info.value
            google_page.wait_for_load_state('domcontentloaded')
            
            # Entrer l'email Google
            email_field = google_page.locator('input[type="email"]')
            email_field.fill(self.google_email)
            google_page.locator('button:has-text("Next"), button:has-text("Suivant")').click()
            
            self._random_delay(2, 3)
            
            # Entrer le mot de passe
            password_field = google_page.locator('input[type="password"]')
            password_field.wait_for(state='visible', timeout=10000)
            password_field.fill(self.google_password)
            google_page.locator('button:has-text("Next"), button:has-text("Suivant")').click()
            
            # Attendre la redirection vers X
            self._random_delay(5, 8)
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur connexion Google: {e}")
            return False
    
    def _login(self) -> bool:
        """Se connecte à X (Twitter)."""
        try:
            logger.info("Connexion à X (Twitter)...")
            
            # Aller sur la page de login
            self.page.goto(self.LOGIN_URL, wait_until='domcontentloaded', timeout=60000)
            self._random_delay(3, 5)
            
            # Gérer les cookies
            self._handle_cookie_popup()
            
            # Option: Connexion via Google
            if self.use_google_login and self.google_email:
                if self._login_with_google():
                    return self._check_logged_in()
            
            # Connexion classique
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
            
            username_field.click(force=True)
            self._random_delay(0.3, 0.5)
            username_field.fill(self.username)
            
            self._random_delay(1, 2)
            
            # Cliquer sur "Suivant"
            next_btn = self.page.locator('button:has-text("Next"), button:has-text("Suivant")').first
            next_btn.click(force=True)
            
            self._random_delay(2, 3)
            
            # Vérifier s'il y a une vérification supplémentaire
            try:
                verification_field = self.page.locator('input[data-testid="ocfEnterTextTextInput"]').first
                if verification_field.is_visible(timeout=3000):
                    logger.info("Vérification supplémentaire demandée")
                    # Entrer l'email ou le username
                    verification_field.fill(self.username)
                    self._random_delay(1, 2)
                    self.page.locator('button:has-text("Next")').first.click(force=True)
                    self._random_delay(2, 3)
            except:
                pass
            
            # Étape 2: Entrer le mot de passe
            password_field = self.page.locator('input[type="password"]').first
            password_field.wait_for(state='visible', timeout=15000)
            
            password_field.click(force=True)
            self._random_delay(0.3, 0.5)
            password_field.fill(self.password)
            
            self._random_delay(1, 2)
            
            # Cliquer sur "Se connecter"
            login_btn = self.page.locator('button[data-testid="LoginForm_Login_Button"], button:has-text("Log in"), button:has-text("Se connecter")').first
            login_btn.click(force=True)
            
            # Attendre la redirection
            self._random_delay(5, 8)
            
            # Gérer les vérifications de sécurité
            current_url = self.page.url.lower()
            if 'challenge' in current_url or 'verify' in current_url:
                logger.warning("⚠️ Vérification de sécurité X détectée!")
                self._take_screenshot("security_challenge")
                return False
            
            # Fermer les popups
            self._dismiss_popups()
            
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
            
            # Tronquer le texte si nécessaire
            original_length = len(text)
            text = PostContent.truncate_for_twitter(text, 280)
            if len(text) < original_length:
                logger.info(f"Texte tronqué de {original_length} à {len(text)} caractères")
            
            # Aller sur l'accueil
            self.page.goto(self.HOME_URL, wait_until='domcontentloaded', timeout=60000)
            self._random_delay(2, 3)
            
            self._dismiss_popups()
            
            # Trouver le champ de texte
            tweet_box = self.page.locator('[data-testid="tweetTextarea_0"]').first
            
            if not tweet_box.is_visible(timeout=5000):
                # Cliquer sur le bouton de nouveau tweet
                new_tweet_btn = self.page.locator('[data-testid="SideNav_NewTweet_Button"]').first
                if new_tweet_btn.is_visible():
                    new_tweet_btn.click(force=True)
                    self._random_delay(2, 3)
                    tweet_box = self.page.locator('[data-testid="tweetTextarea_0"]').first
            
            if not tweet_box.is_visible(timeout=5000):
                raise Exception("Zone de texte non trouvée")
            
            tweet_box.click(force=True)
            self._random_delay(0.5, 1)
            tweet_box.type(text, delay=30)
            
            self._random_delay(1, 2)
            
            # Ajouter une image si fournie
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
            
            # Cliquer sur "Post"
            post_btn = self.page.locator('[data-testid="tweetButtonInline"], [data-testid="tweetButton"]').first
            
            if post_btn.is_visible() and post_btn.is_enabled():
                post_btn.click(force=True)
            else:
                raise Exception("Bouton Post non trouvé ou désactivé")
            
            self._random_delay(3, 5)
            
            self._take_screenshot("published")
            logger.info("✅ Publication X terminée")
            return True
            
        except Exception as e:
            logger.error(f"Erreur publication X: {e}")
            self._take_screenshot("publish_error")
            return False
