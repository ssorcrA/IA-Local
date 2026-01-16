🛡️ AD Log Monitor Pro v4.0
Système de surveillance multi-sources avec analyse IA et détection d'intrusion renforcée
Moniteur intelligent de logs Windows (ForwardedEvents) et Syslog avec analyse automatique par IA locale (Ollama), détection agressive des menaces et création de tickets structurés.

🎯 Fonctionnalités principales
✨ Sources de logs multiples

ForwardedEvents (EVTX) : Événements Windows centralisés avec détection en temps réel
Syslog : Logs d'équipements réseau (Stormshield, Switches, WiFi) avec analyse agressive
Logs locaux : Fichiers .log personnalisés

🤖 Analyse IA avancée (SANS TIMEOUT)

Ollama local (prioritaire) : Analyse rapide et privée sans limitation de temps
API de repli : Groq, Claude, OpenAI si Ollama indisponible
Interface web Ollama : Intégration directe à localhost:3000 ou 192.168.10.110:3000
⚡ NOUVEAU v4.0 : Suppression du timeout pour analyses approfondies
🛑 Arrêt immédiat : Interruption propre des analyses IA en cours

🎨 Interface moderne et ergonomique

Mode clair/sombre : Basculement instantané avec sauvegarde des préférences
Console multi-sources : Logs colorés et structurés en temps réel
Console IA dédiée : Journal séparé pour les analyses IA (onglet "🤖 Analyses IA")
Base de données hiérarchique : Organisation par Catégorie > Event_ID > Tickets
Détails enrichis : Rapports d'incidents complets avec solutions actionnables
Affichage du chemin : Visualisation permanente du fichier sélectionné

🚨 Détection d'intrusion AGRESSIVE (v4.0)

15 patterns d'intrusion : Détection garantie des tentatives d'accès non autorisés
Seuil optimisé : Capture des événements importants (priorité ≥ 5)
Boost firewall : +2 points de priorité pour les événements de sécurité
Indicateurs multiples : Authentication failed, access denied, brute force, port scan...
Surveillance 100% silencieuse : Rapports toutes les 60 secondes, logs seulement si menaces détectées

📊 Organisation intelligente

Catégorisation automatique : Par type d'appareil avec boost de priorité
Priorisation 1-10 : Des incidents critiques aux informations
Regroupement intelligent : Évite les doublons (fenêtre de 30 min), regroupe les incidents similaires
Filtrage avancé : Mots-clés, Event IDs critiques, recherche en temps réel
Structure hiérarchique : Catégorie/Event_ID/Tickets pour une navigation intuitive


📁 Structure du projet
C:\IA\
├── Code\
│   ├── main.py                      # Interface graphique principale ⭐ CORRIGÉ
│   ├── config.py                    # Configuration production
│   ├── enhanced_ai_analyzer.py      # Analyseur IA avec arrêt immédiat ⭐ CORRIGÉ
│   ├── unified_log_reader.py        # Lecteur multi-sources silencieux ⭐ CORRIGÉ
│   ├── event_reader.py              # Lecteur ForwardedEvents (gestion fichiers verrouillés) ⭐ CORRIGÉ
│   ├── syslog_reader.py             # Lecteur Syslog avec diagnostics étendus ⭐ CORRIGÉ
│   ├── event_filter.py              # Filtre avec classification Syslog auto ⭐ AMÉLIORÉ
│   ├── ticket_manager.py            # Gestionnaire structure hiérarchique ⭐ CORRIGÉ
│   ├── device_detector.py           # Détecteur centralisé d'appareils ⭐ CORRIGÉ
│   ├── monitoring_thread.py         # Surveillance silencieuse + rapports minute ⭐ CORRIGÉ
│   ├── ticket_tree_view.py          # Vue arborescente Catégorie/Event/Ticket
│   ├── ticket_operations.py         # Opérations sur tickets (export, copie...)
│   ├── console_manager.py           # Gestionnaire des consoles
│   ├── tab_creators.py              # Création des onglets
│   ├── gui_components.py            # Composants interface (StatusBar, Footer...)
│   ├── theme_manager.py             # Gestionnaire de thèmes
│   ├── web_searcher.py              # Recherche web de solutions
│   ├── launcher.pyw                 # Lanceur silencieux
│   │
│   ├── syslog_debug.py              # Outil de diagnostic Syslog ⭐ NOUVEAU
│   ├── syslog_analyzer.py           # Analyseur intelligent avec filtrage avancé ⭐ NOUVEAU
│   └── syslog_diagnostic.py         # Script de diagnostic complet ⭐ NOUVEAU
│
├── JournalTransfert\
│   └── ForwardedEvents.evtx         # Logs Windows centralisés
│
├── Tickets\                          # Tickets générés (hiérarchique)
│   ├── Serveur AD\
│   │   ├── Event_1234\
│   │   │   ├── ticket_2025-01-09_xxx.txt
│   │   │   └── ticket_2025-01-10_xxx.txt
│   │   └── Event_4625\
│   ├── Stormshield\
│   │   ├── Event_7000\
│   │   └── Event_8000\
│   ├── Switch Principal\
│   ├── Borne WiFi\
│   ├── Serveur IA\
│   └── Autres\
│
├── Logs\                             # Logs locaux optionnels
│
└── historique.json                   # État de surveillance

🚀 Installation
Prérequis

Python 3.8+
Ollama installé et démarré (recommandé)
Bibliothèques Python :

bash  pip install pywin32 requests beautifulsoup4
Configuration Ollama

Installer Ollama :

Télécharger depuis https://ollama.ai
Installer sur votre serveur IA


Télécharger un modèle :

bash   ollama pull llama3.2
   # ou
   ollama pull mistral

Démarrer Ollama :

bash   ollama serve

Vérifier l'accès :

API : http://localhost:11434
Interface : http://localhost:3000 (si installé)



Configuration réseau (optionnelle)
Si Ollama est sur un autre serveur (ex: 192.168.10.110) :

Modifier config.py :

python   OLLAMA_API_URL_ALT = "http://192.168.10.110:11434"
   OLLAMA_WEB_URL_ALT = "http://192.168.10.110:3000"

S'assurer que le port 11434 est ouvert dans le pare-feu


⚙️ Configuration
Fichier config.py
Tous les paramètres sont centralisés dans config.py :
Chemins principaux
pythonLOG_FILE = r"C:\IA\JournalTransfert\ForwardedEvents.evtx"
OUTPUT_DIR = r"C:\IA\Tickets"
SYSLOG_PATH = r"\\SRV-SYSLOG\surveillence$\syslog"
Ollama (SANS TIMEOUT v4.0)
pythonOLLAMA_API_URL = "http://localhost:11434"
OLLAMA_WEB_URL = "http://localhost:3000"
OLLAMA_MODEL = "llama3.2:latest"  # Modèle à utiliser
AI_TIMEOUT = 90  # Timeout pour API externes uniquement
MAX_TOKENS = 2000
Surveillance
pythonPOLLING_INTERVAL = 10  # Vérification toutes les 10s (temps réel)
INITIAL_CHECK_HOURS = 24  # Analyse des 24 dernières heures
MIN_PRIORITY_THRESHOLD = 5  # Seuil de priorité minimum
ENABLE_ONLINE_SEVERITY_CHECK = True  # Vérification en ligne
Appareils surveillés (6 équipements)
pythonMONITORED_DEVICES = {
    '192.168.10.254': {'name': 'Stormshield UTM', 'type': 'firewall', 'icon': '🔥', 'priority_boost': 3},
    '192.168.10.10': {'name': 'Active Directory', 'type': 'Server', 'icon': '🖥️', 'priority_boost': 2},
    '192.168.10.110': {'name': 'Serveur-IA', 'type': 'Server', 'icon': '🤖', 'priority_boost': 1},
    '192.168.10.15': {'name': 'Switch Principal', 'type': 'switch', 'icon': '🔌', 'priority_boost': 2},
    '192.168.10.16': {'name': 'Switch Secondaire', 'type': 'switch', 'icon': '🔌', 'priority_boost': 2},
    '192.168.10.11': {'name': 'Borne WiFi', 'type': 'wifi', 'icon': '📡', 'priority_boost': 1}
}

🎮 Utilisation
Démarrage
Mode normal (avec console)
bashcd C:\IA\Code
python main.py
Mode silencieux (sans console)
bashpythonw launcher.pyw
```

### Interface

#### 1. 🖥️ Console multi-sources
- Surveillance en temps réel de TOUS les événements
- Logs colorés :
  - 🔴 Erreurs critiques
  - 🟠 Avertissements
  - 🟢 Succès
  - 🔵 Informations
- Indicateurs de source (ForwardedEvents, Syslog...)

#### 2. 🤖 Analyses IA (NOUVEAU v4.0)
- **Console dédiée** pour les analyses IA (onglet séparé)
- **Requêtes tracées** : Affichage de chaque demande IA
- **Réponses colorées** : Succès (vert), Erreurs (rouge)
- **Performances** : Durée et taille des analyses
- **Arrêt propre** : Interruption immédiate possible

#### 3. 📋 Base de données hiérarchique
Structure à 3 niveaux :
```
📁 Catégorie (ex: Stormshield)
  └─ 🆔 Event ID (ex: Event 7000)
      └─ 📄 Tickets individuels
```

**Fonctionnalités** :
- **Recherche en temps réel** : Filtrage instantané
- **Affichage du chemin** : Visualisation permanente du fichier sélectionné
- **Double-clic** : Ouverture dans l'onglet Détails
- **Clic droit** : Menu contextuel (copier, ouvrir dossier...)

#### 4. 📋 Détails
- **Rapport complet** de l'incident sélectionné
- **Analyse IA** avec solutions pas à pas
- **Liens web** vers ressources
- **Historique** des occurrences
- **Boutons d'action** : Export, Copie

### Boutons de contrôle

| Bouton | Action |
|--------|--------|
| ▶️ **Surveillance** | Lance la surveillance continue (10s) |
| ⏸️ **Arrêter** | Arrête la surveillance |
| 🔄 **Actualiser** | Recharge la base de données (sans analyse) |
| 🔍 **Test 2h** | Analyse rapide des 2 dernières heures ⭐ NOUVEAU |
| 📅 **Analyse 24h** | Analyse complète des 24 dernières heures |
| ⏹️ **Arrêter vérif.** | Stoppe l'analyse en cours (arrêt immédiat) ⭐ AMÉLIORÉ |
| 🗑️ **Nettoyer** | Supprime les tickets > 30 jours |
| 🌙/☀️ **Thème** | Bascule mode clair/sombre |

### ⭐ NOUVEAUTÉS v4.0 - Modes d'opération

1. **▶️ Surveillance continue** (10 secondes)
   - Scan permanent toutes les 10 secondes
   - **100% silencieux** entre les rapports
   - **Rapport toutes les 60 secondes** avec statistiques
   - **Logs immédiats** uniquement si menaces détectées
   - Idéal pour : Production, surveillance 24/7

2. **🔍 Test 2h** (analyse ponctuelle)
   - Scan des 2 dernières heures
   - Rapide et informatif
   - Idéal pour : Tests, vérifications rapides

3. **📅 Analyse 24h** (analyse complète)
   - Scan complet des 24 dernières heures
   - Peut générer beaucoup d'événements
   - Idéal pour : Audit initial, analyse post-incident

---

## 🔍 Système de priorité (v4.0 OPTIMISÉ)

### Niveaux de priorité (1-10)

| Niveau | Couleur | Signification | Action |
|--------|---------|---------------|--------|
| 10 | 🔴 | **Critique absolu** | IMMÉDIAT - Bloquer, alerter équipe sécurité |
| 9 | 🔴 | **Très haute** | URGENT - Enquêter rapidement, documenter |
| 8 | 🟠 | **Haute** | RAPIDE - Analyser et corriger dans l'heure |
| 7 | 🟠 | **Moyenne-haute** | PLANIFIER - Intervention nécessaire aujourd'hui |
| 6 | 🟡 | **Moyenne** | SURVEILLER - Vérifier évolution |
| 5 | 🟡 | **Basse-moyenne** | NOTER - Corriger si temps disponible |
| 4 | 🟢 | **Basse** | MONITORER - Information |
| 3 | 🟢 | **Très basse** | RÉFÉRENCE - Archiver |
| 2 | 🔵 | **Info** | IGNORER - Info seulement |
| 1 | ⚪ | **Minimal** | IGNORER - Très peu important |

### Event IDs critiques

**Niveau 10 (Critique absolu)**
- **1102** : Journal d'audit effacé ⚠️
- **4719** : Modification politique d'audit
- **4794** : Mode restauration AD

**Niveau 9 (Très haute)**
- **7045** : Nouveau service installé
- **4697** : Service installé dans le système
- **4765** : SID historique ajouté

**Niveau 8 (Haute)**
- **4625** : Échec authentification
- **1001** : Plantage système (BSOD)
- **4724** : Réinitialisation mot de passe
- **4728** : Membre ajouté groupe sécurité global
- **4732** : Membre ajouté groupe local

### Mots-clés critiques avec scores

**Niveau 10**
- ransomware, intrusion, breach, compromis, hack, rootkit

**Niveau 9**
- exploit, privilege escalation, élévation de privilèges, backdoor

**Niveau 8**
- attack, attaque, unauthorized, non autorisé, malware, blocked, denied

**Niveau 7**
- trojan, worm, botnet, alert

**Niveau 6**
- virus, vulnerability, vulnérabilité, brute force, injection, critical

---

## 🚨 Détection d'intrusion (v4.0 AGRESSIVE)

### Patterns d'intrusion (15 détections)

| Pattern | Score | Description |
|---------|-------|-------------|
| `authentication.*fail` | 9 | Échec d'authentification |
| `login.*fail` | 9 | Échec de connexion |
| `invalid.*user` | 8 | Utilisateur invalide |
| `invalid.*password` | 8 | Mot de passe invalide |
| `access.*denied` | 8 | Accès refusé |
| `connection.*refused` | 7 | Connexion refusée |
| `unauthorized.*access` | 9 | Accès non autorisé |
| `brute.*force` | 10 | Attaque brute force |
| `port.*scan` | 9 | Scan de ports |
| `(ddos\|dos).*attack` | 10 | Attaque DDoS |
| `intrusion.*detect` | 10 | Intrusion détectée |
| `malware.*detect` | 10 | Malware détecté |
| `blocked.*ip` | 8 | IP bloquée |
| `deny.*rule` | 7 | Règle de refus |
| `drop.*packet` | 7 | Paquet rejeté |

### Boosts de priorité

- **Facility critique** (`firewall`, `asqd`, `security`, `auth`) : +2 points
- **Catégorie appareil** :
  - Stormshield : +3 points
  - Serveur AD : +2 points
  - Switches : +2 points
  - Borne WiFi : +1 point
  - Serveur IA : +1 point

### Gestion des doublons (v4.0)

- **Fenêtre de 30 min** pour événements standards
- **Fenêtre de 20 min** pour haute priorité (≥7)
- **Fenêtre de 10 min** pour événements critiques (≥9)
- **Vérification isolée** : Ne bloque pas les événements suivants

---

## 🤖 Analyse IA (v4.0 SANS TIMEOUT + ARRÊT IMMÉDIAT)

### Priorité des fournisseurs

1. **Ollama local (prioritaire)** ⭐
   - ✅ Plus rapide (local)
   - ✅ Privé (pas de données envoyées)
   - ✅ Gratuit
   - ✅ **SANS TIMEOUT** : Analyses approfondies illimitées
   - ✅ **ARRÊT IMMÉDIAT** : Interruption propre garantie
   - ⚠️ Nécessite serveur local

2. **Groq (repli 1)**
   - Très rapide
   - Gratuit (limité)
   - Timeout: 60s
   - Nécessite clé API

3. **Claude (repli 2)**
   - Très précis
   - Timeout: 60s
   - Payant
   - Nécessite clé API

4. **OpenAI (repli 3)**
   - Précis
   - Timeout: 60s
   - Payant
   - Nécessite clé API

### Structure de l'analyse

Chaque ticket contient :
```
🔍 DIAGNOSTIC
   └─ Explication claire du problème en 2-3 phrases

🎯 CAUSES PROBABLES
   └─ Liste de 2-3 causes possibles avec probabilités

⚡ SOLUTION IMMÉDIATE (< 5 minutes)
   └─ Actions à faire MAINTENANT pour contenir le problème

🛠️ RÉSOLUTION COMPLÈTE (solution durable)
   └─ Procédure détaillée pas à pas avec commandes exactes

🔒 PRÉVENTION
   └─ Mesures pour éviter la récurrence

📊 Catégories d'appareils (6 équipements surveillés)
Les tickets sont automatiquement classés par catégorie :
CatégorieIcônePriorité BoostTypeMots-clésServeur AD🖥️+2Windows192.168.10.10, DC, Active Directory, LDAP, Kerberos, DNSServeur IA🤖+1Windows192.168.10.110, Ollama, IA, Machine Learning, GPUStormshield🔥+3Syslog192.168.10.254, firewall, utm, asqdSwitch Principal🔌+2Syslog192.168.10.15, switch, vlan, portSwitch Secondaire🔌+2Syslog192.168.10.16, switch, vlan, portBorne WiFi📡+1Syslog192.168.10.11, WiFi, SSID, wireless, APAutres❓+0-(par défaut)

🔧 Dépannage
Ollama ne se connecte pas

Vérifier qu'Ollama est démarré :

bash   # Windows
   tasklist | findstr ollama
   
   # Linux
   ps aux | grep ollama

Tester manuellement :

bash   curl http://localhost:11434/api/tags

Vérifier le pare-feu :

Le port 11434 doit être ouvert


Consulter les logs Ollama :

Rechercher les erreurs dans les logs



Aucun événement détecté
ForwardedEvents :

Vérifier que le fichier EVTX existe
Vérifier les permissions de lecture
Si fichier verrouillé (erreur 32) → Mode copie automatique activé

Syslog :

Vérifier l'accès au partage réseau :

bash   dir \\SRV-SYSLOG\surveillence$\syslog

Utiliser syslog_debug.py pour diagnostic :

bash   python syslog_debug.py

Vérifier les IP surveillées dans MONITORED_DEVICES

Filtrage :

Vérifier MIN_PRIORITY_THRESHOLD dans config.py (défaut: 5)
Utiliser 🔍 Test 2h pour vérification rapide

Intrusions non détectées (v4.0)

Lancer le diagnostic Syslog :

bash   python syslog_debug.py
```
   
   Résultat attendu :
```
   🚨 INTRUSIONS POTENTIELLES DÉTECTÉES: X
   
   [1] 🚨 INTRUSION POTENTIELLE #1
   ────────────────────────────────────
   ⏰ Timestamp: Jan 9 14:32:15
   🔍 IP Source: 192.168.10.254
   🏷️ Facility: asqd
   ⚠️ Severity: ERR
   🔑 Mots-clés trouvés: fail, authentication, denied

Tester une ligne spécifique :

bash   python syslog_debug.py --test-line "192.168.10.254 Jan 9 14:32:15 asqd err authentication failed"

Vérifier les patterns dans syslog_reader.py :

15 patterns d'intrusion actifs
Mots-clés étendus (fail, deny, drop, attack...)



Tickets non créés

Vérifier les permissions :

bash   icacls C:\IA\Tickets

Vérifier l'espace disque :

bash   dir C:\IA\Tickets

Consulter les consoles :

Console principale pour les événements
Console IA pour les analyses



Surveillance silencieuse (v4.0)
Comportement normal :

✅ Aucun log pendant 60 secondes
✅ Rapport automatique toutes les minutes
✅ Logs immédiats si menace détectée

Si aucun rapport après 60s :

Vérifier que la surveillance est démarrée (▶️ Surveillance)
Consulter la console pour erreurs éventuelles


📝 Automatisation
Démarrage automatique
Tâche planifiée Windows

Ouvrir Planificateur de tâches
Créer une tâche :

Nom : AD Log Monitor Pro
Déclencheur : Au démarrage
Action : C:\Python\pythonw.exe C:\IA\Code\launcher.pyw
Exécuter avec : Compte système ou compte admin



Service Windows
Utiliser NSSM (Non-Sucking Service Manager) :
bashnssm install ADLogMonitorPro "C:\Python\pythonw.exe" "C:\IA\Code\main.py"
nssm set ADLogMonitorPro AppDirectory "C:\IA\Code"
nssm start ADLogMonitorPro

🔐 Sécurité
Bonnes pratiques

Clés API :

Stocker dans variables d'environnement
Ne jamais commiter dans Git


Permissions :

Lecture seule sur ForwardedEvents
Écriture restreinte sur C:\IA\Tickets


Réseau :

Utiliser HTTPS pour Ollama si distant
VPN pour accéder aux Syslog


Logs :

Archiver régulièrement les tickets
Chiffrer les logs sensibles




📈 Performances
Optimisations

Ollama local :

Utiliser un serveur dédié avec GPU
Modèle llama3.2 (rapide) ou mistral (équilibré)
SANS TIMEOUT : Analyses approfondies garanties


Filtrage :

Ajuster MIN_PRIORITY_THRESHOLD (défaut: 5)
Affiner les mots-clés dans CRITICAL_KEYWORDS
Utiliser les patterns d'intrusion


Polling :

10 secondes : Détection temps réel optimale
Rapports toutes les 60 secondes
Surveillance 100% silencieuse



Ressources recommandées

CPU : 4 cœurs minimum
RAM : 8 Go (16 Go avec Ollama)
GPU : NVIDIA recommandé pour Ollama
Disque : SSD pour rapidité


🆘 Support
Logs de diagnostic
Activer le mode debug dans config.py :
pythonDEBUG_MODE = True
VERBOSE_SYSLOG = True
VERBOSE_EVENTS = True
Fichiers importants

C:\IA\historique.json : État de surveillance
C:\IA\Tickets\.ticket_index.json : Index des tickets
C:\IA\.syslog_state.json : État Syslog
Console principale : Logs en temps réel
Console IA : Analyses IA tracées

Outils de diagnostic (v4.0)

syslog_debug.py : Diagnostic complet Syslog avec détection d'intrusions
syslog_diagnostic.py : Script de diagnostic par étapes
syslog_analyzer.py : Analyseur intelligent avec filtrage avancé

Contact
Pour toute question ou problème, consultez :

Documentation Ollama : https://ollama.ai/docs
Forums Microsoft TechNet
Documentation pywin32


📄 Licence
Ce projet est fourni tel quel, sans garantie. Utilisez-le à vos propres risques.

🎉 Journal des modifications
v4.0 (16/01/2025) 🚀
🔥 NOUVELLES FONCTIONNALITÉS MAJEURES
Surveillance temps réel optimisée

✨ Surveillance 100% silencieuse entre les rapports
✨ Rapport toutes les 60 secondes avec statistiques détaillées
✨ Logs immédiats uniquement si menaces détectées
✨ 3 modes d'opération : Surveillance (10s), Test 2h, Analyse 24h
✨ Détails par appareil dans chaque rapport

Détection d'intrusion agressive

✨ 15 patterns d'intrusion avec détection garantie
✨ Seuil optimisé à priorité ≥ 5
✨ Boost +2 pour événements firewall/sécurité
✨ Statistiques en temps réel (intrusions, haute priorité)
✨ Indicateurs multiples dans les tickets

Analyse IA sans limitation + Arrêt immédiat

✨ Suppression du timeout pour Ollama local
✨ Arrêt immédiat garanti des analyses en cours
✨ Fermeture propre des sessions HTTP
✨ Console IA dédiée avec traçage complet
✨ Analyses approfondies illimitées (Ollama)
✨ Timeout 60s pour API externes (Groq, Claude, OpenAI)

Organisation hiérarchique

✨ Structure à 3 niveaux : Catégorie/Event_ID/Tickets
✨ Navigation intuitive dans la base de données
✨ Affichage permanent du chemin du fichier sélectionné
✨ Vue arborescente avec compt

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
