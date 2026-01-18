# 🚀 Budget Famille - Social Media Bot

Bot d'automatisation de publication sur les réseaux sociaux pour Budget Famille.
**Coût : 0€** - Utilise l'automatisation de navigateur (Playwright).

## 📋 Réseaux supportés

- ✅ LinkedIn
- ✅ Instagram  
- ✅ Facebook
- ✅ X (Twitter)

## 🛠️ Installation

### Prérequis
- Python 3.9+
- Git

### Étapes

```bash
# 1. Cloner le projet
git clone https://github.com/votre-username/budgetfamille-social-bot.git
cd budgetfamille-social-bot

# 2. Créer un environnement virtuel
python -m venv venv

# Sur Windows:
venv\Scripts\activate

# Sur Mac/Linux:
source venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Installer les navigateurs Playwright
playwright install chromium

# 5. Configurer vos identifiants
cp .env.example .env
# Puis éditez .env avec vos identifiants
```

## ⚙️ Configuration

### Fichier .env

Copiez `.env.example` vers `.env` et remplissez vos identifiants :

```env
# LinkedIn
LINKEDIN_EMAIL=votre-email@example.com
LINKEDIN_PASS=votre-mot-de-passe

# Instagram
INSTAGRAM_USER=budgetfamille
INSTAGRAM_PASS=votre-mot-de-passe

# Facebook
FACEBOOK_EMAIL=votre-email@example.com
FACEBOOK_PASS=votre-mot-de-passe

# X (Twitter)
TWITTER_USER=budgetfamille
TWITTER_PASS=votre-mot-de-passe
```

## 📝 Créer un post

### Structure des dossiers

```
posts/
├── 2025-01-20/
│   ├── caption.txt      # Texte du post
│   ├── image.jpg        # Image (optionnel)
│   └── config.json      # Configuration spécifique (optionnel)
└── 2025-01-27/
    ├── caption.txt
    └── video.mp4        # Vidéo (optionnel)
```

### Fichier caption.txt

```
🎉 Nouvelle fonctionnalité sur Budget Famille !

Découvrez notre système de suggestions IA pour économiser sur vos factures d'énergie.

👉 budgetfamille.com

#BudgetFamille #Économies #FinancesPersonnelles #France
```

### Fichier config.json (optionnel)

```json
{
  "platforms": ["linkedin", "instagram", "facebook", "twitter"],
  "schedule": "2025-01-20T10:00:00",
  "hashtags_twitter": "#BudgetFamille #Tech #Finance",
  "hashtags_instagram": "#budgetfamille #économies #famille #budget"
}
```

## 🚀 Utilisation

### Publier tous les posts en attente

```bash
python main.py
```

### Publier sur une plateforme spécifique

```bash
python main.py --platform linkedin
python main.py --platform instagram
python main.py --platform facebook
python main.py --platform twitter
```

### Publier un post spécifique

```bash
python main.py --post 2025-01-20
```

### Mode test (affiche le navigateur)

```bash
python main.py --visible
```

### Mode dry-run (simule sans publier)

```bash
python main.py --dry-run
```

## 📅 Templates de posts

Le dossier `templates/` contient des modèles prêts à l'emploi :

- `nouvelle-fonctionnalite.txt` - Annonce de feature
- `astuce-budget.txt` - Conseil financier
- `temoignage.txt` - Retour utilisateur
- `mise-a-jour.txt` - Changelog
- `promotion.txt` - Offre spéciale

## 🔐 Sécurité

⚠️ **IMPORTANT** :

1. **Ne jamais commiter `.env`** - Il est dans `.gitignore`
2. **Utilisez des mots de passe forts** - Activez 2FA si possible
3. **Exécutez localement** - Pas sur un serveur (risque de ban)
4. **Espacez les publications** - Min 5 min entre chaque réseau
5. **Variez les horaires** - Ne publiez pas à la même heure chaque semaine

## ⏰ Automatisation recommandée

### Workflow hebdomadaire

1. **Dimanche soir** : Préparez vos posts de la semaine dans `posts/`
2. **Lundi matin** : Lancez `python main.py --visible` en prenant votre café
3. **Vérifiez** : Ouvrez chaque réseau pour confirmer les publications

### Avec Task Scheduler (Windows)

```powershell
# Créer une tâche planifiée
schtasks /create /tn "BudgetFamillePost" /tr "python C:\path\to\main.py" /sc weekly /d MON /st 09:00
```

### Avec cron (Mac/Linux)

```bash
# Éditer crontab
crontab -e

# Ajouter (tous les lundis à 9h)
0 9 * * 1 cd /path/to/budgetfamille-social-bot && /path/to/venv/bin/python main.py >> logs/cron.log 2>&1
```

## 🐛 Dépannage

### "Navigateur ne se lance pas"

```bash
playwright install chromium --with-deps
```

### "Connexion échoue"

- Vérifiez vos identifiants dans `.env`
- Désactivez 2FA temporairement ou utilisez un mot de passe d'application
- Essayez en mode `--visible` pour voir ce qui se passe

### "Compte bloqué temporairement"

- Attendez 24-48h avant de réessayer
- Réduisez la fréquence de publication
- Connectez-vous manuellement d'abord

## 📊 Logs

Les logs sont sauvegardés dans `logs/` :

```
logs/
├── 2025-01-20.log        # Log du jour
└── errors.log            # Erreurs uniquement
```

## 🤝 Contribution

1. Fork le projet
2. Créez une branche (`git checkout -b feature/amelioration`)
3. Committez (`git commit -m 'Ajout de feature'`)
4. Push (`git push origin feature/amelioration`)
5. Ouvrez une Pull Request

## 📄 Licence

MIT - Libre d'utilisation pour Budget Famille

---

**Note** : Ce bot est conçu pour un usage personnel et raisonnable. L'abus peut entraîner la suspension de vos comptes sur les réseaux sociaux.
