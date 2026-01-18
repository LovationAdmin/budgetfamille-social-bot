#!/usr/bin/env python3
"""
Budget Famille - Test Script
=============================
Teste que l'installation est correcte.

Usage:
    python test_install.py
"""

import sys
from pathlib import Path


def test_imports():
    """Teste les imports nécessaires."""
    print("📦 Test des imports...")
    
    errors = []
    
    modules = [
        ('playwright.sync_api', 'playwright'),
        ('dotenv', 'python-dotenv'),
        ('click', 'click'),
        ('rich', 'rich'),
        ('PIL', 'Pillow'),
    ]
    
    for module, package in modules:
        try:
            __import__(module)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - pip install {package}")
            errors.append(package)
    
    return len(errors) == 0


def test_project_structure():
    """Teste la structure du projet."""
    print("\n📁 Test de la structure...")
    
    required_files = [
        'main.py',
        'setup.py',
        'requirements.txt',
        '.env.example',
        '.gitignore',
        'README.md',
        'platforms/__init__.py',
        'platforms/base.py',
        'platforms/linkedin.py',
        'platforms/instagram.py',
        'platforms/facebook.py',
        'platforms/twitter.py',
        'utils/__init__.py',
        'utils/logger.py',
        'utils/helpers.py',
    ]
    
    all_found = True
    
    for file in required_files:
        path = Path(file)
        if path.exists():
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} manquant")
            all_found = False
    
    return all_found


def test_env_config():
    """Teste la configuration .env."""
    print("\n⚙️  Test de la configuration...")
    
    env_file = Path('.env')
    
    if not env_file.exists():
        print("   ⚠️  Fichier .env non trouvé")
        print("   💡 Exécutez: cp .env.example .env")
        return False
    
    print("   ✅ Fichier .env trouvé")
    
    # Charger et vérifier les variables
    try:
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        
        required_vars = [
            'LINKEDIN_EMAIL',
            'LINKEDIN_PASS',
            'INSTAGRAM_USER',
            'INSTAGRAM_PASS',
            'FACEBOOK_EMAIL',
            'FACEBOOK_PASS',
            'TWITTER_USER',
            'TWITTER_PASS',
        ]
        
        configured = 0
        for var in required_vars:
            value = os.getenv(var, '')
            if value and not value.startswith('votre-'):
                configured += 1
        
        if configured == 0:
            print("   ⚠️  Aucun identifiant configuré dans .env")
            return False
        elif configured < len(required_vars):
            print(f"   ⚠️  {configured}/{len(required_vars)} plateformes configurées")
        else:
            print(f"   ✅ Toutes les plateformes configurées")
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    return True


def test_playwright():
    """Teste Playwright."""
    print("\n🌐 Test de Playwright...")
    
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            # Tester le lancement rapide
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto('https://www.google.com', timeout=10000)
            title = page.title()
            browser.close()
            
            print(f"   ✅ Navigateur fonctionnel (page: {title[:30]}...)")
            return True
            
    except Exception as e:
        error_msg = str(e)
        if 'Executable doesn\'t exist' in error_msg:
            print("   ❌ Navigateur non installé")
            print("   💡 Exécutez: playwright install chromium")
        else:
            print(f"   ❌ Erreur: {error_msg[:100]}")
        return False


def main():
    """Fonction principale."""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║   🧪 TEST D'INSTALLATION - Budget Famille Social Bot        ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    results = {
        'imports': test_imports(),
        'structure': test_project_structure(),
        'config': test_env_config(),
    }
    
    # Test Playwright (optionnel, peut être lent)
    response = input("\n🌐 Tester Playwright (peut prendre 10s)? (O/n): ").strip().lower()
    if response != 'n':
        results['playwright'] = test_playwright()
    
    # Résumé
    print("\n" + "═" * 60)
    print("📊 RÉSUMÉ")
    print("═" * 60)
    
    all_passed = True
    for test, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {test}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 Tous les tests sont passés!")
        print("   Vous pouvez lancer: python main.py --dry-run")
    else:
        print("\n⚠️  Certains tests ont échoué.")
        print("   Corrigez les problèmes ci-dessus avant de continuer.")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
