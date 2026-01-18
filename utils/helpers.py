"""
Budget Famille - Helpers
=========================
Fonctions utilitaires pour le bot.
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from utils.logger import get_logger

logger = get_logger(__name__)


def load_post(post_dir: Path) -> Dict[str, Any]:
    """
    Charge un post depuis un dossier.
    
    Args:
        post_dir: Chemin vers le dossier du post
        
    Returns:
        Dictionnaire avec le contenu du post
    """
    post = {
        'date': post_dir.name,
        'text': '',
        'image': None,
        'video': None,
        'platforms': None,  # None = toutes les plateformes
    }
    
    # Charger le texte (caption.txt)
    caption_file = post_dir / 'caption.txt'
    if caption_file.exists():
        with open(caption_file, 'r', encoding='utf-8') as f:
            post['text'] = f.read().strip()
    else:
        logger.warning(f"Pas de caption.txt dans {post_dir}")
    
    # Chercher une image
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    for ext in image_extensions:
        image_file = post_dir / f'image{ext}'
        if image_file.exists():
            post['image'] = str(image_file.absolute())
            break
        
        # Chercher aussi n'importe quel fichier image
        for file in post_dir.glob(f'*{ext}'):
            post['image'] = str(file.absolute())
            break
        
        if post['image']:
            break
    
    # Chercher une vidéo
    video_extensions = ['.mp4', '.mov', '.avi', '.webm']
    for ext in video_extensions:
        video_file = post_dir / f'video{ext}'
        if video_file.exists():
            post['video'] = str(video_file.absolute())
            break
        
        for file in post_dir.glob(f'*{ext}'):
            post['video'] = str(file.absolute())
            break
        
        if post['video']:
            break
    
    # Charger la configuration optionnelle
    config_file = post_dir / 'config.json'
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            if 'platforms' in config:
                post['platforms'] = config['platforms']
            
            if 'schedule' in config:
                post['schedule'] = config['schedule']
                
        except json.JSONDecodeError as e:
            logger.error(f"Erreur parsing config.json: {e}")
    
    return post


def validate_post(post: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Valide un post avant publication.
    
    Args:
        post: Dictionnaire du post
        
    Returns:
        Tuple (is_valid, list of errors)
    """
    errors = []
    
    # Vérifier le texte
    if not post.get('text'):
        errors.append("Le texte (caption.txt) est vide")
    
    # Vérifier la longueur pour Twitter
    if post.get('text') and len(post['text']) > 280:
        # Pas une erreur, juste un warning - sera tronqué automatiquement
        logger.warning(f"Texte de {len(post['text'])} caractères sera tronqué pour Twitter")
    
    # Vérifier les fichiers média
    if post.get('image') and not Path(post['image']).exists():
        errors.append(f"Image non trouvée: {post['image']}")
    
    if post.get('video') and not Path(post['video']).exists():
        errors.append(f"Vidéo non trouvée: {post['video']}")
    
    # Instagram nécessite un média
    platforms = post.get('platforms', ['linkedin', 'instagram', 'facebook', 'twitter'])
    if 'instagram' in platforms and not post.get('image') and not post.get('video'):
        errors.append("Instagram nécessite une image ou une vidéo")
    
    return len(errors) == 0, errors


def get_pending_posts(posts_dir: Path) -> List[Dict[str, Any]]:
    """
    Récupère tous les posts en attente de publication.
    
    Args:
        posts_dir: Chemin vers le dossier des posts
        
    Returns:
        Liste des posts triés par date
    """
    posts = []
    
    if not posts_dir.exists():
        logger.warning(f"Dossier des posts non trouvé: {posts_dir}")
        return posts
    
    # Parcourir tous les sous-dossiers
    for item in posts_dir.iterdir():
        if not item.is_dir():
            continue
        
        # Ignorer les dossiers cachés et les exemples
        if item.name.startswith('.') or item.name.startswith('_'):
            continue
        
        # Charger le post
        post = load_post(item)
        
        # Valider
        is_valid, errors = validate_post(post)
        
        if not is_valid:
            logger.warning(f"Post {item.name} invalide: {errors}")
            continue
        
        # Vérifier la date de planification si présente
        if 'schedule' in post:
            try:
                scheduled_time = datetime.fromisoformat(post['schedule'])
                if scheduled_time > datetime.now():
                    logger.info(f"Post {item.name} planifié pour {scheduled_time}")
                    continue  # Pas encore l'heure
            except ValueError:
                pass
        
        posts.append(post)
    
    # Trier par date (nom du dossier)
    posts.sort(key=lambda p: p['date'])
    
    return posts


def archive_post(post_dir: Path):
    """
    Archive un post après publication.
    
    Args:
        post_dir: Chemin vers le dossier du post
    """
    archive_dir = post_dir.parent / '_published'
    archive_dir.mkdir(exist_ok=True)
    
    # Ajouter un timestamp au nom
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    new_name = f"{post_dir.name}_{timestamp}"
    
    # Déplacer le dossier
    new_path = archive_dir / new_name
    post_dir.rename(new_path)
    
    logger.info(f"Post archivé: {new_path}")


def format_text_for_platform(text: str, platform: str) -> str:
    """
    Formate le texte selon la plateforme.
    
    Args:
        text: Texte original
        platform: Nom de la plateforme
        
    Returns:
        Texte formaté
    """
    if platform == 'twitter':
        # Tronquer pour Twitter
        if len(text) > 280:
            # Trouver un bon point de coupure
            truncated = text[:277]
            
            # Essayer de couper à un espace
            last_space = truncated.rfind(' ')
            if last_space > 200:
                truncated = truncated[:last_space]
            
            return truncated + "..."
    
    elif platform == 'linkedin':
        # LinkedIn supporte plus de caractères mais préfère les paragraphes
        # Ajouter des sauts de ligne après les phrases si absent
        pass
    
    elif platform == 'instagram':
        # Instagram a une limite de 2200 caractères
        if len(text) > 2200:
            text = text[:2197] + "..."
    
    return text


def extract_hashtags(text: str) -> List[str]:
    """
    Extrait les hashtags d'un texte.
    
    Args:
        text: Texte contenant des hashtags
        
    Returns:
        Liste des hashtags
    """
    return re.findall(r'#\w+', text)


def create_post_from_template(template_name: str, variables: Dict[str, str]) -> str:
    """
    Crée un texte de post à partir d'un template.
    
    Args:
        template_name: Nom du fichier template (sans extension)
        variables: Dictionnaire de variables à remplacer
        
    Returns:
        Texte formaté
    """
    templates_dir = Path('templates')
    template_file = templates_dir / f'{template_name}.txt'
    
    if not template_file.exists():
        raise FileNotFoundError(f"Template non trouvé: {template_file}")
    
    with open(template_file, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # Remplacer les variables {{variable}}
    for key, value in variables.items():
        template = template.replace(f'{{{{{key}}}}}', value)
    
    return template


def get_optimal_posting_time(platform: str) -> str:
    """
    Retourne l'heure optimale de publication pour une plateforme.
    
    Args:
        platform: Nom de la plateforme
        
    Returns:
        Heure au format HH:MM
    """
    # Basé sur des études de marketing digital
    optimal_times = {
        'linkedin': '10:00',    # Mardi-Jeudi, 10h-12h
        'instagram': '11:00',   # Lundi, Mercredi, 11h
        'facebook': '13:00',    # Mercredi, 13h-16h
        'twitter': '09:00',     # Mercredi, 9h-12h
    }
    
    return optimal_times.get(platform, '10:00')


def estimate_post_time(platforms: List[str]) -> int:
    """
    Estime le temps total de publication en secondes.
    
    Args:
        platforms: Liste des plateformes
        
    Returns:
        Temps estimé en secondes
    """
    delay_between = int(os.getenv('DELAY_BETWEEN_POSTS', 300))
    time_per_platform = 60  # ~1 minute par plateforme
    
    total = len(platforms) * time_per_platform
    total += (len(platforms) - 1) * delay_between
    
    return total
