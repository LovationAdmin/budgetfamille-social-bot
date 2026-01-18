"""
Budget Famille - Logger
========================
Configuration du système de logging.
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Créer le dossier de logs s'il n'existe pas
LOGS_DIR = Path('logs')
LOGS_DIR.mkdir(exist_ok=True)

# Format de log
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def setup_logger(name: str = 'budgetfamille-bot', level: str = None) -> logging.Logger:
    """
    Configure et retourne le logger principal.
    
    Args:
        name: Nom du logger
        level: Niveau de log (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Logger configuré
    """
    # Déterminer le niveau de log
    if level is None:
        level = 'DEBUG' if os.getenv('DEBUG_MODE', 'false').lower() == 'true' else 'INFO'
    
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Créer le logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Éviter les doublons de handlers
    if logger.handlers:
        return logger
    
    # Handler console avec couleurs
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Essayer d'utiliser colorlog si disponible
    try:
        import colorlog
        console_formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(levelname)s - %(message)s%(reset)s',
            datefmt=DATE_FORMAT,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
    except ImportError:
        console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Handler fichier (un fichier par jour)
    today = datetime.now().strftime('%Y-%m-%d')
    file_handler = RotatingFileHandler(
        LOGS_DIR / f'{today}.log',
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Handler pour les erreurs uniquement
    error_handler = RotatingFileHandler(
        LOGS_DIR / 'errors.log',
        maxBytes=5*1024*1024,  # 5 MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    logger.addHandler(error_handler)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Récupère un logger enfant.
    
    Args:
        name: Nom du module (ex: platforms.linkedin)
        
    Returns:
        Logger
    """
    parent_logger = logging.getLogger('budgetfamille-bot')
    
    if name:
        return parent_logger.getChild(name)
    
    return parent_logger


class LogCapture:
    """Context manager pour capturer les logs."""
    
    def __init__(self, logger_name: str = 'budgetfamille-bot'):
        self.logger = logging.getLogger(logger_name)
        self.captured = []
        self.handler = None
    
    def __enter__(self):
        class CaptureHandler(logging.Handler):
            def __init__(self, captured_list):
                super().__init__()
                self.captured = captured_list
            
            def emit(self, record):
                self.captured.append({
                    'level': record.levelname,
                    'message': record.getMessage(),
                    'time': datetime.fromtimestamp(record.created)
                })
        
        self.handler = CaptureHandler(self.captured)
        self.logger.addHandler(self.handler)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.handler:
            self.logger.removeHandler(self.handler)
    
    def get_errors(self):
        """Retourne uniquement les erreurs capturées."""
        return [log for log in self.captured if log['level'] in ('ERROR', 'CRITICAL')]
    
    def get_warnings(self):
        """Retourne les warnings et erreurs."""
        return [log for log in self.captured if log['level'] in ('WARNING', 'ERROR', 'CRITICAL')]
