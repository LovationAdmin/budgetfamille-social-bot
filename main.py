#!/usr/bin/env python3
"""
Budget Famille - Social Media Bot
==================================
Script principal pour publier automatiquement sur les réseaux sociaux.

Usage:
    python main.py                      # Publie tous les posts en attente
    python main.py --platform linkedin  # Publie uniquement sur LinkedIn
    python main.py --post 2025-01-20    # Publie un post spécifique
    python main.py --visible            # Mode visible (debug)
    python main.py --dry-run            # Simule sans publier
"""

import os
import sys
import json
import time
import click
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import print as rprint

# Import des modules de publication
from platforms.linkedin import LinkedInPoster
from platforms.instagram import InstagramPoster
from platforms.facebook import FacebookPoster
from platforms.twitter import TwitterPoster
from utils.logger import setup_logger
from utils.helpers import load_post, validate_post, get_pending_posts

# Charger les variables d'environnement
load_dotenv()

# Console Rich pour l'affichage
console = Console()

# Configuration des plateformes
PLATFORMS = {
    'linkedin': LinkedInPoster,
    'instagram': InstagramPoster,
    'facebook': FacebookPoster,
    'twitter': TwitterPoster,
}

# Emojis pour chaque plateforme
PLATFORM_EMOJIS = {
    'linkedin': '💼',
    'instagram': '📸',
    'facebook': '👥',
    'twitter': '🐦',
}


def print_banner():
    """Affiche la bannière du bot."""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║   🚀 BUDGET FAMILLE - Social Media Bot                      ║
    ║                                                              ║
    ║   Automatisation de publication sur les réseaux sociaux     ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")


def check_credentials():
    """Vérifie que les identifiants sont configurés."""
    missing = []
    
    credentials_map = {
        'LinkedIn': ['LINKEDIN_EMAIL', 'LINKEDIN_PASS'],
        'Instagram': ['INSTAGRAM_USER', 'INSTAGRAM_PASS'],
        'Facebook': ['FACEBOOK_EMAIL', 'FACEBOOK_PASS'],
        'Twitter': ['TWITTER_USER', 'TWITTER_PASS'],
    }
    
    for platform, creds in credentials_map.items():
        for cred in creds:
            if not os.getenv(cred):
                missing.append(f"{platform}: {cred}")
    
    if missing:
        console.print("\n⚠️  [yellow]Identifiants manquants:[/yellow]")
        for m in missing:
            console.print(f"   • {m}")
        console.print("\n💡 Copiez .env.example vers .env et remplissez vos identifiants.\n")
        return False
    
    return True


def display_posts_table(posts: list):
    """Affiche un tableau des posts à publier."""
    table = Table(title="📋 Posts en attente")
    table.add_column("Date", style="cyan")
    table.add_column("Texte (aperçu)", style="white")
    table.add_column("Média", style="green")
    table.add_column("Plateformes", style="magenta")
    
    for post in posts:
        text_preview = post['text'][:50] + "..." if len(post['text']) > 50 else post['text']
        media = "📷" if post.get('image') else ("🎬" if post.get('video') else "—")
        platforms = ", ".join([PLATFORM_EMOJIS.get(p, p) for p in post.get('platforms', PLATFORMS.keys())])
        
        table.add_row(post['date'], text_preview, media, platforms)
    
    console.print(table)


def publish_post(post: dict, platforms: list, headless: bool = True, dry_run: bool = False):
    """
    Publie un post sur les plateformes spécifiées.
    
    Args:
        post: Dictionnaire contenant le contenu du post
        platforms: Liste des plateformes cibles
        headless: Si False, affiche le navigateur
        dry_run: Si True, simule sans publier
    """
    results = {}
    delay = int(os.getenv('DELAY_BETWEEN_POSTS', 300))
    
    for i, platform_name in enumerate(platforms):
        if platform_name not in PLATFORMS:
            console.print(f"❌ Plateforme inconnue: {platform_name}", style="red")
            results[platform_name] = {'success': False, 'error': 'Unknown platform'}
            continue
        
        emoji = PLATFORM_EMOJIS.get(platform_name, '📱')
        
        if dry_run:
            console.print(f"{emoji} [yellow][DRY RUN][/yellow] {platform_name.capitalize()}: Publication simulée")
            results[platform_name] = {'success': True, 'dry_run': True}
            continue
        
        with Progress(
            SpinnerColumn(),
            TextColumn(f"{emoji} Publication sur {platform_name.capitalize()}..."),
            console=console
        ) as progress:
            task = progress.add_task("posting", total=None)
            
            try:
                poster_class = PLATFORMS[platform_name]
                poster = poster_class(headless=headless)
                
                result = poster.post(
                    text=post['text'],
                    image_path=post.get('image'),
                    video_path=post.get('video')
                )
                
                if result['success']:
                    console.print(f"{emoji} ✅ {platform_name.capitalize()}: Publié avec succès!", style="green")
                else:
                    console.print(f"{emoji} ❌ {platform_name.capitalize()}: {result.get('error', 'Erreur inconnue')}", style="red")
                
                results[platform_name] = result
                
            except Exception as e:
                error_msg = str(e)
                console.print(f"{emoji} ❌ {platform_name.capitalize()}: {error_msg}", style="red")
                results[platform_name] = {'success': False, 'error': error_msg}
        
        # Attendre entre les publications (sauf pour le dernier)
        if i < len(platforms) - 1 and not dry_run:
            console.print(f"\n⏳ Pause de {delay} secondes avant la prochaine publication...\n")
            time.sleep(delay)
    
    return results


def save_results(post_date: str, results: dict):
    """Sauvegarde les résultats de publication."""
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'post_date': post_date,
        'results': results
    }
    
    # Charger les logs existants ou créer une nouvelle liste
    if log_file.exists():
        with open(log_file, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    else:
        logs = []
    
    logs.append(log_entry)
    
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)
    
    console.print(f"\n📝 Résultats sauvegardés dans {log_file}")


@click.command()
@click.option('--platform', '-p', type=click.Choice(list(PLATFORMS.keys())), 
              help='Publier uniquement sur cette plateforme')
@click.option('--post', '-o', 'post_name', type=str, 
              help='Publier uniquement ce post (nom du dossier)')
@click.option('--visible', '-v', is_flag=True, 
              help='Afficher le navigateur (mode debug)')
@click.option('--dry-run', '-d', is_flag=True, 
              help='Simuler sans publier')
@click.option('--list', '-l', 'list_posts', is_flag=True, 
              help='Lister les posts en attente')
def main(platform, post_name, visible, dry_run, list_posts):
    """
    Budget Famille - Bot de publication sur les réseaux sociaux.
    
    Publie automatiquement vos posts sur LinkedIn, Instagram, Facebook et X.
    """
    print_banner()
    
    # Setup logger
    logger = setup_logger()
    logger.info("Démarrage du bot")
    
    # Vérifier les identifiants
    if not dry_run and not list_posts:
        if not check_credentials():
            sys.exit(1)
    
    # Récupérer les posts
    posts_folder = Path(os.getenv('POSTS_FOLDER', 'posts'))
    
    if post_name:
        # Un seul post spécifié
        post_path = posts_folder / post_name
        if not post_path.exists():
            console.print(f"❌ Post non trouvé: {post_path}", style="red")
            sys.exit(1)
        posts = [load_post(post_path)]
    else:
        # Tous les posts en attente
        posts = get_pending_posts(posts_folder)
    
    if not posts:
        console.print("\n📭 Aucun post en attente de publication.\n", style="yellow")
        console.print("💡 Créez un dossier dans 'posts/' avec un fichier caption.txt")
        sys.exit(0)
    
    # Lister uniquement
    if list_posts:
        display_posts_table(posts)
        sys.exit(0)
    
    # Afficher le récapitulatif
    display_posts_table(posts)
    
    # Demander confirmation
    if not dry_run:
        if not click.confirm('\n🚀 Voulez-vous lancer la publication?', default=True):
            console.print("❌ Publication annulée.", style="yellow")
            sys.exit(0)
    
    console.print("\n" + "═" * 60)
    console.print("🚀 DÉMARRAGE DE LA PUBLICATION", style="bold cyan")
    console.print("═" * 60 + "\n")
    
    # Déterminer les plateformes cibles
    target_platforms = [platform] if platform else list(PLATFORMS.keys())
    
    # Publier chaque post
    all_results = {}
    
    for i, post in enumerate(posts):
        console.print(Panel(f"📝 Post {i+1}/{len(posts)}: {post['date']}", style="cyan"))
        
        # Utiliser les plateformes du config.json si disponible
        post_platforms = post.get('platforms', target_platforms)
        if platform:
            post_platforms = [platform]
        
        results = publish_post(
            post=post,
            platforms=post_platforms,
            headless=not visible,
            dry_run=dry_run
        )
        
        all_results[post['date']] = results
        save_results(post['date'], results)
        
        # Pause entre les posts
        if i < len(posts) - 1 and not dry_run:
            console.print(f"\n⏳ Pause de 60 secondes avant le prochain post...\n")
            time.sleep(60)
    
    # Résumé final
    console.print("\n" + "═" * 60)
    console.print("📊 RÉSUMÉ DE PUBLICATION", style="bold cyan")
    console.print("═" * 60 + "\n")
    
    success_count = 0
    fail_count = 0
    
    for post_date, results in all_results.items():
        for platform_name, result in results.items():
            if result.get('success'):
                success_count += 1
            else:
                fail_count += 1
    
    summary_table = Table()
    summary_table.add_column("Métrique", style="cyan")
    summary_table.add_column("Valeur", style="white")
    
    summary_table.add_row("✅ Succès", str(success_count))
    summary_table.add_row("❌ Échecs", str(fail_count))
    summary_table.add_row("📝 Posts traités", str(len(posts)))
    
    console.print(summary_table)
    
    if fail_count > 0:
        console.print("\n⚠️  Certaines publications ont échoué. Consultez les logs pour plus de détails.", style="yellow")
    else:
        console.print("\n🎉 Toutes les publications ont réussi!", style="green")
    
    logger.info(f"Terminé - Succès: {success_count}, Échecs: {fail_count}")


if __name__ == '__main__':
    main()
