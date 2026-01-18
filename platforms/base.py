"""
Budget Famille - Base Poster (Fixed v3)
========================================
Utilise le profil Chrome existant de l'utilisateur pour éviter les blocages de sécurité.
"""

import os
import time
import random
from abc import ABC, abstractmethod
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Browser
from utils.logger import get_logger

logger = get_logger(__name__)


def get_chrome_path():
    """Trouve le chemin de Chrome selon l'OS."""
    import platform
    system = platform.system()
    
    if system == "Windows":
        paths = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        ]
    elif system == "Darwin":  # macOS
        paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ]
    else:  # Linux
        paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium-browser",
        ]
    
    for path in paths:
        if os.path.exists(path):
            return path
    
    return None


def get_chrome_user_data_dir():
    """Trouve le dossier User Data de Chrome."""
    import platform
    system = platform.system()
    
    if system == "Windows":
        return os.path.expandvars(r"%LocalAppData%\Google\Chrome\User Data")
    elif system == "Darwin":  # macOS
        return os.path.expanduser("~/Library/Application Support/Google/Chrome")
    else:  # Linux
        return os.path.expanduser("~/.config/google-chrome")


class BasePoster(ABC):
    """
    Classe de base pour les posters de réseaux sociaux.
    Utilise le profil Chrome existant pour réutiliser les sessions.
    """
    
    PLATFORM_NAME = "base"
    LOGIN_URL = ""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.page = None
        self.playwright = None
        self.context = None
        
        # Dossier pour les screenshots
        self.screenshots_dir = Path('screenshots')
        self.screenshots_dir.mkdir(exist_ok=True)
        
        # Utiliser le profil Chrome existant ?
        self.use_existing_chrome = os.getenv('USE_EXISTING_CHROME', 'true').lower() == 'true'
    
    def _random_delay(self, min_sec: float = 1.0, max_sec: float = 3.0):
        """Délai aléatoire pour simuler un comportement humain."""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)
    
    def _take_screenshot(self, name: str):
        """Capture d'écran pour debug."""
        if self.page:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = self.screenshots_dir / f"{self.PLATFORM_NAME}_{name}_{timestamp}.png"
            try:
                self.page.screenshot(path=str(filename))
                logger.debug(f"Screenshot: {filename}")
            except:
                pass
    
    def _start_browser(self):
        """Démarre le navigateur en utilisant le profil Chrome existant."""
        self.playwright = sync_playwright().start()
        
        chrome_path = get_chrome_path()
        user_data_dir = get_chrome_user_data_dir()
        
        if self.use_existing_chrome and chrome_path and os.path.exists(user_data_dir):
            logger.info("🔓 Utilisation du profil Chrome existant (sessions sauvegardées)")
            
            # IMPORTANT: Ferme Chrome avant de lancer le bot !
            # Playwright ne peut pas utiliser un profil déjà ouvert
            
            try:
                # Lancer Chrome avec le profil utilisateur existant
                self.context = self.playwright.chromium.launch_persistent_context(
                    user_data_dir=user_data_dir,
                    channel="chrome",  # Utilise Chrome installé, pas Chromium
                    headless=self.headless,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                    ],
                    viewport={'width': 1920, 'height': 1080},
                    locale='fr-FR',
                    timezone_id='Europe/Paris',
                )
                
                # Utiliser la première page ou en créer une
                if self.context.pages:
                    self.page = self.context.pages[0]
                else:
                    self.page = self.context.new_page()
                
                logger.info("✅ Chrome lancé avec ton profil existant")
                
            except Exception as e:
                logger.warning(f"⚠️ Impossible d'utiliser le profil Chrome: {e}")
                logger.info("Fallback vers navigateur isolé...")
                self._start_isolated_browser()
        else:
            logger.info("Utilisation d'un navigateur isolé")
            self._start_isolated_browser()
        
        self.page.set_default_timeout(60000)  # 60 secondes timeout
    
    def _start_isolated_browser(self):
        """Démarre un navigateur avec un profil dédié au bot (cookies sauvegardés)."""
        # Créer le dossier pour le profil du bot s'il n'existe pas
        user_data_dir = Path('browser_data')
        user_data_dir.mkdir(exist_ok=True)
        
        logger.info(f"📂 Utilisation du profil dédié : {user_data_dir.absolute()}")

        # Lancement en mode persistant (sauvegarde les cookies ici)
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            channel="chrome",  # Utilise votre vrai Chrome
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-infobars',
            ],
            viewport={'width': 1280, 'height': 720},
            locale='fr-FR',
            timezone_id='Europe/Paris',
        )
        
        # Récupérer la première page
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = self.context.new_page()


    def _close_browser(self):
        """Ferme proprement le navigateur."""
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            logger.error(f"Erreur fermeture: {e}")
    
    def _check_logged_in(self) -> bool:
        """Vérifie si connecté. À implémenter."""
        return False
    
    @abstractmethod
    def _login(self) -> bool:
        """Se connecte. À implémenter."""
        pass
    
    @abstractmethod
    def _publish(self, text: str, image_path: str = None, video_path: str = None) -> bool:
        """Publie. À implémenter."""
        pass
    
    def post(self, text: str, image_path: str = None, video_path: str = None) -> dict:
        """Méthode principale pour publier."""
        result = {
            'success': False,
            'platform': self.PLATFORM_NAME,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'error': None
        }
        
        try:
            logger.info(f"Démarrage publication sur {self.PLATFORM_NAME}")
            
            self._start_browser()
            
            # Aller sur la page
            self.page.goto(self.LOGIN_URL, wait_until='domcontentloaded', timeout=60000)
            self._random_delay(2, 4)
            
            # Vérifier si déjà connecté (grâce au profil Chrome)
            if not self._check_logged_in():
                logger.info("Connexion requise...")
                if not self._login():
                    raise Exception("Échec de la connexion")
            else:
                logger.info("✅ Déjà connecté (session Chrome existante)")
            
            # Publier
            self._random_delay(2, 4)
            
            if not self._publish(text, image_path, video_path):
                raise Exception("Échec de la publication")
            
            result['success'] = True
            logger.info(f"✅ Publication réussie sur {self.PLATFORM_NAME}")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"❌ Erreur sur {self.PLATFORM_NAME}: {e}")
            self._take_screenshot("error")
            
        finally:
            self._close_browser()
        
        return result


class PostContent:
    """Utilitaire pour formater le contenu."""
    
    @staticmethod
    def truncate_for_twitter(text: str, max_length: int = 280) -> str:
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
