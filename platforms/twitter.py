"""
Budget Famille - Twitter/X Poster (Fixed v4)
=============================================
Module pour publier automatiquement sur X (Twitter).
Gestion améliorée du flow Google OAuth avec sélection de compte.
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
        self.email = os.getenv('TWITTER_EMAIL', self.username)
        # Google credentials for OAuth login
        self.google_email = os.getenv('GOOGLE_EMAIL')
        self.google_password = os.getenv('GOOGLE_PASS')
    
    def _handle_cookie_popup(self) -> bool:
        """Gère les popups de cookies X."""
        cookie_selectors = [
            '[data-testid="cookie-banner-accept"]',
            'button:has-text("Accept all cookies")',
            'button:has-text("Accepter tous les cookies")',
            'button:has-text("Accept")',
            'button:has-text("Accepter")',
            '[aria-label="Accept all cookies"]',
        ]
        
        for selector in cookie_selectors:
            try:
                btn = self.page.locator(selector).first
                if btn.is_visible(timeout=2000):
                    btn.click(force=True)
                    self._random_delay(1, 2)
                    logger.info("Popup cookies X fermé")
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
            '[data-testid="app-bar-close"]',
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
            
            current_url = self.page.url.lower()
            if 'login' in current_url or 'flow' in current_url:
                return False
            
            indicators = [
                '[data-testid="SideNav_NewTweet_Button"]',
                '[aria-label="Post"]',
                '[data-testid="tweetTextarea_0"]',
                '[data-testid="primaryColumn"]',
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
    
    def _wait_for_popup_close(self, popup, timeout: int = 30000) -> bool:
        """Attend que le popup se ferme."""
        start_time = time.time()
        timeout_sec = timeout / 1000
        
        while time.time() - start_time < timeout_sec:
            try:
                if popup.is_closed():
                    return True
            except:
                return True
            time.sleep(0.5)
        
        return False
    
    def _login_with_google(self) -> bool:
        """Connexion via Google OAuth avec gestion de la sélection de compte."""
        if not self.google_email or not self.google_password:
            logger.info("Identifiants Google non configurés")
            return False
        
        try:
            logger.info("🔍 Recherche du bouton 'Sign in with Google'...")
            
            google_btn_selectors = [
                'button:has-text("Sign in with Google")',
                'button:has-text("Sign up with Google")',
                'button:has-text("Continue with Google")',
                '[data-provider="google"]',
                'button[aria-label*="Google"]',
                'div[role="button"]:has-text("Google")',
            ]
            
            google_btn = None
            for selector in google_btn_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if btn.is_visible(timeout=3000):
                        google_btn = btn
                        logger.info(f"✅ Bouton Google trouvé: {selector}")
                        break
                except:
                    continue
            
            if not google_btn:
                logger.info("❌ Bouton Google non trouvé")
                return False
            
            logger.info("Clic sur le bouton Google...")
            self._take_screenshot("before_google_click")
            
            try:
                with self.page.context.expect_page(timeout=45000) as popup_info:
                    google_btn.click()
                
                popup = popup_info.value
                popup.wait_for_load_state('domcontentloaded', timeout=30000)
            except Exception as e:
                logger.warning(f"Pas de popup Google: {e}")
                self._random_delay(3, 5)
                return self._check_logged_in()
            
            self._random_delay(2, 3)
            self._take_screenshot("google_popup_opened")
            
            # CAS 1: Liste de comptes Google
            try:
                account_list = popup.locator('div[data-email], div[data-identifier]')
                if account_list.count() > 0:
                    logger.info("📋 Liste de comptes Google détectée")
                    
                    for selector in [f'div[data-email="{self.google_email}"]', f'div[data-identifier="{self.google_email}"]']:
                        try:
                            account = popup.locator(selector).first
                            if account.is_visible(timeout=3000):
                                logger.info(f"✅ Compte trouvé: {self.google_email}")
                                account.click()
                                self._random_delay(2, 3)
                                break
                        except:
                            continue
            except:
                pass
            
            # CAS 2: Champ email
            try:
                email_field = popup.locator('input[type="email"], #identifierId').first
                if email_field.is_visible(timeout=5000):
                    logger.info("Saisie de l'email Google...")
                    email_field.fill(self.google_email)
                    self._random_delay(1, 2)
                    popup.locator('button:has-text("Next"), button:has-text("Suivant")').first.click()
                    self._random_delay(3, 4)
            except:
                pass
            
            # CAS 3: Mot de passe
            logger.info("Attente du champ mot de passe...")
            try:
                password_field = popup.locator('input[type="password"]').first
                if password_field.is_visible(timeout=10000):
                    logger.info("Saisie du mot de passe Google...")
                    password_field.fill(self.google_password)
                    self._random_delay(1, 2)
                    popup.locator('button:has-text("Next"), button:has-text("Suivant")').first.click()
                    self._random_delay(3, 5)
            except Exception as e:
                logger.warning(f"Champ mot de passe non trouvé: {e}")
            
            # CAS 4: Autorisation
            try:
                for selector in ['button:has-text("Allow")', 'button:has-text("Continue")']:
                    try:
                        btn = popup.locator(selector).first
                        if btn.is_visible(timeout=5000):
                            btn.click()
                            self._random_delay(2, 3)
                            break
                    except:
                        continue
            except:
                pass
            
            # Attendre fermeture
            logger.info("Attente de la fermeture du popup...")
            if self._wait_for_popup_close(popup, timeout=30000):
                logger.info("Popup Google fermé")
            else:
                try:
                    popup.close()
                except:
                    pass
            
            self._random_delay(3, 5)
            self._take_screenshot("after_google_login")
            
            if self._check_logged_in():
                logger.info("✅ Connexion X via Google réussie!")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur connexion Google: {e}")
            return False
    
    def _login_classic(self) -> bool:
        """Connexion classique multi-étapes."""
        try:
            logger.info("Connexion classique à X...")
            
            if 'login' not in self.page.url.lower():
                self.page.goto(self.LOGIN_URL, wait_until='domcontentloaded', timeout=60000)
                self._random_delay(3, 5)
            
            self._handle_cookie_popup()
            
            # Étape 1: Username
            logger.info("Étape 1: Username...")
            username_field = None
            for selector in ['input[autocomplete="username"]', 'input[name="text"]']:
                try:
                    self.page.wait_for_selector(selector, state='visible', timeout=10000)
                    username_field = self.page.locator(selector).first
                    break
                except:
                    continue
            
            if not username_field:
                raise Exception("Champ username non trouvé")
            
            username_field.fill(self.username)
            self._random_delay(1, 2)
            
            self.page.locator('button:has-text("Next"), button:has-text("Suivant")').first.click()
            self._random_delay(2, 4)
            
            # Étape 2: Vérification
            try:
                verif_field = self.page.locator('input[data-testid="ocfEnterTextTextInput"]').first
                if verif_field.is_visible(timeout=3000):
                    logger.info("Vérification supplémentaire...")
                    verif_field.fill(self.email)
                    self._random_delay(1, 2)
                    self.page.locator('button:has-text("Next")').first.click()
                    self._random_delay(2, 3)
            except:
                pass
            
            # Étape 3: Password
            logger.info("Étape 2: Password...")
            password_field = None
            for selector in ['input[name="password"]', 'input[type="password"]']:
                try:
                    self.page.wait_for_selector(selector, state='visible', timeout=15000)
                    password_field = self.page.locator(selector).first
                    break
                except:
                    continue
            
            if not password_field:
                raise Exception("Champ password non trouvé")
            
            password_field.fill(self.password)
            self._random_delay(1, 2)
            
            self.page.locator('[data-testid="LoginForm_Login_Button"], button:has-text("Log in")').first.click()
            self._random_delay(5, 8)
            
            if 'challenge' in self.page.url.lower() or 'verify' in self.page.url.lower():
                logger.warning("⚠️ Vérification de sécurité X détectée!")
                return False
            
            self._dismiss_popups()
            return self._check_logged_in()
            
        except Exception as e:
            logger.error(f"Erreur connexion X: {e}")
            return False
    
    def _login(self) -> bool:
        """Connexion: Google OAuth prioritaire, puis classique."""
        try:
            logger.info("Connexion à X (Twitter)...")
            
            self.page.goto(self.LOGIN_URL, wait_until='domcontentloaded', timeout=60000)
            self._random_delay(3, 5)
            self._handle_cookie_popup()
            
            # Priorité 1: Google
            if self.google_email and self.google_password:
                logger.info("📍 Tentative Google (prioritaire)...")
                if self._login_with_google():
                    return True
                logger.info("Fallback au login classique")
                self.page.goto(self.LOGIN_URL, wait_until='domcontentloaded', timeout=60000)
                self._random_delay(2, 3)
            
            # Priorité 2: Classique
            return self._login_classic()
            
        except Exception as e:
            logger.error(f"Erreur connexion X: {e}")
            return False
    
    def _publish(self, text: str, image_path: str = None, video_path: str = None) -> bool:
        """Publie un tweet."""
        try:
            logger.info("Publication sur X...")
            
            self.page.goto(self.HOME_URL, wait_until='domcontentloaded', timeout=30000)
            self._random_delay(2, 3)
            self._dismiss_popups()
            
            text_area = None
            for selector in ['[data-testid="tweetTextarea_0"]', 'div[contenteditable="true"][role="textbox"]']:
                try:
                    area = self.page.locator(selector).first
                    if area.is_visible(timeout=5000):
                        text_area = area
                        break
                except:
                    continue
            
            if not text_area:
                self.page.locator('[data-testid="SideNav_NewTweet_Button"]').first.click()
                self._random_delay(2, 3)
                text_area = self.page.locator('[data-testid="tweetTextarea_0"]').first
            
            text_area.click()
            self._random_delay(0.5, 1)
            text_area.type(text, delay=15)
            self._random_delay(2, 3)
            
            if image_path and Path(image_path).exists():
                try:
                    self.page.locator('input[type="file"][accept*="image"]').first.set_input_files(image_path)
                    self._random_delay(3, 5)
                    logger.info("Image ajoutée")
                except:
                    pass
            
            self.page.locator('[data-testid="tweetButton"], [data-testid="tweetButtonInline"]').first.click()
            self._random_delay(3, 5)
            
            logger.info("✅ Tweet publié")
            return True
            
        except Exception as e:
            logger.error(f"Erreur publication X: {e}")
            return False