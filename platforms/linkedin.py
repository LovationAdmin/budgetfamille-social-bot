"""
Budget Famille - LinkedIn Poster (Fixed v6)
============================================
Module pour publier automatiquement sur LinkedIn.
Détection robuste du bouton de publication (FR/EN).
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
            'button:has-text("Accept")',
            'button:has-text("Accepter")',
            '.artdeco-global-alert__action button',
        ]
        
        for selector in cookie_selectors:
            try:
                btn = self.page.locator(selector).first
                if btn.is_visible(timeout=2000):
                    btn.click(force=True)
                    self._random_delay(1, 2)
                    logger.info(f"Popup cookies fermé: {selector}")
                    return True
            except:
                continue
        return False
    
    def _dismiss_popups(self):
        """Ferme les popups LinkedIn."""
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
        """Vérifie si connecté à LinkedIn."""
        try:
            self.page.goto(self.FEED_URL, wait_until='domcontentloaded', timeout=60000)
            self._random_delay(2, 3)
            self._handle_cookie_popup()
            
            if 'login' in self.page.url.lower() or 'authwall' in self.page.url.lower():
                return False
            
            indicators = [
                'button[aria-label*="Start a post"]',
                'button[aria-label*="Commencer un post"]',
                '.share-box-feed-entry__trigger',
                '.global-nav__me-photo',
            ]
            
            for indicator in indicators:
                try:
                    if self.page.locator(indicator).count() > 0:
                        return True
                except:
                    continue
            return False
        except:
            return False
    
    def _wait_for_popup_close(self, popup, timeout: int = 30000) -> bool:
        """Attend la fermeture du popup."""
        start_time = time.time()
        while time.time() - start_time < timeout / 1000:
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
            
            google_btn = None
            for selector in ['.alternate-signin__btn--google', 'button:has-text("Sign in with Google")']:
                try:
                    btn = self.page.locator(selector).first
                    if btn.is_visible(timeout=2000):
                        google_btn = btn
                        break
                except:
                    continue
            
            if not google_btn:
                return False
            
            logger.info("✅ Bouton Google trouvé")
            
            with self.page.context.expect_page(timeout=45000) as popup_info:
                google_btn.click()
            
            popup = popup_info.value
            popup.wait_for_load_state('domcontentloaded', timeout=30000)
            self._random_delay(2, 3)
            
            # Sélection du compte
            try:
                for selector in [f'div[data-email="{self.google_email}"]', f'div[data-identifier="{self.google_email}"]']:
                    try:
                        account = popup.locator(selector).first
                        if account.is_visible(timeout=3000):
                            account.click()
                            self._random_delay(2, 3)
                            break
                    except:
                        continue
            except:
                pass
            
            # Email
            try:
                email_field = popup.locator('input[type="email"], #identifierId').first
                if email_field.is_visible(timeout=5000):
                    email_field.fill(self.google_email)
                    self._random_delay(1, 2)
                    popup.locator('button:has-text("Next"), button:has-text("Suivant")').first.click()
                    self._random_delay(3, 4)
            except:
                pass
            
            # Password
            try:
                password_field = popup.locator('input[type="password"]').first
                if password_field.is_visible(timeout=10000):
                    password_field.fill(self.google_password)
                    self._random_delay(1, 2)
                    popup.locator('button:has-text("Next"), button:has-text("Suivant")').first.click()
                    self._random_delay(3, 5)
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
        """Connexion: Google prioritaire puis classique."""
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
    
    def _click_publish_button(self) -> bool:
        """
        Clique sur le bouton de publication avec détection robuste.
        Supporte: Post, Publier, Share, Partager, Envoyer, Send (FR/EN)
        """
        logger.info("Recherche du bouton de publication...")
        
        # Liste exhaustive des sélecteurs
        publish_selectors = [
            # Par data-control-name (le plus fiable)
            'button[data-control-name="share.post"]',
            
            # Par classe LinkedIn
            'button.share-actions__primary-action',
            '.share-box-footer__primary-btn',
            '.share-creation-state__footer button.artdeco-button--primary',
            
            # Par texte exact (EN)
            'button:text-is("Post")',
            'button:text-is("Share")',
            'button:text-is("Send")',
            'button:text-is("Publish")',
            
            # Par texte exact (FR)
            'button:text-is("Publier")',
            'button:text-is("Poster")',
            'button:text-is("Partager")',
            'button:text-is("Envoyer")',
            
            # Par has-text (moins précis mais plus flexible)
            'button:has-text("Post")',
            'button:has-text("Publier")',
            'button:has-text("Poster")',
            'button:has-text("Share")',
            'button:has-text("Partager")',
            
            # Par aria-label
            'button[aria-label="Post"]',
            'button[aria-label="Publier"]',
            'button[aria-label="Share"]',
            'button[aria-label="Partager"]',
            
            # Boutons primaires dans le modal
            '.share-box-footer button.artdeco-button--primary',
            'footer button.artdeco-button--primary',
            'div[role="dialog"] button.artdeco-button--primary',
        ]
        
        for selector in publish_selectors:
            try:
                btn = self.page.locator(selector).first
                if btn.is_visible(timeout=1500):
                    # Vérifier que le bouton est activé
                    if btn.is_enabled():
                        btn_text = btn.text_content().strip()
                        logger.info(f"✅ Bouton trouvé: '{btn_text}' ({selector})")
                        btn.click(force=True)
                        return True
            except:
                continue
        
        # Fallback JavaScript - recherche intelligente
        logger.info("Recherche via JavaScript...")
        try:
            clicked = self.page.evaluate("""
                () => {
                    // Mots-clés pour le bouton de publication
                    const publishKeywords = ['post', 'publier', 'poster', 'share', 'partager', 'send', 'envoyer', 'publish'];
                    
                    // Chercher dans le modal de partage
                    const modal = document.querySelector('.share-box, .artdeco-modal, div[role="dialog"]');
                    const searchContainer = modal || document;
                    
                    // Chercher tous les boutons
                    const buttons = searchContainer.querySelectorAll('button');
                    
                    // Premier passage: boutons primaires avec le bon texte
                    for (const btn of buttons) {
                        if (btn.disabled) continue;
                        
                        const text = btn.textContent.trim().toLowerCase();
                        const ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();
                        const classes = btn.className.toLowerCase();
                        
                        const isPrimary = classes.includes('primary') || 
                                         classes.includes('share-actions') ||
                                         btn.closest('.share-box-footer, .share-actions, footer');
                        
                        const isPublishButton = publishKeywords.some(keyword => 
                            text === keyword || ariaLabel === keyword
                        );
                        
                        if (isPrimary && isPublishButton) {
                            console.log('Clicking publish button:', btn.textContent);
                            btn.click();
                            return { success: true, text: btn.textContent.trim() };
                        }
                    }
                    
                    // Deuxième passage: n'importe quel bouton avec le bon texte
                    for (const btn of buttons) {
                        if (btn.disabled) continue;
                        
                        const text = btn.textContent.trim().toLowerCase();
                        
                        if (publishKeywords.some(keyword => text === keyword)) {
                            console.log('Clicking button by text:', btn.textContent);
                            btn.click();
                            return { success: true, text: btn.textContent.trim() };
                        }
                    }
                    
                    // Troisième passage: bouton primaire dans le footer
                    const footers = searchContainer.querySelectorAll('.share-box-footer, .share-actions, footer, [class*="footer"]');
                    for (const footer of footers) {
                        const primaryBtn = footer.querySelector('button.artdeco-button--primary, button[class*="primary"]');
                        if (primaryBtn && !primaryBtn.disabled) {
                            console.log('Clicking primary button in footer:', primaryBtn.textContent);
                            primaryBtn.click();
                            return { success: true, text: primaryBtn.textContent.trim() };
                        }
                    }
                    
                    return { success: false };
                }
            """)
            
            if clicked and clicked.get('success'):
                logger.info(f"✅ Bouton cliqué via JS: '{clicked.get('text')}'")
                return True
        except Exception as e:
            logger.debug(f"JavaScript fallback failed: {e}")
        
        # Dernier recours: cliquer sur le dernier bouton primaire visible
        logger.info("Dernier recours: bouton primaire le plus récent...")
        try:
            all_primary = self.page.locator('button.artdeco-button--primary').all()
            for btn in reversed(all_primary):
                try:
                    if btn.is_visible() and btn.is_enabled():
                        btn_text = btn.text_content().strip()
                        logger.info(f"Clic sur bouton primaire: '{btn_text}'")
                        btn.click(force=True)
                        return True
                except:
                    continue
        except:
            pass
        
        logger.error("❌ Bouton de publication non trouvé!")
        return False
    
    def _publish(self, text: str, image_path: str = None, video_path: str = None) -> bool:
        """Publie sur LinkedIn."""
        try:
            logger.info("Publication sur LinkedIn...")
            
            self.page.goto(self.FEED_URL, wait_until='domcontentloaded', timeout=30000)
            self._random_delay(2, 3)
            self._dismiss_popups()
            
            # ===== ÉTAPE 1: Ouvrir le modal =====
            logger.info("Étape 1: Ouverture du modal...")
            
            start_selectors = [
                'button[aria-label*="Start a post"]',
                'button[aria-label*="Commencer un post"]',
                '.share-box-feed-entry__trigger',
                'button:has-text("Start a post")',
                'button:has-text("Commencer un post")',
            ]
            
            clicked = False
            for selector in start_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if btn.is_visible(timeout=3000):
                        btn.click(force=True)
                        clicked = True
                        logger.info(f"Modal ouvert: {selector}")
                        break
                except:
                    continue
            
            if not clicked:
                raise Exception("Bouton 'Start a post' non trouvé")
            
            self._random_delay(2, 3)
            self._take_screenshot("modal_opened")
            
            # ===== ÉTAPE 2: Saisir le texte =====
            logger.info("Étape 2: Saisie du texte...")
            
            editor_selectors = [
                '.ql-editor[data-placeholder]',
                '.ql-editor',
                'div[contenteditable="true"][role="textbox"]',
                '[aria-label="Text editor for creating content"]',
                '[aria-label="Éditeur de texte pour créer du contenu"]',
            ]
            
            editor = None
            for selector in editor_selectors:
                try:
                    field = self.page.locator(selector).first
                    if field.is_visible(timeout=5000):
                        editor = field
                        break
                except:
                    continue
            
            if not editor:
                raise Exception("Éditeur de texte non trouvé")
            
            editor.click(force=True)
            self._random_delay(0.5, 1)
            editor.type(text, delay=25)
            
            self._random_delay(2, 3)
            self._take_screenshot("text_entered")
            
            # ===== ÉTAPE 3: Ajouter l'image =====
            if image_path and Path(image_path).exists():
                logger.info("Étape 3: Ajout de l'image...")
                try:
                    file_input = self.page.locator('input[type="file"][accept*="image"]').first
                    file_input.set_input_files(image_path)
                    self._random_delay(3, 5)
                    logger.info("✅ Image ajoutée")
                    self._take_screenshot("image_added")
                except Exception as e:
                    logger.warning(f"Impossible d'ajouter l'image: {e}")
            
            # ===== ÉTAPE 4: Publier =====
            logger.info("Étape 4: Publication...")
            self._take_screenshot("before_publish")
            
            if self._click_publish_button():
                self._random_delay(3, 5)
                self._take_screenshot("after_publish")
                
                # Vérifier si le modal s'est fermé
                try:
                    modal_still_visible = self.page.locator('.share-box, .artdeco-modal').first.is_visible(timeout=3000)
                    if modal_still_visible:
                        # Peut-être un message d'erreur
                        error = self.page.locator('.artdeco-inline-feedback--error').first
                        if error.is_visible(timeout=1000):
                            logger.error(f"Erreur: {error.text_content()}")
                            return False
                except:
                    pass  # Modal fermé = succès
                
                logger.info("✅ Publication LinkedIn terminée!")
                return True
            else:
                self._take_screenshot("publish_button_not_found")
                raise Exception("Impossible de publier: bouton non trouvé")
            
        except Exception as e:
            logger.error(f"Erreur publication LinkedIn: {e}")
            self._take_screenshot("publish_error")
            return False