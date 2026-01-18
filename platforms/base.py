"""
Budget Famille - Base Poster
=============================
Classe de base pour tous les posters de réseaux sociaux.
"""

import os
import time
import random
from abc import ABC, abstractmethod
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Browser
from utils.logger import get_logger

logger = get_logger(__name__)


class BasePoster(ABC):
    """
    Classe de base abstraite pour les posters de réseaux sociaux.
    Fournit les fonctionnalités communes et définit l'interface.
    """
    
    PLATFORM_NAME = "base"
    LOGIN_URL = ""
    
    def __init__(self, headless: bool = True):
        """
        Initialise le poster.
        
        Args:
            headless: Si True, le navigateur est invisible
        """
        self.headless = headless
        self.browser = None
        self.page = None
        self.playwright = None
        
        # Dossier pour les screenshots de debug
        self.screenshots_dir = Path('screenshots')
        self.screenshots_dir.mkdir(exist_ok=True)
        
        # State file pour la persistence de session
        self.state_file = Path(f'browser_data/{self.PLATFORM_NAME}_state.json')
        self.state_file.parent.mkdir(exist_ok=True)
    
    def _random_delay(self, min_sec: float = 1.0, max_sec: float = 3.0):
        """Ajoute un délai aléatoire pour simuler un comportement humain."""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)
    
    def _human_type(self, page: Page, selector: str, text: str):
        """
        Tape du texte avec une vitesse humaine.
        
        Args:
            page: Page Playwright
            selector: Sélecteur CSS de l'élément
            text: Texte à taper
        """
        element = page.locator(selector)
        element.click()
        
        for char in text:
            element.type(char, delay=random.randint(30, 100))
            
            # Pause occasionnelle
            if random.random() < 0.1:
                time.sleep(random.uniform(0.1, 0.3))
    
    def _take_screenshot(self, name: str):
        """Prend une capture d'écran pour le debug."""
        if self.page:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = self.screenshots_dir / f"{self.PLATFORM_NAME}_{name}_{timestamp}.png"
            self.page.screenshot(path=str(filename))
            logger.debug(f"Screenshot saved: {filename}")
    
    def _start_browser(self):
        """Démarre le navigateur avec les paramètres appropriés."""
        self.playwright = sync_playwright().start()
        
        # Options du navigateur pour éviter la détection
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-infobars',
            '--window-size=1920,1080',
            '--start-maximized',
        ]
        
        # Lancer le navigateur
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=browser_args
        )
        
        # Créer un contexte avec un user agent réaliste
        context_options = {
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'locale': 'fr-FR',
            'timezone_id': 'Europe/Paris',
        }
        
        # Charger l'état de session si disponible
        if self.state_file.exists():
            context_options['storage_state'] = str(self.state_file)
            logger.info(f"Session chargée depuis {self.state_file}")
        
        context = self.browser.new_context(**context_options)
        
        # Masquer les signes d'automatisation
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['fr-FR', 'fr', 'en']
            });
        """)
        
        self.page = context.new_page()
        
        # Timeout par défaut
        self.page.set_default_timeout(30000)
        
        logger.info(f"Navigateur démarré (headless={self.headless})")
    
    def _save_session(self):
        """Sauvegarde l'état de session pour éviter de se reconnecter."""
        if self.page:
            self.page.context.storage_state(path=str(self.state_file))
            logger.info(f"Session sauvegardée dans {self.state_file}")
    
    def _close_browser(self):
        """Ferme proprement le navigateur."""
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            logger.error(f"Erreur lors de la fermeture: {e}")
    
    def _check_logged_in(self) -> bool:
        """
        Vérifie si on est déjà connecté.
        À implémenter dans chaque sous-classe.
        """
        return False
    
    @abstractmethod
    def _login(self) -> bool:
        """
        Se connecte à la plateforme.
        À implémenter dans chaque sous-classe.
        
        Returns:
            True si la connexion a réussi
        """
        pass
    
    @abstractmethod
    def _publish(self, text: str, image_path: str = None, video_path: str = None) -> bool:
        """
        Publie le contenu sur la plateforme.
        À implémenter dans chaque sous-classe.
        
        Args:
            text: Texte du post
            image_path: Chemin vers l'image (optionnel)
            video_path: Chemin vers la vidéo (optionnel)
            
        Returns:
            True si la publication a réussi
        """
        pass
    
    def post(self, text: str, image_path: str = None, video_path: str = None) -> dict:
        """
        Méthode principale pour publier un post.
        
        Args:
            text: Texte du post
            image_path: Chemin vers l'image (optionnel)
            video_path: Chemin vers la vidéo (optionnel)
            
        Returns:
            Dictionnaire avec le résultat de la publication
        """
        result = {
            'success': False,
            'platform': self.PLATFORM_NAME,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'error': None
        }
        
        try:
            logger.info(f"Démarrage de la publication sur {self.PLATFORM_NAME}")
            
            # Démarrer le navigateur
            self._start_browser()
            
            # Vérifier si déjà connecté
            self.page.goto(self.LOGIN_URL)
            self._random_delay(2, 4)
            
            if not self._check_logged_in():
                logger.info("Connexion requise...")
                if not self._login():
                    raise Exception("Échec de la connexion")
                
                # Sauvegarder la session
                self._save_session()
            else:
                logger.info("Déjà connecté (session sauvegardée)")
            
            # Publier le contenu
            self._random_delay(2, 4)
            
            if not self._publish(text, image_path, video_path):
                raise Exception("Échec de la publication")
            
            result['success'] = True
            logger.info(f"✅ Publication réussie sur {self.PLATFORM_NAME}")
            
        except Exception as e:
            error_msg = str(e)
            result['error'] = error_msg
            logger.error(f"❌ Erreur sur {self.PLATFORM_NAME}: {error_msg}")
            
            # Screenshot d'erreur
            self._take_screenshot("error")
            
        finally:
            self._close_browser()
        
        return result


class PostContent:
    """Classe utilitaire pour formater le contenu des posts."""
    
    @staticmethod
    def truncate_for_twitter(text: str, max_length: int = 280) -> str:
        """Tronque le texte pour X/Twitter."""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    @staticmethod
    def add_line_breaks(text: str, platform: str) -> str:
        """Ajoute des sauts de ligne appropriés selon la plateforme."""
        # LinkedIn et Facebook supportent les sauts de ligne
        # Instagram et Twitter préfèrent moins de sauts de ligne
        if platform in ['instagram', 'twitter']:
            # Remplacer les doubles sauts par des simples
            text = text.replace('\n\n', '\n')
        return text
    
    @staticmethod
    def extract_hashtags(text: str) -> list:
        """Extrait les hashtags du texte."""
        import re
        return re.findall(r'#\w+', text)
