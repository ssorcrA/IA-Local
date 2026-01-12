import os
from pathlib import Path

APP_NAME = "AD Log Monitor Pro"
APP_VERSION = "3.0"

LOG_FILE = r"C:\IA\JournalTransfert\ForwardedEvents.evtx"
OUTPUT_DIR = r"C:\IA\Tickets"
HISTORY_FILE = r"C:\IA\historique.json"

SYSLOG_PATH = r"\\SRV-SYSLOG\surveillence$\syslog"
SYSLOG_ARCHIVE_PATH = r"\\SRV-SYSLOG\surveillence$\archive"
LOCAL_LOGS_PATH = r"C:\IA\Logs"

POLLING_INTERVAL = 60
INITIAL_CHECK_HOURS = 24
CLEANUP_DAYS = 30
MAX_EVENTS_PER_CYCLE = 100

OLLAMA_WEB_URL = "http://localhost:3000"
OLLAMA_WEB_URL_ALT = "http://192.168.10.110:3000"
OLLAMA_API_URL = "http://localhost:11434"
OLLAMA_API_URL_ALT = "http://192.168.10.110:11434"
OLLAMA_MODEL = "llama3.2:latest"
AI_TIMEOUT = 90
MAX_TOKENS = 2000

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')

WEB_SEARCH_ENABLED = True
WEB_SEARCH_TIMEOUT = 10
MAX_WEB_RESULTS = 3

MIN_PRIORITY_THRESHOLD = 4
ENABLE_ONLINE_SEVERITY_CHECK = True

SMTP_ENABLED = False
SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587
SMTP_USERNAME = ""
SMTP_PASSWORD = ""
SMTP_FROM = ""
SMTP_TO = ["admin@example.com"]

MONITORED_DEVICES = {
    '192.168.1.254': {'name': 'Stormshield UTM', 'type': 'firewall', 'icon': '🔥', 'priority_boost': 3},
    '192.168.1.15': {'name': 'Switch Principal', 'type': 'switch', 'icon': '🔌', 'priority_boost': 2},
    '192.168.1.11': {'name': 'Borne WiFi', 'type': 'wifi', 'icon': '📡', 'priority_boost': 1}
}

DEVICE_CATEGORIES = {
    'Serveur AD': {'keywords': ['DC', 'Active Directory', 'LDAP', 'DNS', 'Kerberos', 'NTDS', 'DFS'], 'icon': '🖥️', 'priority_boost': 2},
    'Serveur IA': {'keywords': ['IA', 'Ollama', 'AI', 'Machine Learning', 'GPU'], 'icon': '🤖', 'priority_boost': 1},
    'Stormshield': {'keywords': ['192.168.1.254', 'Stormshield', 'firewall', 'utm'], 'icon': '🔥', 'priority_boost': 3},
    'Switch': {'keywords': ['192.168.1.15', 'Switch', 'switch', 'port', 'vlan'], 'icon': '🔌', 'priority_boost': 1},
    'Borne WiFi': {'keywords': ['192.168.1.11', 'WiFi', 'wireless', 'SSID', 'AP'], 'icon': '📡', 'priority_boost': 1},
    'Serveurs': {'keywords': ['Server', 'SRV-', 'Windows Server'], 'icon': '💻', 'priority_boost': 1},
    'Autres': {'keywords': [], 'icon': '❓', 'priority_boost': 0}
}

CRITICAL_EVENT_IDS = {
    1102: 10, 4719: 10, 4794: 10,
    4765: 9, 7045: 9, 4697: 9,
    4625: 8, 1001: 8, 4724: 8, 4728: 8, 4732: 8, 4756: 8,
    41: 7, 6008: 7, 4720: 7, 4648: 7,
    4688: 6, 4722: 6, 1311: 6, 2087: 6, 2088: 6,
    1000: 5, 1002: 5,
}

CRITICAL_KEYWORDS = {
    'ransomware': 10, 'intrusion': 10, 'breach': 10, 'compromis': 10, 'hack': 10, 'rootkit': 10,
    'exploit': 9, 'privilege escalation': 9, 'élévation de privilèges': 9, 'backdoor': 9,
    'attack': 8, 'attaque': 8, 'unauthorized': 8, 'non autorisé': 8, 'malware': 8, 'blocked': 8, 'denied': 8,
    'trojan': 7, 'worm': 7, 'botnet': 7, 'alert': 7,
    'virus': 6, 'vulnerability': 6, 'vulnérabilité': 6, 'brute force': 6, 'injection': 6, 'critical': 6, 'critique': 6,
    'suspicious': 5, 'suspect': 5, 'warning': 5, 'error': 5,
    'corruption': 4, 'fatal': 4, 'emergency': 4,
}

def ensure_directories():
    directories = [OUTPUT_DIR, os.path.dirname(HISTORY_FILE), LOCAL_LOGS_PATH]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    for category in DEVICE_CATEGORIES.keys():
        category_path = os.path.join(OUTPUT_DIR, category)
        os.makedirs(category_path, exist_ok=True)

def validate_config():
    issues = []
    if not os.path.exists(os.path.dirname(LOG_FILE)):
        issues.append(f"Dossier ForwardedEvents introuvable: {os.path.dirname(LOG_FILE)}")
    
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
    if not ollama_available and not any([ANTHROPIC_API_KEY, OPENAI_API_KEY, GROQ_API_KEY]):
        issues.append("Aucune API d'IA configurée (ni Ollama, ni API externe)")
    return issues

def get_ollama_url():
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
    import requests
    for url in [OLLAMA_WEB_URL, OLLAMA_WEB_URL_ALT]:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                return url
        except:
            continue
    return OLLAMA_WEB_URL

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