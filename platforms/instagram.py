"""
Budget Famille - Instagram Poster (Fixed v5)
=============================================
Module pour publier automatiquement sur Instagram.
Gestion complète du flow multi-étapes (crop, filter, caption, share).
"""

import os
import time
from pathlib import Path
from .base import BasePoster
from utils.logger import get_logger

logger = get_logger(__name__)


class InstagramPoster(BasePoster):
    """Poster pour Instagram."""
    
    PLATFORM_NAME = "instagram"
    LOGIN_URL = "https://www.instagram.com/accounts/login/"
    HOME_URL = "https://www.instagram.com/"
    
    def __init__(self, headless: bool = True):
        super().__init__(headless)
        self.username = os.getenv('INSTAGRAM_USER')
        self.password = os.getenv('INSTAGRAM_PASS')
    
    def _handle_cookie_popup(self) -> bool:
        """Gère les popups de cookies Instagram."""
        cookie_selectors = [
            'button:has-text("Allow all cookies")',
            'button:has-text("Autoriser tous les cookies")',
            'button:has-text("Accept All")',
            'button:has-text("Tout accepter")',
            'button:has-text("Accept")',
            'button:has-text("Accepter")',
        ]
        
        for selector in cookie_selectors:
            try:
                btn = self.page.locator(selector).first
                if btn.is_visible(timeout=2000):
                    btn.click(force=True)
                    self._random_delay(1, 2)
                    logger.info("Popup cookies Instagram fermé")
                    return True
            except:
                continue
        return False
    
    def _dismiss_popups(self):
        """Ferme les popups Instagram courants."""
        self._handle_cookie_popup()
        
        popup_selectors = [
            'button:has-text("Not Now")',
            'button:has-text("Pas maintenant")',
            'button:has-text("Cancel")',
            'button:has-text("Annuler")',
            '[aria-label="Close"]',
            '[aria-label="Fermer"]',
            'svg[aria-label="Close"]',
        ]
        
        for selector in popup_selectors:
            try:
                popup = self.page.locator(selector).first
                if popup.is_visible(timeout=1500):
                    popup.click(force=True)
                    self._random_delay(0.5, 1)
            except:
                continue
    
    def _check_logged_in(self) -> bool:
        """Vérifie si on est connecté à Instagram."""
        try:
            self.page.goto(self.HOME_URL, wait_until='domcontentloaded', timeout=60000)
            self._random_delay(2, 3)
            
            self._handle_cookie_popup()
            
            current_url = self.page.url.lower()
            if 'login' in current_url or 'accounts' in current_url:
                return False
            
            indicators = [
                'svg[aria-label="New post"]',
                'svg[aria-label="Nouvelle publication"]',
                '[aria-label="Create"]',
                '[aria-label="Créer"]',
                'svg[aria-label="Home"]',
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
            self._random_delay(2, 3)
            
            self._handle_cookie_popup()
            
            # Attendre le formulaire
            self.page.wait_for_selector('input[name="username"]', state='visible', timeout=15000)
            
            # Entrer les identifiants
            self.page.locator('input[name="username"]').fill(self.username)
            self._random_delay(0.5, 1)
            self.page.locator('input[name="password"]').fill(self.password)
            self._random_delay(1, 2)
            
            # Se connecter
            self.page.locator('button[type="submit"]').click()
            self._random_delay(5, 8)
            
            # Vérifier les challenges
            if 'challenge' in self.page.url.lower() or 'suspicious' in self.page.url.lower():
                logger.warning("⚠️ Vérification de sécurité Instagram détectée!")
                return False
            
            self._dismiss_popups()
            
            if self._check_logged_in():
                logger.info("✅ Connexion Instagram réussie")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur connexion Instagram: {e}")
            return False
    
    def _click_next_button(self) -> bool:
        """Clique sur le bouton Next/Suivant avec plusieurs stratégies."""
        next_selectors = [
            # Boutons textuels
            'button:has-text("Next")',
            'button:has-text("Suivant")',
            'div[role="button"]:has-text("Next")',
            'div[role="button"]:has-text("Suivant")',
            
            # Sélecteurs spécifiques Instagram
            'div[role="dialog"] button:has-text("Next")',
            'div[role="dialog"] button:has-text("Suivant")',
            
            # Par position (dernier bouton dans le header du dialog)
            'div[role="dialog"] header button:last-child',
        ]
        
        for selector in next_selectors:
            try:
                btn = self.page.locator(selector).first
                if btn.is_visible(timeout=3000) and btn.is_enabled():
                    btn.click(force=True)
                    logger.info(f"Bouton Next cliqué: {selector}")
                    return True
            except:
                continue
        
        # Fallback JavaScript
        try:
            clicked = self.page.evaluate("""
                () => {
                    const dialog = document.querySelector('div[role="dialog"]');
                    if (!dialog) return false;
                    
                    const buttons = dialog.querySelectorAll('button, div[role="button"]');
                    for (const btn of buttons) {
                        const text = btn.textContent.toLowerCase().trim();
                        if (text === 'next' || text === 'suivant') {
                            btn.click();
                            return true;
                        }
                    }
                    
                    // Dernier bouton du header
                    const header = dialog.querySelector('header, [role="heading"]');
                    if (header) {
                        const headerBtns = header.parentElement.querySelectorAll('button');
                        if (headerBtns.length > 0) {
                            headerBtns[headerBtns.length - 1].click();
                            return true;
                        }
                    }
                    
                    return false;
                }
            """)
            if clicked:
                logger.info("Bouton Next cliqué via JavaScript")
                return True
        except:
            pass
        
        return False
    
    def _click_share_button(self) -> bool:
        """Clique sur le bouton Share/Partager avec plusieurs stratégies."""
        share_selectors = [
            # Boutons textuels
            'button:has-text("Share")',
            'button:has-text("Partager")',
            'div[role="button"]:has-text("Share")',
            'div[role="button"]:has-text("Partager")',
            
            # Sélecteurs spécifiques Instagram
            'div[role="dialog"] button:has-text("Share")',
            'div[role="dialog"] button:has-text("Partager")',
        ]
        
        for selector in share_selectors:
            try:
                btn = self.page.locator(selector).first
                if btn.is_visible(timeout=3000) and btn.is_enabled():
                    btn.click(force=True)
                    logger.info(f"Bouton Share cliqué: {selector}")
                    return True
            except:
                continue
        
        # Fallback JavaScript
        try:
            clicked = self.page.evaluate("""
                () => {
                    const dialog = document.querySelector('div[role="dialog"]');
                    if (!dialog) return false;
                    
                    const buttons = dialog.querySelectorAll('button, div[role="button"]');
                    for (const btn of buttons) {
                        const text = btn.textContent.toLowerCase().trim();
                        if (text === 'share' || text === 'partager') {
                            btn.click();
                            return true;
                        }
                    }
                    return false;
                }
            """)
            if clicked:
                logger.info("Bouton Share cliqué via JavaScript")
                return True
        except:
            pass
        
        return False
    
    def _publish(self, text: str, image_path: str = None, video_path: str = None) -> bool:
        """
        Publie un post sur Instagram.
        Flow complet: Upload → Crop → Filter → Caption → Share
        """
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
            
            # ===== ÉTAPE 1: Cliquer sur "Créer" =====
            logger.info("Étape 1: Ouverture du dialog de création...")
            
            create_selectors = [
                'svg[aria-label="New post"]',
                'svg[aria-label="Nouvelle publication"]',
                '[aria-label="Create"]',
                '[aria-label="Créer"]',
                'a[href="/create/style/"]',
            ]
            
            clicked = False
            for selector in create_selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.is_visible(timeout=3000):
                        # Cliquer sur le parent (le lien/bouton)
                        parent = element.locator('xpath=..')
                        parent.click(force=True)
                        clicked = True
                        logger.info(f"Bouton Créer cliqué: {selector}")
                        break
                except:
                    continue
            
            if not clicked:
                # Essayer via le menu latéral
                try:
                    menu_create = self.page.locator('span:has-text("Create"), span:has-text("Créer")').first
                    if menu_create.is_visible(timeout=3000):
                        menu_create.click(force=True)
                        clicked = True
                        logger.info("Bouton Créer cliqué via menu")
                except:
                    pass
            
            if not clicked:
                raise Exception("Bouton Créer non trouvé")
            
            self._random_delay(2, 3)
            self._take_screenshot("create_dialog_opened")
            
            # ===== ÉTAPE 2: Upload du fichier =====
            logger.info("Étape 2: Upload du média...")
            
            file_input = self.page.locator('input[type="file"]').first
            file_input.set_input_files(media_path)
            
            self._random_delay(3, 5)
            self._take_screenshot("media_uploaded")
            
            # ===== ÉTAPE 3: Recadrage (Crop) - Cliquer sur "Next" =====
            logger.info("Étape 3: Recadrage (Crop)...")
            
            if self._click_next_button():
                self._random_delay(2, 3)
                self._take_screenshot("after_crop")
            else:
                logger.warning("Bouton Next (crop) non trouvé, tentative de continuer...")
            
            # ===== ÉTAPE 4: Filtres - Cliquer sur "Next" =====
            logger.info("Étape 4: Filtres...")
            
            if self._click_next_button():
                self._random_delay(2, 3)
                self._take_screenshot("after_filter")
            else:
                logger.warning("Bouton Next (filter) non trouvé, tentative de continuer...")
            
            # ===== ÉTAPE 5: Ajouter la légende =====
            logger.info("Étape 5: Ajout de la légende...")
            
            caption_selectors = [
                'textarea[aria-label*="caption"]',
                'textarea[aria-label*="légende"]',
                'textarea[aria-label*="Write a caption"]',
                'textarea[aria-label*="Écrivez une légende"]',
                'div[role="dialog"] textarea',
                'div[contenteditable="true"][role="textbox"]',
                'div[aria-label*="caption"]',
            ]
            
            caption_field = None
            for selector in caption_selectors:
                try:
                    field = self.page.locator(selector).first
                    if field.is_visible(timeout=3000):
                        caption_field = field
                        logger.info(f"Champ légende trouvé: {selector}")
                        break
                except:
                    continue
            
            if caption_field:
                caption_field.click(force=True)
                self._random_delay(0.5, 1)
                caption_field.type(text, delay=30)
                self._random_delay(1, 2)
                self._take_screenshot("caption_added")
            else:
                logger.warning("Champ de légende non trouvé")
            
            # ===== ÉTAPE 6: Partager =====
            logger.info("Étape 6: Publication (Share)...")
            
            if self._click_share_button():
                self._random_delay(5, 10)
                self._take_screenshot("after_share")
            else:
                # Dernière tentative
                logger.info("Tentative alternative pour le bouton Share...")
                try:
                    # Chercher n'importe quel bouton bleu/primaire
                    primary_btn = self.page.locator('div[role="dialog"] button[type="button"]').last
                    if primary_btn.is_visible() and primary_btn.is_enabled():
                        btn_text = primary_btn.text_content()
                        logger.info(f"Clic sur bouton: {btn_text}")
                        primary_btn.click(force=True)
                        self._random_delay(5, 10)
                except:
                    raise Exception("Bouton Share/Partager non trouvé")
            
            # Vérifier le succès (message "Post shared" ou fermeture du dialog)
            try:
                success_indicators = [
                    'text=Your post has been shared',
                    'text=Votre publication a été partagée',
                    'text=Post shared',
                    'text=Publication partagée',
                ]
                
                for indicator in success_indicators:
                    try:
                        if self.page.locator(indicator).is_visible(timeout=3000):
                            logger.info("✅ Confirmation de publication détectée")
                            break
                    except:
                        continue
            except:
                pass
            
            logger.info("✅ Publication Instagram terminée!")
            return True
            
        except Exception as e:
            logger.error(f"Erreur publication Instagram: {e}")
            self._take_screenshot("publish_error")
            return False