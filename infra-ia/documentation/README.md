# 📚 Documentation de BerinIA

Bienvenue dans la documentation du système BerinIA, un écosystème d'agents IA autonomes et collaboratifs pour l'automatisation de la prospection commerciale.

## 🗂️ Structure de la documentation

La documentation est organisée en sections thématiques pour faciliter la navigation :

### 📊 Vue d'ensemble du système
- [Synthèse complète du système BerinIA](./résumé/synthèse_système_BerinIA.md) - Vue globale du système et de ses composants

### 🏗️ Architecture
- [Architecture du système](./architecture/ARCHITECTURE.md) - Documentation technique détaillée
- [Vue d'ensemble](./architecture/overview.md) - Aperçu simplifié
- [Système d'agents](./architecture/agents-system.md) - Architecture des agents IA
- [Communication](./architecture/communication.md) - Flux de communication entre composants

### 🔌 Intégrations
- [Base de données](./integrations/database.md) - Connexion et structure de la base de données
- [Twilio (SMS)](./integrations/sms-twilio.md) - Intégration des SMS via Twilio
- [WhatsApp](./integrations/whatsapp.md) - Intégration de WhatsApp
- [Instantly.ai](./integrations/instantly.md) - Intégration pour l'envoi d'emails

### ⚙️ Services et déploiement
- [Services Systemd](./services/systemd_services.md) - Gestion des services système
- [API](./api.md) - Documentation de l'API BerinIA
- [Variables d'environnement](./services/env_variables_api.md) - Gestion des variables d'environnement

### 📘 Guides
- [Guide d'utilisation API pour l'IA](./api_usage_guide_for_ai.md) - Guide pour l'utilisation de l'API par l'IA

## 🚀 Installation et démarrage

Pour installer et démarrer le système BerinIA, veuillez consulter :

1. [Vue d'ensemble](./architecture/overview.md) - Pour comprendre l'architecture
2. [Services Systemd](./services/systemd_services.md) - Pour le déploiement des services

## 🔄 Utilisation quotidienne

Pour l'utilisation quotidienne du système :

1. Démarrez les services dans l'ordre recommandé (voir [Services Systemd](./services/systemd_services.md))
2. Utilisez l'interface en langage naturel (`python interact.py`)
3. Consultez les logs via l'API ou directement avec journalctl

## 📋 Administration système

Pour les tâches d'administration :

1. Utilisez les endpoints API pour gérer les services (`/api/services/`)
2. Configurez les intégrations externes via les endpoints dédiés
3. Vérifiez régulièrement les logs pour détecter d'éventuels problèmes

## 🔧 Dépannage

En cas de problème :

1. Vérifiez les logs des services concernés
2. Assurez-vous que toutes les dépendances sont actives
3. Vérifiez la connectivité à la base de données
4. Consultez l'état des services systemd

## 👨‍💻 Développement et extension

Pour le développement et l'extension du système :

1. Consultez l'architecture des agents pour comprendre le fonctionnement interne
2. Suivez le modèle existant pour créer de nouveaux agents
3. Utilisez les outils de test inclus pour valider vos modifications

## 📅 Historique des mises à jour

- **Mai 2025** : Ajout de l'intégration Instantly.ai et des services systemd
- **Avril 2025** : Amélioration de l'analyse visuelle et de la classification de niches
- **Mars 2025** : Intégration WhatsApp et système de logs unifié
- **Février 2025** : Version initiale

## 📞 Support

Pour obtenir de l'aide ou signaler des problèmes, contactez l'équipe technique via le groupe WhatsApp dédié.
