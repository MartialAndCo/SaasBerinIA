# Guide de démarrage rapide

*Dernière mise à jour: 8 mai 2025*

## Sommaire
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Première utilisation](#première-utilisation)
- [Commandes courantes](#commandes-courantes)
- [Prochaines étapes](#prochaines-étapes)

## Prérequis

Pour utiliser BerinIA, vous aurez besoin de :

- Python 3.8 ou supérieur
- Une clé API OpenAI (pour GPT-4.1, GPT-4.1-mini et GPT-4.1-nano)
- Optionnel: Comptes Mailgun et Twilio pour les fonctionnalités d'envoi d'emails et SMS

## Installation

1. Clonez le dépôt :
   ```bash
   git clone https://github.com/berinai/berinia.git
   cd berinia/infra-ia
   ```

2. Créez et activez un environnement virtuel Python :
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Pour Linux/Mac
   # OU
   .venv\Scripts\activate  # Pour Windows
   ```

3. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

4. Créez un fichier `.env` avec vos clés API :
   ```
   OPENAI_API_KEY=sk-...
   
   # Optionnel - Qdrant pour la mémoire vectorielle
   QDRANT_URL=http://localhost:6333
   
   # Optionnel - Mailgun pour les emails
   MAILGUN_API_KEY=...
   MAILGUN_DOMAIN=...
   
   # Optionnel - Twilio pour les SMS
   TWILIO_SID=...
   TWILIO_TOKEN=...
   TWILIO_PHONE=+33...
   ```

5. Vérifiez votre installation :
   ```bash
   python verify_installation.py
   # Pour une vérification complète (test de l'API OpenAI) :
   python verify_installation.py --full
   ```

## Première utilisation

1. Démarrez l'interface interactive :
   ```bash
   python interact.py
   ```

2. Interagissez avec le système en langage naturel :
   ```
   >>> Explore la niche des consultants en cybersécurité
   ```

3. Pour lancer le serveur de webhooks (réception des réponses) :
   ```bash
   python webhook/run_webhook.py
   ```

## Commandes courantes

Voici quelques exemples de commandes que vous pouvez utiliser dans l'interface interactive :

- **Explorer une niche** : `Explore la niche des consultants en cybersécurité`
- **Récupérer des leads** : `Récupère 50 leads dans cette niche`
- **Préparer une campagne** : `Prépare une campagne d'emails avec comme sujet "Sécurisez votre entreprise"`
- **Envoyer une campagne** : `Envoie cette campagne aux 20 meilleurs leads`
- **Planifier une relance** : `Planifie une relance dans 3 jours`
- **Voir les statistiques** : `Montre-moi les statistiques de la dernière campagne`

## Prochaines étapes

Une fois familiarisé avec les bases, vous pouvez explorer :

- [Installation complète](installation.md) pour une configuration plus détaillée
- [Architecture système](../architecture/overview.md) pour comprendre les composants
- [Intégration WhatsApp](../integrations/whatsapp.md) pour envoyer/recevoir des messages via WhatsApp
- [Intégration SMS](../integrations/sms-twilio.md) pour la gestion des SMS

---

[Retour à l'accueil](../index.md) | [Installation détaillée →](installation.md)
