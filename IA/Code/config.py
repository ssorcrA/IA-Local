"""
Configuration complète du moniteur AD - Version 3.0
Fichier : config.py
"""
import os
from pathlib import Path

# ============================================================================
# INFORMATIONS APPLICATION
# ============================================================================
APP_NAME = "AD Log Monitor Pro"
APP_VERSION = "3.0"

# ============================================================================
# CHEMINS PRINCIPAUX
# ============================================================================
# Fichier EVTX des événements transférés
LOG_FILE = r"C:\IA\JournalTransfert\ForwardedEvents.evtx"

# Dossier de sortie des tickets
OUTPUT_DIR = r"C:\IA\Tickets"

# Fichier d'historique
HISTORY_FILE = r"C:\IA\historique.json"

# ============================================================================
# CHEMINS SYSLOG
# ============================================================================
# Dossier principal Syslog
SYSLOG_PATH = r"\\SRV-SYSLOG\surveillence$\syslog"

# Dossier archives Syslog
SYSLOG_ARCHIVE_PATH = r"\\SRV-SYSLOG\surveillence$\archive"

# Dossier logs locaux
LOCAL_LOGS_PATH = r"C:\IA\Logs"

# ============================================================================
# PARAMÈTRES DE SURVEILLANCE
# ============================================================================
# Intervalle entre chaque vérification (en secondes)
POLLING_INTERVAL = 60

# Nombre d'heures à analyser lors du check initial
INITIAL_CHECK_HOURS = 24

# Nombre de jours avant suppression des vieux tickets
CLEANUP_DAYS = 30

# Nombre maximum d'événements à traiter par cycle
MAX_EVENTS_PER_CYCLE = 100

# ============================================================================
# CONFIGURATION IA - OLLAMA
# ============================================================================
# URL de l'interface Ollama
OLLAMA_WEB_URL = "http://localhost:3000"
OLLAMA_WEB_URL_ALT = "http://192.168.10.110:3000"

# URL de l'API Ollama
OLLAMA_API_URL = "http://localhost:11434"
OLLAMA_API_URL_ALT = "http://192.168.10.110:11434"

# Modèle Ollama à utiliser
OLLAMA_MODEL = "llama3.2:latest"  # ou "mistral", "codellama", etc.

# Timeout pour les requêtes IA (en secondes)
AI_TIMEOUT = 90

# Nombre maximum de tokens pour la réponse
MAX_TOKENS = 2000

# ============================================================================
# CLÉS API EXTERNES (optionnel - fallback)
# ============================================================================
# Ces clés sont utilisées uniquement si Ollama n'est pas disponible
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')

# ============================================================================
# CONFIGURATION RECHERCHE WEB
# ============================================================================
WEB_SEARCH_ENABLED = True
WEB_SEARCH_TIMEOUT = 10
MAX_WEB_RESULTS = 3

# ============================================================================
# CONFIGURATION FILTRAGE ÉVÉNEMENTS
# ============================================================================
# Seuil minimum de priorité pour créer un ticket (1-10)
MIN_PRIORITY_THRESHOLD = 4

# Activer la vérification en ligne de la sévérité
ENABLE_ONLINE_SEVERITY_CHECK = True

# ============================================================================
# CONFIGURATION EMAILS (optionnel)
# ============================================================================
SMTP_ENABLED = False
SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587
SMTP_USERNAME = ""
SMTP_PASSWORD = ""
SMTP_FROM = ""
SMTP_TO = ["admin@example.com"]

# ============================================================================
# APPAREILS SURVEILLÉS
# ============================================================================
MONITORED_DEVICES = {
    '192.168.1.254': {
        'name': 'Stormshield UTM',
        'type': 'firewall',
        'icon': '🔥',
        'priority_boost': 3
    },
    '192.168.1.15': {
        'name': 'Switch Principal',
        'type': 'switch',
        'icon': '🔌',
        'priority_boost': 2
    },
    '192.168.1.11': {
        'name': 'Borne WiFi',
        'type': 'wifi',
        'icon': '📡',
        'priority_boost': 1
    }
}

# ============================================================================
# CATÉGORIES D'APPAREILS
# ============================================================================
DEVICE_CATEGORIES = {
    'Serveur AD': {
        'keywords': ['DC', 'Active Directory', 'LDAP', 'DNS', 'Kerberos', 'NTDS', 'DFS'],
        'icon': '🖥️',
        'priority_boost': 2
    },
    'Serveur IA': {
        'keywords': ['IA', 'Ollama', 'AI', 'Machine Learning', 'GPU'],
        'icon': '🤖',
        'priority_boost': 1
    },
    'Stormshield': {
        'keywords': ['192.168.1.254', 'Stormshield', 'firewall', 'utm'],
        'icon': '🔥',
        'priority_boost': 3
    },
    'Switch': {
        'keywords': ['192.168.1.15', 'Switch', 'switch', 'port', 'vlan'],
        'icon': '🔌',
        'priority_boost': 1
    },
    'Borne WiFi': {
        'keywords': ['192.168.1.11', 'WiFi', 'wireless', 'SSID', 'AP'],
        'icon': '📡',
        'priority_boost': 1
    },
    'Serveurs': {
        'keywords': ['Server', 'SRV-', 'Windows Server'],
        'icon': '💻',
        'priority_boost': 1
    },
    'Autres': {
        'keywords': [],
        'icon': '❓',
        'priority_boost': 0
    }
}

# ============================================================================
# EVENT IDS CRITIQUES
# ============================================================================
CRITICAL_EVENT_IDS = {
    # Niveau 10 - CRITIQUE ABSOLU
    1102: 10,  # Journal d'audit effacé
    4719: 10,  # Modification politique d'audit
    4794: 10,  # Mode restauration services d'annuaire
    
    # Niveau 9 - TRÈS HAUTE PRIORITÉ
    4765: 9,   # Historique SID ajouté
    7045: 9,   # Nouveau service installé
    4697: 9,   # Service installé dans le système
    
    # Niveau 8 - HAUTE PRIORITÉ
    4625: 8,   # Échec d'authentification
    1001: 8,   # Crash système (BSOD)
    4724: 8,   # Tentative de réinitialisation mot de passe
    4728: 8,   # Membre ajouté à un groupe de sécurité global
    4732: 8,   # Membre ajouté à un groupe local
    4756: 8,   # Membre ajouté à un groupe universel
    
    # Niveau 7 - PRIORITÉ MOYENNE-HAUTE
    41: 7,     # Redémarrage sans arrêt propre
    6008: 7,   # Arrêt inattendu
    4720: 7,   # Compte utilisateur créé
    4648: 7,   # Tentative de connexion explicite
    
    # Niveau 6 - PRIORITÉ MOYENNE
    4688: 6,   # Nouveau processus créé
    4722: 6,   # Compte utilisateur activé
    1311: 6,   # Erreur réplication KCC
    2087: 6,   # Échec résolution DNS pour DC
    2088: 6,   # Échec recherche DC
    
    # Niveau 5 - PRIORITÉ BASSE-MOYENNE
    1000: 5,   # Crash d'application
    1002: 5,   # Application bloquée
}

# ============================================================================
# MOTS-CLÉS CRITIQUES
# ============================================================================
CRITICAL_KEYWORDS = {
    # Niveau 10
    'ransomware': 10, 'intrusion': 10, 'breach': 10, 'compromis': 10,
    'hack': 10, 'rootkit': 10,
    
    # Niveau 9
    'exploit': 9, 'privilege escalation': 9, 'élévation de privilèges': 9,
    'backdoor': 9,
    
    # Niveau 8
    'attack': 8, 'attaque': 8, 'unauthorized': 8, 'non autorisé': 8,
    'malware': 8, 'blocked': 8, 'denied': 8,
    
    # Niveau 7
    'trojan': 7, 'worm': 7, 'botnet': 7, 'alert': 7,
    
    # Niveau 6
    'virus': 6, 'vulnerability': 6, 'vulnérabilité': 6,
    'brute force': 6, 'injection': 6, 'critical': 6, 'critique': 6,
    
    # Niveau 5
    'suspicious': 5, 'suspect': 5, 'warning': 5, 'error': 5,
    
    # Niveau 4
    'corruption': 4, 'fatal': 4, 'emergency': 4,
}

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================
def ensure_directories():
    """Crée tous les répertoires nécessaires"""
    directories = [
        OUTPUT_DIR,
        os.path.dirname(HISTORY_FILE),
        LOCAL_LOGS_PATH
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        
    # Créer les sous-dossiers de catégories
    for category in DEVICE_CATEGORIES.keys():
        category_path = os.path.join(OUTPUT_DIR, category)
        os.makedirs(category_path, exist_ok=True)


def validate_config():
    """Valide la configuration et retourne les problèmes trouvés"""
    issues = []
    
    # Vérifier chemins critiques
    if not os.path.exists(os.path.dirname(LOG_FILE)):
        issues.append(f"Dossier ForwardedEvents introuvable: {os.path.dirname(LOG_FILE)}")
    
    # Vérifier Ollama
    import requests
    ollama_available = False
    for url in [OLLAMA_API_URL, OLLAMA_API_URL_ALT]:
        try:
            r = requests.get(f"{url}/api/tags", timeout=2)
            if r.status_code == 200:
                ollama_available = True
                break
        except:
            pass
    
    if not ollama_available:
        issues.append("Ollama n'est pas accessible. Vérifiez qu'il est démarré.")
    
    # Vérifier clés API de secours
    if not ollama_available and not any([ANTHROPIC_API_KEY, OPENAI_API_KEY, GROQ_API_KEY]):
        issues.append("Aucune API d'IA configurée (ni Ollama, ni API externe)")
    
    return issues


def get_ollama_url():
    """Retourne l'URL Ollama accessible"""
    import requests
    
    for url in [OLLAMA_API_URL, OLLAMA_API_URL_ALT]:
        try:
            r = requests.get(f"{url}/api/tags", timeout=2)
            if r.status_code == 200:
                return url
        except:
            continue
    
    return OLLAMA_API_URL


def get_ollama_web_url():
    """Retourne l'URL de l'interface web Ollama accessible"""
    import requests
    
    for url in [OLLAMA_WEB_URL, OLLAMA_WEB_URL_ALT]:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                return url
        except:
            continue
    
    return OLLAMA_WEB_URL


# ============================================================================
# INITIALISATION
# ============================================================================
if __name__ == "__main__":
    print(f"Configuration {APP_NAME} v{APP_VERSION}")
    print("=" * 60)
    
    ensure_directories()
    print("✓ Répertoires créés")
    
    issues = validate_config()
    if issues:
        print("\n⚠️  Problèmes détectés:")
        for issue in issues:
            print(f"  • {issue}")
    else:
        print("\n✅ Configuration valide")
    
    print(f"\n🤖 URL Ollama API: {get_ollama_url()}")
    print(f"🌐 URL Ollama Web: {get_ollama_web_url()}")