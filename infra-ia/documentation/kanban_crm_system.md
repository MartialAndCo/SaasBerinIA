# Système CRM Kanban - BerinIA

## Vue d'ensemble

Le système CRM Kanban de BerinIA permet le suivi et la gestion des leads à travers un tableau kanban inspiré de Flowlu. Les leads sont organisés par statut et peuvent être déplacés par drag & drop entre les différentes étapes du processus commercial.

## 🎯 Fonctionnalités

### Tableau Kanban
- **7 colonnes de statut** : Nouveau, Qualification, Présentation, Négociation, Évaluation, Gagné, Perdu
- **Drag & Drop** : Déplacement des leads entre colonnes avec mise à jour immédiate en base
- **Cartes détaillées** : Affichage des informations essentielles de chaque lead
- **Compteurs en temps réel** : Nombre de leads par statut

### Filtres et Recherche
- **Recherche textuelle** : Par nom, email, entreprise
- **Filtre par campagne** : Affichage des leads d'une campagne spécifique
- **Débounce intelligent** : Recherche optimisée sans surcharge serveur

### Actions sur les Leads
- **Édition** : Modification des informations du lead
- **Suppression** : Suppression avec confirmation
- **Notes** : Ajout de notes lors du changement de statut
- **Export** : Export CSV avec filtres

## 🏗️ Architecture

### Backend (FastAPI)
```
backend/app/api/endpoints/leads.py
├── GET /api/leads/kanban          # Leads groupés par statut
├── PATCH /api/leads/{id}/status   # Mise à jour statut
├── GET /api/leads/stats           # Statistiques
├── GET /api/leads                 # Liste avec filtres
└── GET /api/leads/export          # Export CSV
```

### Frontend (Next.js)
```
frontend/app/dashboard/crm/
├── page.tsx                       # Page principale
├── components/
│   ├── KanbanBoard.tsx           # Tableau avec drag & drop
│   ├── KanbanColumn.tsx          # Colonnes de statut
│   ├── LeadCard.tsx              # Cartes individuelles
│   └── KanbanFilters.tsx         # Filtres et recherche
└── services/api/
    └── kanban-service.ts         # Service API dédié
```

## 🔧 Technologies

- **Drag & Drop** : @dnd-kit/core, @dnd-kit/sortable
- **Backend** : FastAPI + SQLAlchemy + PostgreSQL
- **Frontend** : Next.js + TypeScript + Tailwind CSS
- **État** : React Hooks + API synchronisée
- **Notifications** : Sonner pour les retours utilisateur

## 📊 Statuts des Leads

| Statut        | Description                               | Couleur    |
|---------------|-------------------------------------------|------------|
| new          | Nouveau lead non contacté                 | Gris       |
| qualification| Lead en cours de qualification           | Bleu       |
| presentation | Présentation en cours                     | Jaune      |
| negotiation  | Négociation commerciale                   | Orange     |
| evaluation   | Évaluation finale                         | Violet     |
| won          | Lead converti (gagné)                     | Vert       |
| lost         | Lead perdu                                | Rouge      |

## 🚀 Utilisation

### Accès
Naviguer vers `/admin/crm` dans l'interface BerinIA (accessible depuis la sidebar admin).

### Déplacer un Lead
1. Cliquer et maintenir sur une carte de lead
2. Glisser vers la colonne de destination
3. Relâcher pour valider le changement
4. Le statut est mis à jour automatiquement en base

### Filtrer les Leads
1. Utiliser la barre de recherche pour filtrer par texte
2. Sélectionner une campagne dans le filtre dédié
3. Les résultats se mettent à jour en temps réel

### Actions Disponibles
- **Éditer** : Icône crayon sur chaque carte
- **Supprimer** : Icône poubelle sur chaque carte
- **Exporter** : Bouton d'export dans les filtres

## 🔍 Tests

Exécuter les tests du système :

```bash
cd /root/berinia/infra-ia
python tests/test_kanban_api.py
```

Tests inclus :
- ✅ Connexion API
- ✅ Endpoint kanban
- ✅ Endpoint statistiques
- ✅ Mise à jour de statut
- ✅ Filtres et pagination

## 📈 Intégration

Le système kanban s'intègre parfaitement avec l'écosystème BerinIA :

- **Agents** : Les agents peuvent mettre à jour les statuts automatiquement
- **Campagnes** : Filtrage par campagne dans le kanban
- **Analyse visuelle** : Affichage des scores visuels dans les cartes
- **Messages** : Historique des interactions visible
- **Base de données** : Synchronisation complète avec PostgreSQL

## 🔒 Sécurité

- **Validation** : Validation des statuts côté backend
- **Authentification** : Utilisation du système d'auth existant
- **Permissions** : Respect des permissions utilisateur
- **Logs** : Traçabilité des modifications de statut

## 🎨 Interface

L'interface respecte le design system de BerinIA :
- **Responsive** : Adaptée aux différentes tailles d'écran
- **Accessibilité** : Navigation clavier et lecteurs d'écran
- **Performance** : Optimisée pour de gros volumes de leads
- **UX cohérente** : Intégrée dans le dashboard existant

## ⚡ Performance

- **Optimisation API** : Requêtes groupées et pagination
- **État local** : Mise à jour optimiste pour la fluidité
- **Débounce** : Recherche intelligente sans spam serveur
- **Lazy loading** : Chargement à la demande des données lourdes

## 🛠️ Maintenance

### Ajout d'un Nouveau Statut
1. Modifier `KANBAN_STATUSES` dans `kanban-service.ts`
2. Ajouter la validation dans `leads.py`
3. Mettre à jour les tests

### Personnalisation des Couleurs
Modifier les classes CSS dans `KANBAN_STATUSES` configuration.

### Ajout de Filtres
Étendre `KanbanFilters` interface et composant correspondant.
