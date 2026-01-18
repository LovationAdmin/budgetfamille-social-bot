"""
Budget Famille - Facebook Poster (Fixed v2)
============================================
Module pour publier automatiquement sur Facebook.
Gestion robuste des popups de cookies avec attente de l'overlay.
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
    
    def _handle_cookie_popup(self) -> bool:
        """
        Gère le popup de cookies Facebook - DOIT être appelé en premier.
        Utilise une stratégie multi-niveaux pour gérer l'overlay.
        """
        logger.info("Recherche du popup de cookies...")
        
        try:
            # Attendre que la page soit complètement chargée
            self.page.wait_for_load_state('networkidle', timeout=10000)
        except:
            pass
        
        self._random_delay(1, 2)
        
        # Stratégie 1: Clic direct avec JavaScript sur le bouton du cookie dialog
        try:
            result = self.page.evaluate("""
                () => {
                    // Chercher le dialogue de cookies par data-testid
                    const dialog = document.querySelector('[data-testid="cookie-policy-manage-dialog"]');
                    if (dialog) {
                        // Chercher le bouton "Autoriser" ou "Allow" dans le dialogue
                        const buttons = dialog.querySelectorAll('div[role="button"]');
                        for (const btn of buttons) {
                            const text = btn.textContent.toLowerCase();
                            // Premier bouton est généralement "Autoriser tous les cookies"
                            if (text.includes('autoriser') || text.includes('allow') || 
                                text.includes('accepter') || text.includes('accept') ||
                                text.includes('essential') || text.includes('essentiel')) {
                                btn.click();
                                return 'clicked_dialog_button';
                            }
                        }
                        // Si pas de texte trouvé, cliquer sur le premier bouton principal
                        const primaryBtn = dialog.querySelector('div[aria-label*="cookies"], div[role="button"]');
                        if (primaryBtn) {
                            primaryBtn.click();
                            return 'clicked_primary';
                        }
                    }
                    
                    // Chercher les boutons génériques
                    const allButtons = document.querySelectorAll('button, div[role="button"]');
                    for (const btn of allButtons) {
                        const text = btn.textContent.toLowerCase();
                        if ((text.includes('autoriser') && text.includes('cookie')) ||
                            (text.includes('allow') && text.includes('cookie')) ||
                            text.includes('tout accepter') ||
                            text.includes('accept all') ||
                            text === 'autoriser les cookies essentiels et optionnels' ||
                            text === 'allow all cookies') {
                            btn.click();
                            return 'clicked_generic';
                        }
                    }
                    
                    return 'no_popup_found';
                }
            """)
            
            if result and result != 'no_popup_found':
                logger.info(f"Popup cookies fermé via JavaScript: {result}")
                self._random_delay(2, 3)
                return True
                
        except Exception as e:
            logger.debug(f"Stratégie JS échouée: {e}")
        
        # Stratégie 2: Utiliser les sélecteurs Playwright avec force click
        cookie_selectors = [
            # Sélecteurs spécifiques Facebook 2024/2025
            '[data-testid="cookie-policy-manage-dialog"] div[role="button"]:first-of-type',
            '[data-cookiebanner="accept_button"]',
            'button[data-testid="cookie-policy-manage-dialog-accept-button"]',
            # Sélecteurs par texte
            'div[role="button"]:has-text("Autoriser les cookies essentiels et optionnels")',
            'div[role="button"]:has-text("Allow all cookies")',
            'div[role="button"]:has-text("Tout accepter")',
            'div[role="button"]:has-text("Accept all")',
            'button:has-text("Tout accepter")',
            'button:has-text("Allow all cookies")',
            # Sélecteurs par aria-label
            '[aria-label*="Autoriser"][aria-label*="cookies"]',
            '[aria-label*="Allow"][aria-label*="cookies"]',
            '[aria-label="Tout accepter"]',
            '[aria-label="Allow all cookies"]',
        ]
        
        for selector in cookie_selectors:
            try:
                btn = self.page.locator(selector).first
                if btn.is_visible(timeout=1500):
                    # Utiliser dispatch_event pour contourner l'overlay
                    btn.dispatch_event('click')
                    logger.info(f"Popup cookies fermé avec: {selector}")
                    self._random_delay(2, 3)
                    return True
            except Exception as e:
                continue
        
        # Stratégie 3: Attendre et fermer tout dialogue visible
        try:
            self.page.evaluate("""
                () => {
                    // Supprimer les overlays de cookies
                    const overlays = document.querySelectorAll('[data-testid="cookie-policy-manage-dialog"]');
                    overlays.forEach(el => el.remove());
                    
                    // Supprimer les backdrops
                    const backdrops = document.querySelectorAll('.__fb-light-mode div[style*="position: fixed"]');
                    backdrops.forEach(el => {
                        if (el.style.zIndex > 100) el.remove();
                    });
                }
            """)
            logger.info("Overlays de cookies supprimés via JS")
            self._random_delay(1, 2)
        except:
            pass
        
        logger.info("Pas de popup de cookies détecté ou déjà fermé")
        return False
    
    def _dismiss_popups(self):
        """Ferme les popups Facebook courants."""
        # D'abord gérer les cookies
        self._handle_cookie_popup()
        
        popups = [
            '[aria-label="Close"]',
            '[aria-label="Fermer"]',
            'div[aria-label="Close"]',
            'button:has-text("Not Now")',
            'button:has-text("Pas maintenant")',
            'div[role="button"]:has-text("Not Now")',
            'div[role="button"]:has-text("Pas maintenant")',
        ]
        
        for popup_selector in popups:
            try:
                popup = self.page.locator(popup_selector).first
                if popup.is_visible(timeout=1000):
                    popup.dispatch_event('click')
                    self._random_delay(0.5, 1)
            except:
                continue
    
    def _check_logged_in(self) -> bool:
        """Vérifie si on est connecté à Facebook."""
        try:
            self.page.goto(self.HOME_URL, wait_until='domcontentloaded', timeout=60000)
            self._random_delay(2, 3)
            
            # Gérer les cookies d'abord - CRITIQUE
            self._handle_cookie_popup()
            self._random_delay(1, 2)
            
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
                '[aria-label="Menu"]',
                'div[role="navigation"]',
                '[data-pagelet="LeftRail"]',
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
            self.page.goto(self.LOGIN_URL, wait_until='domcontentloaded', timeout=60000)
            self._random_delay(2, 3)
            
            # CRITIQUE: Gérer les cookies AVANT toute interaction
            self._handle_cookie_popup()
            self._random_delay(1, 2)
            
            # Attendre que le formulaire soit prêt
            try:
                self.page.wait_for_selector('input#email', state='visible', timeout=15000)
            except:
                # Peut-être déjà connecté ou cookies non gérés
                self._handle_cookie_popup()
                self.page.wait_for_selector('input#email', state='visible', timeout=10000)
            
            # Entrer l'email
            email_field = self.page.locator('input#email')
            email_field.click()
            self._random_delay(0.3, 0.5)
            email_field.fill(self.email)
            
            self._random_delay(0.5, 1)
            
            # Entrer le mot de passe
            password_field = self.page.locator('input#pass')
            password_field.click()
            self._random_delay(0.3, 0.5)
            password_field.fill(self.password)
            
            self._random_delay(1, 2)
            
            # Cliquer sur le bouton de connexion
            login_btn = self.page.locator('button[name="login"], button[type="submit"], button:has-text("Log In"), button:has-text("Se connecter")').first
            login_btn.click()
            
            # Attendre la redirection
            self._random_delay(5, 8)
            
            # Vérifier s'il y a un checkpoint de sécurité
            current_url = self.page.url.lower()
            if 'checkpoint' in current_url or 'two_step' in current_url:
                logger.warning("⚠️ Vérification de sécurité Facebook détectée!")
                self._take_screenshot("security_checkpoint")
                return False
            
            # Fermer les popups post-connexion
            self._dismiss_popups()
            
            if self._check_logged_in():
                logger.info("✅ Connexion Facebook réussie")
                return True
            
            logger.error("Échec de la connexion Facebook")
            return False
            
        except Exception as e:
            logger.error(f"Erreur connexion Facebook: {e}")
            self._take_screenshot("login_error")
            return False
    
    def _switch_to_page(self) -> bool:
        """Passe en mode page pour publier."""
        if not self.page_name:
            logger.info("Pas de nom de page configuré, publication sur profil personnel")
            return True
        
        try:
            logger.info(f"Passage à la page: {self.page_name}")
            
            # Aller sur la page
            page_url = f"https://www.facebook.com/{self.page_name.replace(' ', '')}"
            self.page.goto(page_url, wait_until='domcontentloaded', timeout=30000)
            self._random_delay(2, 3)
            
            self._dismiss_popups()
            
            # Vérifier si on est sur la page
            return True
            
        except Exception as e:
            logger.error(f"Erreur changement de page: {e}")
            return False
    
    def _publish(self, text: str, image_path: str = None, video_path: str = None) -> bool:
        """Publie sur Facebook."""
        try:
            logger.info("Publication sur Facebook...")
            
            # Passer à la page si configurée
            self._switch_to_page()
            
            # Chercher et cliquer sur la zone de création de post
            create_post_selectors = [
                '[aria-label="Create a post"]',
                '[aria-label="Créer une publication"]',
                'div[role="button"]:has-text("What\'s on your mind")',
                'div[role="button"]:has-text("Exprimez-vous")',
                'div[role="button"]:has-text("Quoi de neuf")',
                '[data-pagelet="ProfileComposer"] div[role="button"]',
            ]
            
            create_btn = None
            for selector in create_post_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if btn.is_visible(timeout=3000):
                        create_btn = btn
                        break
                except:
                    continue
            
            if not create_btn:
                raise Exception("Bouton de création de post non trouvé")
            
            create_btn.click()
            self._random_delay(2, 3)
            
            # Attendre le modal de composition
            text_area_selectors = [
                '[aria-label="What\'s on your mind?"]',
                '[aria-label="Exprimez-vous..."]',
                '[contenteditable="true"][role="textbox"]',
                'div[role="textbox"]',
            ]
            
            text_area = None
            for selector in text_area_selectors:
                try:
                    area = self.page.locator(selector).first
                    if area.is_visible(timeout=5000):
                        text_area = area
                        break
                except:
                    continue
            
            if not text_area:
                raise Exception("Zone de texte non trouvée")
            
            # Entrer le texte
            text_area.click()
            self._random_delay(0.5, 1)
            text_area.type(text, delay=20)
            
            self._random_delay(2, 3)
            
            # Ajouter l'image si fournie
            if image_path and Path(image_path).exists():
                try:
                    # Chercher le bouton d'ajout de photo
                    photo_btn = self.page.locator('[aria-label="Photo/video"], [aria-label="Photo/vidéo"]').first
                    if photo_btn.is_visible(timeout=3000):
                        photo_btn.click()
                        self._random_delay(1, 2)
                    
                    # Upload le fichier
                    file_input = self.page.locator('input[type="file"][accept*="image"]').first
                    file_input.set_input_files(image_path)
                    self._random_delay(3, 5)
                    logger.info("Image ajoutée")
                except Exception as e:
                    logger.warning(f"Impossible d'ajouter l'image: {e}")
            
            # Cliquer sur Publier
            publish_selectors = [
                '[aria-label="Post"]',
                '[aria-label="Publier"]',
                'div[role="button"]:has-text("Post")',
                'div[role="button"]:has-text("Publier")',
            ]
            
            for selector in publish_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if btn.is_visible() and btn.is_enabled():
                        btn.click()
                        break
                except:
                    continue
            
            self._random_delay(5, 8)
            
            self._take_screenshot("published")
            logger.info("✅ Publication Facebook terminée")
            return True
            
        except Exception as e:
            logger.error(f"Erreur publication Facebook: {e}")
            self._take_screenshot("publish_error")
            return False