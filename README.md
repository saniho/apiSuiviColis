# My Suivi Colis

Intégration Home Assistant pour le suivi de colis en temps réel avec carte interactive.

## Objectif

My Suivi Colis permet de suivre vos colis depuis Home Assistant en utilisant :
- Les **API publiques gratuites** des transporteurs (La Poste, Colissimo, Chronopost)
- Le **scraping des pages de tracking** (Mondial Relay)
- Une **carte interactive** pour visualiser la position de vos colis
- Des **notifications** lors des changements de statut

## Avertissement

Cette intégration est fournie **"telle quelle"**, sans garantie de bon fonctionnement. Les mécanismes de scraping HTML utilisés pour certains transporteurs peuvent cesser de fonctionner à tout moment si les sites web des transporteurs changent.

**Le développeur décline toute responsabilité** en cas de :
- Dysfonctionnement lié à des changements d'API ou de sites web des transporteurs
- Blocage par les transporteurs (rate limiting, blocage IP)
- Utilisation abusive ou non conforme aux CGU des transporteurs
- Perte de données ou indisponibilité du service

Cette intégration est un projet communautaire open source, sans affiliation avec Home Assistant, HACS ou les transporteurs supportés.

## Fonctionnalités

- Suivi de colis multi-transporteurs
- Carte interactive Leaflet avec position des colis (géocodage automatique des villes)
- Liste des colis avec statut, transporteur et localisation
- Mise à jour automatique via DataUpdateCoordinator
- Notifications lors des changements de statut (événement `my_suivi_colis_status_changed`)
- Ajout/suppression de colis depuis la carte Lovelace ou les services
- Persistance des données via Store HA
- Code postal optionnel pour les transporteurs qui en ont besoin (Mondial Relay)

## Transporteurs supportés

| Transporteur | Méthode | Statut |
|---|---|---|
| La Poste | API publique | ✅ Natif |
| Colissimo | API publique | ✅ Natif |
| Chronopost | API publique | ✅ Natif |
| Mondial Relay | Scraping HTML | ✅ (code postal requis) |
| DHL | Générique | ⚠️ Clé API externe |
| FedEx | Générique | ⚠️ Clé API externe |
| UPS | Générique | ⚠️ Clé API externe |
| TNT | Générique | ⚠️ Clé API externe |
| GLS | Générique | ⚠️ Clé API externe |
| Amazon Logistics | Générique | ⚠️ Clé API externe |
| DPD | Générique | ⚠️ Clé API externe |
| Relais Colis | Générique | ⚠️ Clé API externe |

## Installation

### Via HACS

1. Ajoutez ce dépôt à HACS comme dépôt personnalisé (catégorie: Intégration)
2. Recherchez "My Suivi Colis" dans HACS
3. Installez l'intégration
4. Redémarrez Home Assistant

### Via Samba/SCP

Copiez le dossier `custom_components/my_suivi_colis` dans votre dossier `custom_components` de Home Assistant.

## Configuration

1. Allez dans Paramètres > Intégrations > Ajouter une intégration > My Suivi Colis
2. Configurez l'intervalle de mise à jour (défaut: 30 min)
3. Depuis l'écran d'intégration, cliquez sur "Configurer" pour :
   - Modifier l'intervalle
   - Ajouter un colis (numéro + transporteur + code postal optionnel)
   - Supprimer un colis

## Services disponibles

| Service | Description |
|---|---|
| `my_suivi_colis.add_tracking` | Ajouter un colis (tracking_number, carrier, name, postal_code) |
| `my_suivi_colis.remove_tracking` | Supprimer un colis (tracking_number) |
| `my_suivi_colis.refresh` | Forcer l'actualisation |

## Carte Lovelace

Ajoutez la carte à votre tableau de bord :

```yaml
type: custom:my-suivi-colis-card
title: Mes colis
default_view: both
```

La carte permet d'ajouter et supprimer des colis directement depuis le tableau de bord.

### Modes d'affichage
- **Carte** : visualisation géographique des colis (géocodage automatique via Nominatim/OSM)
- **Liste** : vue liste avec statut, transporteur et localisation
- **Les deux** : carte + liste simultanément

Cliquez sur un colis dans la liste pour centrer la carte sur sa position.

## Automatisations

Exemple de notification lors d'un changement de statut :

```yaml
automation:
  - alias: "Notification livraison colis"
    trigger:
      platform: event
      event_type: my_suivi_colis_status_changed
    action:
      service: notify.mobile_app_phone
      data:
        title: "{{ trigger.event.data.status_friendly }}"
        message: "Colis {{ trigger.event.data.tracking_number }}"
```

## Développement

### Structure du projet

```
custom_components/my_suivi_colis/
├── __init__.py          # Setup, services, Store
├── manifest.json        # Configuration du composant
├── const.py             # Constantes, transporteurs, statuts
├── config_flow.py       # UI Configuration
├── coordinator.py       # DataUpdateCoordinator
├── helpers.py           # Trackers avec géocodage
├── sensor.py            # Entités capteurs
├── services.yaml        # Définition des services
├── translations/        # Traductions EN/FR
└── www/
    └── my-suivi-colis-card.js  # Carte Lovelace
```

## Licence

Projet open source distribué sous licence MIT.
