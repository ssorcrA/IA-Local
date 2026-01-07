# 🛡️ AD Log Monitor Pro v3.0

## Système de surveillance multi-sources avec analyse IA locale

Moniteur intelligent de logs Windows (ForwardedEvents) et Syslog avec analyse automatique par IA locale (Ollama) et création de tickets structurés.

---

## 🎯 Fonctionnalités principales

### ✨ Sources de logs multiples
- **ForwardedEvents (EVTX)** : Événements Windows centralisés
- **Syslog** : Logs d'équipements réseau (Stormshield, Switch, WiFi)
- **Archives Syslog** : Historique des logs réseau
- **Logs locaux** : Fichiers .log personnalisés

### 🤖 Analyse IA avancée
- **Ollama local** (prioritaire) : Analyse rapide et privée sur votre serveur
- **Fallback API** : Claude, OpenAI, Groq si Ollama indisponible
- **Interface web Ollama** : Intégration directe à localhost:3000 ou 192.168.10.110:3000

### 🎨 Interface moderne
- **Mode clair/sombre** : Basculement instantané
- **Console en temps réel** : Logs colorés et structurés
- **Base de données** : Historique complet des incidents
- **Détails enrichis** : Rapports d'incidents complets avec solutions

### 📊 Organisation intelligente
- **Catégorisation automatique** : Par type d'appareil
- **Priorisation 1-10** : Des incidents critiques aux infos
- **Regroupement** : Évite les doublons, regroupe les incidents similaires
- **Filtrage avancé** : Mots-clés, Event IDs critiques

---

## 📁 Structure du projet

```
C:\IA\
├── Code\
│   ├── main.py                    # Interface graphique principale
│   ├── config.py                  # Configuration complète ⭐ NOUVEAU
│   ├── enhanced_ai_analyzer.py    # Analyseur IA avec Ollama ⭐ NOUVEAU
│   ├── unified_log_reader.py      # Lecteur multi-sources
│   ├── event_reader.py            # Lecteur ForwardedEvents
│   ├── syslog_reader.py           # Lecteur Syslog
│   ├── event_filter.py            # Filtre intelligent
│   ├── ticket_manager.py          # Gestionnaire de tickets
│   ├── web_searcher.py            # Recherche web de solutions
│   ├── ai_analyzer.py             # (ancien, remplacé par enhanced)
│   ├── theme_manager.py           # Gestionnaire de thèmes
│   └── launcher.pyw               # Lanceur silencieux
│
├── JournalTransfert\
│   └── ForwardedEvents.evtx       # Logs Windows centralisés
│
├── Tickets\                        # Tickets générés (par catégorie)
│   ├── Serveur AD\
│   ├── Stormshield\
│   ├── Switch\
│   └── ...
│
├── Logs\                           # Logs locaux optionnels
│
└── historique.json                 # État de surveillance
```

---

## 🚀 Installation

### Prérequis

1. **Python 3.8+**
2. **Ollama** installé et démarré (recommandé)
3. **Bibliothèques Python** :

```bash
pip install pywin32 requests beautifulsoup4
```

### Configuration Ollama

1. **Installer Ollama** :
   - Télécharger depuis https://ollama.ai
   - Installer sur votre serveur IA

2. **Télécharger un modèle** :
```bash
ollama pull llama3.2
# ou
ollama pull mistral
```

3. **Démarrer Ollama** :
```bash
ollama serve
```

4. **Vérifier l'accès** :
   - API : http://localhost:11434
   - Interface : http://localhost:3000 (si installée)

### Configuration réseau (optionnel)

Si Ollama est sur un autre serveur (192.168.10.110) :

1. Modifier `config.py` :
```python
OLLAMA_API_URL_ALT = "http://192.168.10.110:11434"
OLLAMA_WEB_URL_ALT = "http://192.168.10.110:3000"
```

2. S'assurer que le port 11434 est ouvert dans le pare-feu

---

## ⚙️ Configuration

### Fichier `config.py`

Tous les paramètres sont centralisés dans `config.py` :

#### Chemins principaux
```python
LOG_FILE = r"C:\IA\JournalTransfert\ForwardedEvents.evtx"
OUTPUT_DIR = r"C:\IA\Tickets"
SYSLOG_PATH = r"\\SRV-SYSLOG\surveillence$\syslog"
```

#### Ollama
```python
OLLAMA_API_URL = "http://localhost:11434"
OLLAMA_WEB_URL = "http://localhost:3000"
OLLAMA_MODEL = "llama3.2"  # Modèle à utiliser
AI_TIMEOUT = 90  # Timeout en secondes
```

#### Surveillance
```python
POLLING_INTERVAL = 60  # Vérification toutes les 60s
INITIAL_CHECK_HOURS = 24  # Analyse des 24 dernières heures
MIN_PRIORITY_THRESHOLD = 4  # Seuil de priorité minimum
```

#### Appareils surveillés
```python
MONITORED_DEVICES = {
    '192.168.1.254': {'name': 'Stormshield', 'icon': '🔥'},
    '192.168.1.15': {'name': 'Switch', 'icon': '🔌'},
    '192.168.1.11': {'name': 'Borne WiFi', 'icon': '📡'}
}
```

---

## 🎮 Utilisation

### Démarrage

#### Mode normal (avec console)
```bash
cd C:\IA\Code
python main.py
```

#### Mode silencieux (sans console)
```bash
pythonw launcher.pyw
```

### Interface

#### 1. Console
- **Surveillance en temps réel** des événements
- **Logs colorés** : 
  - 🔴 Erreurs
  - 🟡 Avertissements
  - 🟢 Succès
  - 🔵 Informations

#### 2. Base de données
- **Liste tous les tickets** créés
- **Recherche** : Filtrer par mot-clé, Event ID, ordinateur...
- **Double-clic** : Ouvrir le rapport détaillé

#### 3. Détails
- **Rapport complet** de l'incident sélectionné
- **Analyse IA** avec solutions
- **Liens web** vers ressources

### Boutons de contrôle

| Bouton | Action |
|--------|--------|
| ▶ Surveillance | Lance la surveillance continue |
| ⏸ Arrêter | Arrête la surveillance |
| 🔄 Actualiser | Recharge la base de données |
| 📅 Analyse 24h | Analyse les 24 dernières heures |
| ⏹ Arrêter vérif. | Stoppe l'analyse en cours |
| 🗑 Nettoyer | Supprime les tickets > 30 jours |
| 🌙/☀️ Thème | Bascule mode clair/sombre |

---

## 🔍 Système de priorités

### Niveaux de priorité (1-10)

| Niveau | Couleur | Signification | Action |
|--------|---------|---------------|--------|
| 10 | 🔴 | Critique absolu | **IMMÉDIAT** - Bloquer l'accès, alerter |
| 9 | 🔴 | Très haute | **URGENT** - Investiguer rapidement |
| 8 | 🟠 | Haute | **RAPIDE** - Analyser et corriger |
| 7 | 🟠 | Moyenne-haute | **PLANIFIER** - Intervention nécessaire |
| 6 | 🟡 | Moyenne | **SURVEILLER** - Vérifier évolution |
| 5 | 🟡 | Basse-moyenne | **NOTER** - Corriger si temps |
| 4 | 🟢 | Basse | **MONITORER** - Information |
| 3 | 🟢 | Très basse | **RÉFÉRENCE** - Archiver |
| 2 | 🔵 | Info | **IGNORE** - Info seulement |
| 1 | ⚪ | Minimal | **IGNORE** - Très peu important |

### Event IDs critiques

#### Niveau 10 (Critique absolu)
- **1102** : Journal d'audit effacé ⚠️
- **4719** : Modification politique d'audit
- **4794** : Mode restauration AD

#### Niveau 9 (Très haute)
- **7045** : Nouveau service installé
- **4697** : Service installé système
- **4765** : Historique SID ajouté

#### Niveau 8 (Haute)
- **4625** : Échec authentification
- **1001** : Crash système (BSOD)
- **4724** : Réinitialisation mot de passe

---

## 🤖 Analyse IA

### Priorité des providers

1. **Ollama local** (prioritaire)
   - Plus rapide (local)
   - Privé (pas de données envoyées)
   - Gratuit
   - Nécessite serveur local

2. **Groq** (fallback 1)
   - Très rapide
   - Gratuit (limité)
   - Nécessite clé API

3. **Claude** (fallback 2)
   - Très précis
   - Payant
   - Nécessite clé API

4. **OpenAI** (fallback 3)
   - Précis
   - Payant
   - Nécessite clé API

### Structure de l'analyse

Chaque ticket contient :

```
🔍 DIAGNOSTIC
   └─ Explication claire du problème

🎯 CAUSES PROBABLES
   └─ 2-3 causes possibles

⚡ SOLUTION IMMÉDIATE
   └─ Actions à faire maintenant

🛠️ RÉSOLUTION COMPLÈTE
   └─ Procédure détaillée pas à pas

🔒 PRÉVENTION
   └─ Mesures pour éviter la récurrence
```

---

## 📊 Catégories d'appareils

Les tickets sont automatiquement classés par catégorie :

| Catégorie | Icône | Boost priorité | Mots-clés |
|-----------|-------|----------------|-----------|
| Serveur AD | 🖥️ | +2 | DC, LDAP, Kerberos, DNS |
| Stormshield | 🔥 | +3 | 192.168.1.254, firewall, utm |
| Switch | 🔌 | +1 | 192.168.1.15, vlan, port |
| Borne WiFi | 📡 | +1 | 192.168.1.11, SSID, wireless |
| Serveur IA | 🤖 | +1 | Ollama, GPU, AI |
| Serveurs | 💻 | +1 | Server, SRV- |
| Autres | ❓ | +0 | (défaut) |

---

## 🔧 Dépannage

### Ollama ne se connecte pas

1. **Vérifier qu'Ollama est démarré** :
```bash
# Windows
tasklist | findstr ollama

# Linux
ps aux | grep ollama
```

2. **Tester manuellement** :
```bash
curl http://localhost:11434/api/tags
```

3. **Vérifier le pare-feu** :
   - Port 11434 doit être ouvert

4. **Logs Ollama** :
   - Chercher les erreurs dans les logs d'Ollama

### Aucun événement détecté

1. **ForwardedEvents** :
   - Vérifier que le fichier EVTX existe
   - Vérifier les permissions de lecture

2. **Syslog** :
   - Vérifier l'accès au partage réseau
   - Tester : `dir \\SRV-SYSLOG\surveillence$\syslog`

3. **Filtrage** :
   - Abaisser `MIN_PRIORITY_THRESHOLD` dans `config.py`
   - Désactiver temporairement le filtrage dans `event_filter.py`

### Tickets non créés

1. **Vérifier les permissions** :
```bash
icacls C:\IA\Tickets
```

2. **Vérifier l'espace disque** :
```bash
dir C:\IA\Tickets
```

3. **Consulter les logs** dans la console

---

## 📝 Automatisation

### Démarrage automatique

#### Tâche planifiée Windows

1. Ouvrir **Planificateur de tâches**
2. **Créer une tâche** :
   - Nom : `AD Log Monitor`
   - Déclencheur : **Au démarrage**
   - Action : `C:\Python\pythonw.exe C:\IA\Code\launcher.pyw`
   - Exécuter avec : **Compte système** ou votre compte admin

#### Service Windows

Utiliser **NSSM** (Non-Sucking Service Manager) :

```bash
nssm install ADLogMonitor "C:\Python\pythonw.exe" "C:\IA\Code\main.py"
nssm start ADLogMonitor
```

---

## 🔐 Sécurité

### Bonnes pratiques

1. **Clés API** :
   - Stocker dans variables d'environnement
   - Ne jamais commiter dans Git

2. **Permissions** :
   - Lecture seule sur ForwardedEvents
   - Écriture restreinte sur C:\IA\Tickets

3. **Réseau** :
   - Utiliser HTTPS pour Ollama si distant
   - VPN pour accès Syslog

4. **Logs** :
   - Archiver régulièrement les tickets
   - Chiffrer les logs sensibles

---

## 📈 Performances

### Optimisations

1. **Ollama local** :
   - Utiliser un serveur dédié avec GPU
   - Modèle llama3.2 (rapide) ou mistral (équilibré)

2. **Filtrage** :
   - Ajuster `MIN_PRIORITY_THRESHOLD`
   - Affiner les mots-clés dans `CRITICAL_KEYWORDS`

3. **Polling** :
   - Augmenter `POLLING_INTERVAL` si faible activité
   - Diminuer pour surveillance intensive

### Ressources recommandées

- **CPU** : 4 cœurs minimum
- **RAM** : 8 Go (16 Go avec Ollama)
- **GPU** : NVIDIA recommandé pour Ollama
- **Disque** : SSD pour rapidité

---

## 🆘 Support

### Logs de diagnostic

Activer le mode debug dans `config.py` :
```python
DEBUG_MODE = True
```

### Fichiers importants

- `C:\IA\historique.json` : État de surveillance
- `C:\IA\Tickets\.ticket_index.json` : Index des tickets
- Console : Logs en temps réel

### Contact

Pour toute question ou problème, consultez :
- La documentation Ollama : https://ollama.ai/docs
- Les forums Microsoft TechNet
- La documentation pywin32

---

## 📄 Licence

Ce projet est fourni tel quel, sans garantie. Utilisez-le à vos propres risques.

---

## 🎉 Changelog

### v3.0 (2025-01-07)
- ✨ Intégration Ollama local prioritaire
- ✨ Interface graphique Ollama intégrée
- ✨ Configuration centralisée dans config.py
- ✨ Enhanced AI Analyzer avec cascade intelligente
- ✨ Support multi-URL Ollama (localhost + 192.168.10.110)
- 🔧 Amélioration de la détection Syslog
- 🔧 Optimisation du filtrage d'événements
- 🎨 Amélioration du thème sombre

### v2.0
- ✨ Support multi-sources (EVTX + Syslog + Archives)
- ✨ Mode clair/sombre
- ✨ Catégorisation automatique par appareil
- 🔧 Priorisation 1-10 améliorée

### v1.0
- 🎉 Version initiale avec ForwardedEvents uniquement
