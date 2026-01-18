#!/usr/bin/env python3
"""
Budget Famille - Setup Script
==============================
Script d'installation et de configuration initiale.

Usage:
    python setup.py
"""

import os
import sys
import shutil
from pathlib import Path


def print_banner():
    """Affiche la bannière."""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║   🚀 BUDGET FAMILLE - Social Media Bot Setup                ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)


def check_python_version():
    """Vérifie la version de Python."""
    print("📌 Vérification de Python...")
    
    if sys.version_info < (3, 9):
        print(f"❌ Python 3.9+ requis, vous avez {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} détecté")
    return True


def create_directories():
    """Crée les dossiers nécessaires."""
    print("\n📁 Création des dossiers...")
    
    directories = [
        'logs',
        'screenshots',
        'browser_data',
        'posts',
        'templates',
    ]
    
    for dir_name in directories:
        path = Path(dir_name)
        path.mkdir(exist_ok=True)
        print(f"   ✅ {dir_name}/")


def setup_env_file():
    """Configure le fichier .env."""
    print("\n⚙️  Configuration de l'environnement...")
    
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if env_file.exists():
        print("   ℹ️  Le fichier .env existe déjà")
        response = input("   Voulez-vous le remplacer? (o/N): ").strip().lower()
        if response != 'o':
            return
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("   ✅ Fichier .env créé depuis .env.example")
        print("   ⚠️  N'oubliez pas de remplir vos identifiants!")
    else:
        print("   ❌ Fichier .env.example non trouvé")


def install_dependencies():
    """Installe les dépendances Python."""
    print("\n📦 Installation des dépendances...")
    
    try:
        import subprocess
        
        # Installer les packages
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("   ✅ Dépendances Python installées")
        else:
            print(f"   ⚠️  Erreurs pip: {result.stderr}")
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    return True


def install_playwright():
    """Installe les navigateurs Playwright."""
    print("\n🌐 Installation des navigateurs Playwright...")
    
    try:
        import subprocess
        
        result = subprocess.run(
            [sys.executable, '-m', 'playwright', 'install', 'chromium'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("   ✅ Chromium installé")
        else:
            print(f"   ⚠️  Essayez manuellement: playwright install chromium")
            
    except Exception as e:
        print(f"   ⚠️  Installez manuellement: playwright install chromium")


def create_example_post():
    """Crée un post d'exemple."""
    print("\n📝 Création d'un post d'exemple...")
    
    example_dir = Path('posts/exemple-2025-01-20')
    
    if example_dir.exists():
        print("   ℹ️  Le post d'exemple existe déjà")
        return
    
    example_dir.mkdir(parents=True, exist_ok=True)
    
    caption = """🚀 Mon premier post automatisé !

Ceci est un exemple de publication créée avec Budget Famille Social Bot.

#BudgetFamille #Test #Automatisation
"""
    
    with open(example_dir / 'caption.txt', 'w', encoding='utf-8') as f:
        f.write(caption)
    
    print("   ✅ Post d'exemple créé dans posts/exemple-2025-01-20/")


def print_next_steps():
    """Affiche les prochaines étapes."""
    print("""
    ════════════════════════════════════════════════════════════════
    
    🎉 Installation terminée !
    
    Prochaines étapes :
    
    1. Éditez le fichier .env avec vos identifiants :
       nano .env
    
    2. Ajoutez une image dans votre post :
       cp votre-image.jpg posts/exemple-2025-01-20/image.jpg
    
    3. Testez en mode visible (pour voir ce qui se passe) :
       python main.py --visible --dry-run
    
    4. Lancez une vraie publication :
       python main.py --visible
    
    📖 Documentation complète : README.md
    
    ════════════════════════════════════════════════════════════════
    """)


def main():
    """Fonction principale."""
    print_banner()
    
    # Vérifier Python
    if not check_python_version():
        sys.exit(1)
    
    # Créer les dossiers
    create_directories()
    
    # Configurer .env
    setup_env_file()
    
    # Installer les dépendances
    response = input("\n📦 Installer les dépendances Python? (O/n): ").strip().lower()
    if response != 'n':
        if install_dependencies():
            install_playwright()
    
    # Créer un post d'exemple
    create_example_post()
    
    # Afficher les prochaines étapes
    print_next_steps()


if __name__ == '__main__':
    main()
