"""
Budget Famille - LinkedIn Poster (Fixed v5)
============================================
Module pour publier automatiquement sur LinkedIn.
Gestion améliorée du bouton de publication.
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
        self.google_email = os.getenv('GOOGLE_EMAIL')
        self.google_password = os.getenv('GOOGLE_PASS')
    
    def _handle_cookie_popup(self) -> bool:
        """Gère le popup de cookies LinkedIn."""
        cookie_selectors = [
            'button[action-type="ACCEPT"]',
            'button:has-text("Accept & Join")',
            'button:has-text("Accepter et rejoindre")',
            'button:has-text("Accept")',
            'button:has-text("Accepter")',
            'button:has-text("Accept all")',
            'button:has-text("Tout accepter")',
            '.artdeco-global-alert__action button',
        ]
        
        for selector in cookie_selectors:
            try:
                btn = self.page.locator(selector).first
                if btn.is_visible(timeout=2000):
                    btn.click(force=True)
                    self._random_delay(1, 2)
                    logger.info(f"Popup cookies LinkedIn fermé: {selector}")
                    return True
            except:
                continue
        return False
    
    def _dismiss_popups(self):
        """Ferme les popups LinkedIn courants."""
        self._handle_cookie_popup()
        
        popup_selectors = [
            'button[aria-label="Dismiss"]',
            'button[aria-label="Fermer"]',
            'button:has-text("Not now")',
            'button:has-text("Pas maintenant")',
            '.msg-overlay-bubble-header__control--close',
        ]
        
        for selector in popup_selectors:
            try:
                popup = self.page.locator(selector).first
                if popup.is_visible(timeout=1000):
                    popup.click(force=True)
                    self._random_delay(0.5, 1)
            except:
                continue
    
    def _check_logged_in(self) -> bool:
        """Vérifie si on est connecté à LinkedIn."""
        try:
            self.page.goto(self.FEED_URL, wait_until='domcontentloaded', timeout=60000)
            self._random_delay(2, 3)
            
            self._handle_cookie_popup()
            
            current_url = self.page.url.lower()
            if 'login' in current_url or 'checkpoint' in current_url or 'authwall' in current_url:
                return False
            
            logged_in_indicators = [
                'button[aria-label*="Start a post"]',
                'button[aria-label*="Commencer un post"]',
                '.share-box-feed-entry__trigger',
                '.feed-identity-module',
                '.global-nav__me-photo',
            ]
            
            for indicator in logged_in_indicators:
                try:
                    if self.page.locator(indicator).count() > 0:
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur vérification connexion LinkedIn: {e}")
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
        """Connexion via Google OAuth."""
        if not self.google_email or not self.google_password:
            return False
        
        try:
            logger.info("🔍 Recherche du bouton Google...")
            
            google_btn_selectors = [
                '.alternate-signin__btn--google',
                'button:has-text("Sign in with Google")',
                'button:has-text("Continue with Google")',
                '[data-provider="google"]',
            ]
            
            google_btn = None
            for selector in google_btn_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if btn.is_visible(timeout=2000):
                        google_btn = btn
                        logger.info(f"✅ Bouton Google trouvé: {selector}")
                        break
                except:
                    continue
            
            if not google_btn:
                logger.info("❌ Bouton Google non trouvé")
                return False
            
            logger.info("Clic sur le bouton Google...")
            
            with self.page.context.expect_page(timeout=45000) as popup_info:
                google_btn.click()
            
            popup = popup_info.value
            popup.wait_for_load_state('domcontentloaded', timeout=30000)
            self._random_delay(2, 3)
            
            # Liste de comptes Google
            try:
                account_list = popup.locator('div[data-email], div[data-identifier]')
                if account_list.count() > 0:
                    logger.info("📋 Liste de comptes détectée")
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
            
            # Champ email
            try:
                email_field = popup.locator('input[type="email"], #identifierId').first
                if email_field.is_visible(timeout=5000):
                    logger.info("Saisie email Google...")
                    email_field.fill(self.google_email)
                    self._random_delay(1, 2)
                    popup.locator('button:has-text("Next"), button:has-text("Suivant")').first.click()
                    self._random_delay(3, 4)
            except:
                pass
            
            # Mot de passe
            try:
                password_field = popup.locator('input[type="password"]').first
                if password_field.is_visible(timeout=10000):
                    logger.info("Saisie mot de passe Google...")
                    password_field.fill(self.google_password)
                    self._random_delay(1, 2)
                    popup.locator('button:has-text("Next"), button:has-text("Suivant")').first.click()
                    self._random_delay(3, 5)
            except:
                pass
            
            # Autorisation
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
            if self._wait_for_popup_close(popup, timeout=30000):
                logger.info("Popup Google fermé")
            else:
                try:
                    popup.close()
                except:
                    pass
            
            self._random_delay(3, 5)
            
            if self._check_logged_in():
                logger.info("✅ Connexion LinkedIn via Google réussie!")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur connexion Google: {e}")
            return False
    
    def _login_classic(self) -> bool:
        """Connexion classique."""
        try:
            logger.info("Connexion classique à LinkedIn...")
            
            if 'login' not in self.page.url.lower():
                self.page.goto(self.LOGIN_URL, wait_until='domcontentloaded', timeout=60000)
                self._random_delay(2, 3)
            
            self._handle_cookie_popup()
            
            self.page.wait_for_selector('#username', state='visible', timeout=15000)
            
            self.page.locator('#username').fill(self.email)
            self._random_delay(0.5, 1)
            self.page.locator('#password').fill(self.password)
            self._random_delay(1, 2)
            
            self.page.locator('button[type="submit"]').first.click()
            self._random_delay(5, 8)
            
            if 'checkpoint' in self.page.url.lower():
                logger.warning("⚠️ Vérification de sécurité détectée!")
                return False
            
            self._dismiss_popups()
            return self._check_logged_in()
            
        except Exception as e:
            logger.error(f"Erreur connexion LinkedIn: {e}")
            return False
    
    def _login(self) -> bool:
        """Connexion: Google prioritaire, puis classique."""
        try:
            logger.info("Connexion à LinkedIn...")
            
            self.page.goto(self.LOGIN_URL, wait_until='domcontentloaded', timeout=60000)
            self._random_delay(2, 3)
            self._handle_cookie_popup()
            
            if self.google_email and self.google_password:
                logger.info("📍 Tentative Google (prioritaire)...")
                if self._login_with_google():
                    return True
                logger.info("Fallback au login classique")
            
            return self._login_classic()
            
        except Exception as e:
            logger.error(f"Erreur connexion LinkedIn: {e}")
            return False
    
    def _publish(self, text: str, image_path: str = None, video_path: str = None) -> bool:
        """Publie sur LinkedIn avec détection robuste du bouton de publication."""
        try:
            logger.info("Publication sur LinkedIn...")
            
            self.page.goto(self.FEED_URL, wait_until='domcontentloaded', timeout=30000)
            self._random_delay(2, 3)
            self._dismiss_popups()
            
            # ===== ÉTAPE 1: Ouvrir le modal de création de post =====
            logger.info("Étape 1: Ouverture du modal de création...")
            
            start_post_selectors = [
                'button[aria-label*="Start a post"]',
                'button[aria-label*="Commencer un post"]',
                '.share-box-feed-entry__trigger',
                'button:has-text("Start a post")',
                'button:has-text("Commencer un post")',
                '.share-box-feed-entry__top-bar',
                'div[data-urn] button.artdeco-button',
            ]
            
            start_btn = None
            for selector in start_post_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if btn.is_visible(timeout=3000):
                        start_btn = btn
                        logger.info(f"Bouton 'Start a post' trouvé: {selector}")
                        break
                except:
                    continue
            
            if not start_btn:
                # Essayer via JavaScript
                logger.info("Recherche du bouton via JavaScript...")
                clicked = self.page.evaluate("""
                    () => {
                        // Chercher le bouton de création de post
                        const btns = document.querySelectorAll('button, div[role="button"]');
                        for (const btn of btns) {
                            const text = btn.textContent.toLowerCase();
                            const label = btn.getAttribute('aria-label') || '';
                            if (text.includes('start a post') || text.includes('commencer') || 
                                label.includes('Start a post') || label.includes('Commencer')) {
                                btn.click();
                                return true;
                            }
                        }
                        // Chercher le trigger de la share box
                        const shareBox = document.querySelector('.share-box-feed-entry__trigger, .share-box-feed-entry__top-bar');
                        if (shareBox) {
                            shareBox.click();
                            return true;
                        }
                        return false;
                    }
                """)
                if clicked:
                    logger.info("Bouton cliqué via JavaScript")
                else:
                    raise Exception("Bouton 'Start a post' non trouvé")
            else:
                start_btn.click()
            
            self._random_delay(2, 3)
            self._take_screenshot("modal_opened")
            
            # ===== ÉTAPE 2: Trouver et remplir la zone de texte =====
            logger.info("Étape 2: Saisie du texte...")
            
            text_area_selectors = [
                '.ql-editor[data-placeholder]',
                '.ql-editor',
                'div[contenteditable="true"][role="textbox"]',
                '[aria-label="Text editor for creating content"]',
                '[aria-label="Éditeur de texte pour créer du contenu"]',
                'div[aria-placeholder*="What do you want to talk about"]',
                'div[aria-placeholder*="De quoi souhaitez-vous discuter"]',
                '.editor-content div[contenteditable="true"]',
            ]
            
            text_area = None
            for selector in text_area_selectors:
                try:
                    area = self.page.locator(selector).first
                    if area.is_visible(timeout=5000):
                        text_area = area
                        logger.info(f"Zone de texte trouvée: {selector}")
                        break
                except:
                    continue
            
            if not text_area:
                raise Exception("Zone de texte non trouvée")
            
            text_area.click()
            self._random_delay(0.5, 1)
            text_area.type(text, delay=20)
            
            self._random_delay(2, 3)
            self._take_screenshot("text_entered")
            
            # ===== ÉTAPE 3: Ajouter l'image si fournie =====
            if image_path and Path(image_path).exists():
                logger.info("Étape 3: Ajout de l'image...")
                try:
                    media_btn_selectors = [
                        'button[aria-label*="Add a photo"]',
                        'button[aria-label*="Ajouter une photo"]',
                        'button[aria-label*="Add media"]',
                        'button[aria-label*="Ajouter un média"]',
                        '[data-control-name="share.create_image"]',
                    ]
                    
                    for selector in media_btn_selectors:
                        try:
                            btn = self.page.locator(selector).first
                            if btn.is_visible(timeout=2000):
                                btn.click()
                                self._random_delay(1, 2)
                                break
                        except:
                            continue
                    
                    file_input = self.page.locator('input[type="file"][accept*="image"]').first
                    file_input.set_input_files(image_path)
                    self._random_delay(3, 5)
                    logger.info("✅ Image ajoutée")
                except Exception as e:
                    logger.warning(f"Impossible d'ajouter l'image: {e}")
            
            # ===== ÉTAPE 4: Cliquer sur le bouton de publication =====
            logger.info("Étape 4: Publication du post...")
            self._take_screenshot("before_publish")
            
            # Liste exhaustive des sélecteurs pour le bouton de publication
            publish_selectors = [
                # Sélecteurs par data-control-name (LinkedIn specific)
                'button[data-control-name="share.post"]',
                
                # Sélecteurs par classe
                '.share-actions__primary-action',
                '.share-box-footer__primary-btn',
                
                # Sélecteurs par texte (anglais)
                'button:has-text("Post")',
                'button:has-text("Publish")',
                'button:has-text("Send")',
                'button:has-text("Share")',
                
                # Sélecteurs par texte (français)
                'button:has-text("Publier")',
                'button:has-text("Poster")',
                'button:has-text("Envoyer")',
                'button:has-text("Partager")',
                
                # Sélecteurs par aria-label
                'button[aria-label="Post"]',
                'button[aria-label="Publier"]',
                'button[aria-label="Share post"]',
                
                # Sélecteurs génériques dans le modal
                '.share-box_actions button.artdeco-button--primary',
                'div[data-test-modal] button.artdeco-button--primary',
                '.share-creation-state__footer button.artdeco-button--primary',
                
                # Boutons primaires dans le footer
                'footer button.artdeco-button--primary',
                '.share-box-footer button.artdeco-button--primary',
            ]
            
            publish_btn = None
            for selector in publish_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if btn.is_visible(timeout=2000) and btn.is_enabled():
                        publish_btn = btn
                        logger.info(f"✅ Bouton de publication trouvé: {selector}")
                        break
                except:
                    continue
            
            # Si pas trouvé avec les sélecteurs, essayer via JavaScript
            if not publish_btn:
                logger.info("Recherche du bouton de publication via JavaScript...")
                clicked = self.page.evaluate("""
                    () => {
                        // Chercher dans le modal de partage
                        const modal = document.querySelector('.share-box, [data-test-modal], .artdeco-modal');
                        const searchContainer = modal || document;
                        
                        // Chercher tous les boutons
                        const buttons = searchContainer.querySelectorAll('button');
                        
                        for (const btn of buttons) {
                            const text = btn.textContent.trim().toLowerCase();
                            const ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();
                            const classes = btn.className.toLowerCase();
                            
                            // Vérifier si c'est un bouton primaire avec le bon texte
                            const isPrimary = classes.includes('primary') || classes.includes('share-actions');
                            const isPostButton = (
                                text === 'post' || text === 'publier' || text === 'poster' ||
                                text === 'share' || text === 'partager' ||
                                text === 'publish' || text === 'send' || text === 'envoyer' ||
                                ariaLabel.includes('post') || ariaLabel.includes('publier')
                            );
                            
                            if (isPostButton && !btn.disabled) {
                                console.log('Found publish button:', btn.textContent);
                                btn.click();
                                return true;
                            }
                            
                            // Fallback: bouton primaire dans le footer du modal
                            if (isPrimary && btn.closest('.share-box-footer, .share-actions, footer')) {
                                console.log('Found primary button in footer:', btn.textContent);
                                btn.click();
                                return true;
                            }
                        }
                        
                        return false;
                    }
                """)
                
                if clicked:
                    logger.info("✅ Bouton de publication cliqué via JavaScript")
                else:
                    # Dernière tentative: chercher le bouton par sa position
                    logger.info("Dernière tentative: bouton primaire dans le modal...")
                    try:
                        primary_btn = self.page.locator('button.artdeco-button--primary').last
                        if primary_btn.is_visible() and primary_btn.is_enabled():
                            btn_text = primary_btn.text_content()
                            logger.info(f"Clic sur bouton primaire: {btn_text}")
                            primary_btn.click(force=True)
                        else:
                            raise Exception("Bouton de publication non trouvé ou désactivé")
                    except Exception as e:
                        self._take_screenshot("publish_button_not_found")
                        raise Exception(f"Impossible de trouver le bouton de publication: {e}")
            else:
                # Cliquer sur le bouton trouvé
                try:
                    publish_btn.click(force=True)
                except:
                    # Si le clic normal échoue, essayer dispatch_event
                    publish_btn.dispatch_event('click')
            
            self._random_delay(3, 5)
            self._take_screenshot("after_publish")
            
            # Vérifier si le modal s'est fermé (publication réussie)
            try:
                # Si le modal est encore visible après 3 secondes, il y a peut-être une erreur
                modal_visible = self.page.locator('.share-box, .artdeco-modal').first.is_visible(timeout=3000)
                if modal_visible:
                    logger.warning("Le modal est toujours visible, vérification...")
                    # Vérifier s'il y a un message d'erreur
                    error = self.page.locator('.share-box-error, .artdeco-inline-feedback--error').first
                    if error.is_visible(timeout=1000):
                        error_text = error.text_content()
                        logger.error(f"Erreur de publication: {error_text}")
                        return False
            except:
                pass  # Le modal s'est fermé, c'est bon
            
            logger.info("✅ Publication LinkedIn terminée!")
            return True
            
        except Exception as e:
            logger.error(f"Erreur publication LinkedIn: {e}")
            self._take_screenshot("publish_error")
            return False