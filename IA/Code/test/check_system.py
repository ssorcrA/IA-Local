"""
Script de vérification complète du système
Fichier : check_system.py
"""
import os
import sys
import requests
from datetime import datetime

# Ajouter le chemin pour importer config
sys.path.insert(0, os.path.dirname(__file__))

try:
    from config import *
except ImportError:
    print("❌ ERREUR: Impossible d'importer config.py")
    print("   Assurez-vous que config.py est dans le même dossier")
    sys.exit(1)


class SystemChecker:
    """Vérificateur de configuration système"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.successes = []
    
    def print_header(self):
        """Affiche l'en-tête"""
        print("\n" + "="*80)
        print(f"  {APP_NAME} v{APP_VERSION}")
        print("  VÉRIFICATION COMPLÈTE DU SYSTÈME")
        print("="*80 + "\n")
    
    def print_section(self, title):
        """Affiche un titre de section"""
        print(f"\n{'─'*80}")
        print(f"  {title}")
        print('─'*80)
    
    def check_python_version(self):
        """Vérifie la version de Python"""
        self.print_section("🐍 PYTHON")
        
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        
        print(f"  Version: Python {version_str}")
        
        if version.major >= 3 and version.minor >= 8:
            self.successes.append("Python 3.8+ détecté")
            print("  ✅ Version compatible")
        else:
            self.issues.append(f"Python {version_str} trop ancien (requis: 3.8+)")
            print(f"  ❌ Version incompatible (requis: 3.8+)")
    
    def check_dependencies(self):
        """Vérifie les dépendances Python"""
        self.print_section("📦 DÉPENDANCES PYTHON")
        
        dependencies = {
            'win32evtlog': 'pywin32',
            'requests': 'requests',
            'bs4': 'beautifulsoup4'
        }
        
        for module, package in dependencies.items():
            try:
                __import__(module)
                print(f"  ✅ {package}")
                self.successes.append(f"{package} installé")
            except ImportError:
                print(f"  ❌ {package} MANQUANT")
                self.issues.append(f"{package} non installé")
                print(f"      Installation: pip install {package}")
    
    def check_directories(self):
        """Vérifie les répertoires"""
        self.print_section("📁 RÉPERTOIRES")
        
        directories = {
            'Output': OUTPUT_DIR,
            'Logs locaux': LOCAL_LOGS_PATH,
            'ForwardedEvents': os.path.dirname(LOG_FILE)
        }
        
        for name, path in directories.items():
            if os.path.exists(path):
                print(f"  ✅ {name}: {path}")
                self.successes.append(f"Répertoire {name} existe")
            else:
                print(f"  ⚠️  {name}: {path} (sera créé)")
                self.warnings.append(f"Répertoire {name} n'existe pas")
    
    def check_forwardedevents(self):
        """Vérifie l'accès à ForwardedEvents"""
        self.print_section("📊 FORWARDEDEVENTS")
        
        print(f"  Fichier: {LOG_FILE}")
        
        if os.path.exists(LOG_FILE):
            size = os.path.getsize(LOG_FILE) / (1024 * 1024)
            print(f"  ✅ Fichier détecté ({size:.2f} MB)")
            
            try:
                # Test de lecture
                with open(LOG_FILE, 'rb') as f:
                    f.read(100)
                print(f"  ✅ Accès en lecture OK")
                self.successes.append("ForwardedEvents accessible")
            except PermissionError:
                print(f"  ❌ Accès refusé (permissions insuffisantes)")
                self.issues.append("Permissions insuffisantes sur ForwardedEvents")
            except Exception as e:
                print(f"  ⚠️  Erreur: {e}")
                self.warnings.append(f"Erreur ForwardedEvents: {e}")
        else:
            print(f"  ❌ Fichier introuvable")
            self.issues.append("ForwardedEvents introuvable")
    
    def check_syslog(self):
        """Vérifie l'accès Syslog"""
        self.print_section("📡 SYSLOG")
        
        # Syslog principal
        print(f"  Fichier principal: {SYSLOG_PATH}")
        if os.path.exists(SYSLOG_PATH):
            size = os.path.getsize(SYSLOG_PATH) / (1024 * 1024)
            print(f"  ✅ Fichier détecté ({size:.2f} MB)")
            self.successes.append("Syslog accessible")
        else:
            print(f"  ⚠️  Fichier introuvable")
            self.warnings.append("Syslog principal non accessible")
        
        # Archives
        print(f"\n  Archives: {SYSLOG_ARCHIVE_PATH}")
        if os.path.exists(SYSLOG_ARCHIVE_PATH):
            archives = [f for f in os.listdir(SYSLOG_ARCHIVE_PATH) if f.startswith('syslog-')]
            print(f"  ✅ Dossier détecté ({len(archives)} archives)")
            self.successes.append(f"{len(archives)} archives Syslog trouvées")
        else:
            print(f"  ⚠️  Dossier introuvable")
            self.warnings.append("Archives Syslog non accessibles")
    
    def check_ollama(self):
        """Vérifie Ollama"""
        self.print_section("🤖 OLLAMA")
        
        # Test API locale
        print(f"  API locale: {OLLAMA_API_URL}")
        try:
            response = requests.get(f"{OLLAMA_API_URL}/api/tags", timeout=3)
            if response.status_code == 200:
                models = response.json().get('models', [])
                print(f"  ✅ API accessible")
                print(f"  📦 Modèles installés: {len(models)}")
                
                for model in models:
                    name = model['name']
                    icon = "  🎯" if name == OLLAMA_MODEL else "    "
                    print(f"{icon} {name}")
                
                if OLLAMA_MODEL in [m['name'] for m in models]:
                    print(f"  ✅ Modèle configuré '{OLLAMA_MODEL}' trouvé")
                    self.successes.append("Ollama opérationnel avec modèle configuré")
                else:
                    print(f"  ⚠️  Modèle '{OLLAMA_MODEL}' non trouvé")
                    print(f"      Installation: ollama pull {OLLAMA_MODEL}")
                    self.warnings.append(f"Modèle Ollama '{OLLAMA_MODEL}' non installé")
            else:
                print(f"  ❌ API répond avec code {response.status_code}")
                self.issues.append(f"Ollama répond incorrectement ({response.status_code})")
        
        except requests.exceptions.ConnectionError:
            print(f"  ❌ Impossible de se connecter")
            self.issues.append("Ollama non démarré ou inaccessible")
            print(f"      Démarrage: ollama serve")
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
            self.issues.append(f"Erreur Ollama: {e}")
        
        # Test API alternative
        if OLLAMA_API_URL_ALT != OLLAMA_API_URL:
            print(f"\n  API alternative: {OLLAMA_API_URL_ALT}")
            try:
                response = requests.get(f"{OLLAMA_API_URL_ALT}/api/tags", timeout=3)
                if response.status_code == 200:
                    print(f"  ✅ API alternative accessible")
                    self.successes.append("API Ollama alternative accessible")
                else:
                    print(f"  ⚠️  API alternative indisponible")
            except:
                print(f"  ⚠️  API alternative non accessible")
        
        # Test interface web
        print(f"\n  Interface web: {OLLAMA_WEB_URL}")
        try:
            response = requests.get(OLLAMA_WEB_URL, timeout=3)
            if response.status_code == 200:
                print(f"  ✅ Interface web accessible")
                print(f"      Accès: {OLLAMA_WEB_URL}")
                self.successes.append("Interface web Ollama accessible")
            else:
                print(f"  ⚠️  Interface web indisponible")
        except:
            print(f"  ⚠️  Interface web non accessible")
            self.warnings.append("Interface web Ollama non disponible")
    
    def check_external_apis(self):
        """Vérifie les APIs externes"""
        self.print_section("🌐 APIs EXTERNES (FALLBACK)")
        
        apis = {
            'Anthropic Claude': ANTHROPIC_API_KEY,
            'OpenAI GPT': OPENAI_API_KEY,
            'Groq': GROQ_API_KEY
        }
        
        has_api = False
        for name, key in apis.items():
            if key:
                print(f"  ✅ {name}: Configuré")
                self.successes.append(f"API {name} configurée")
                has_api = True
            else:
                print(f"  ⚠️  {name}: Non configuré")
        
        if not has_api:
            print("\n  ℹ️  Aucune API externe configurée")
            print("     Le système fonctionnera uniquement avec Ollama")
    
    def check_monitored_devices(self):
        """Vérifie les appareils surveillés"""
        self.print_section("🔍 APPAREILS SURVEILLÉS")
        
        print(f"  Nombre d'appareils: {len(MONITORED_DEVICES)}")
        
        for ip, info in MONITORED_DEVICES.items():
            print(f"\n  {info['icon']} {info['name']}")
            print(f"     IP: {ip}")
            print(f"     Type: {info['type']}")
            print(f"     Boost priorité: +{info['priority_boost']}")
            
            # Test ping (optionnel)
            # response = os.system(f"ping -n 1 -w 1000 {ip} > nul 2>&1")
            # if response == 0:
            #     print(f"     ✅ Accessible")
            # else:
            #     print(f"     ⚠️  Inaccessible")
    
    def check_configuration(self):
        """Vérifie la configuration"""
        self.print_section("⚙️  CONFIGURATION")
        
        print(f"  Intervalle de surveillance: {POLLING_INTERVAL}s")
        print(f"  Check initial: {INITIAL_CHECK_HOURS}h")
        print(f"  Seuil priorité minimum: {MIN_PRIORITY_THRESHOLD}/10")
        print(f"  Nettoyage après: {CLEANUP_DAYS} jours")
        print(f"  Recherche web: {'Activée' if WEB_SEARCH_ENABLED else 'Désactivée'}")
        print(f"  Timeout IA: {AI_TIMEOUT}s")
        print(f"  Max tokens: {MAX_TOKENS}")
        
        print(f"\n  Event IDs critiques: {len(CRITICAL_EVENT_IDS)}")
        print(f"  Mots-clés critiques: {len(CRITICAL_KEYWORDS)}")
        print(f"  Catégories d'appareils: {len(DEVICE_CATEGORIES)}")
    
    def print_summary(self):
        """Affiche le résumé"""
        self.print_section("📊 RÉSUMÉ")
        
        total = len(self.successes) + len(self.warnings) + len(self.issues)
        
        print(f"\n  ✅ Succès: {len(self.successes)}/{total}")
        print(f"  ⚠️  Avertissements: {len(self.warnings)}/{total}")
        print(f"  ❌ Problèmes: {len(self.issues)}/{total}")
        
        if self.issues:
            print("\n  🔴 PROBLÈMES À RÉSOUDRE:")
            for i, issue in enumerate(self.issues, 1):
                print(f"     {i}. {issue}")
        
        if self.warnings:
            print("\n  🟡 AVERTISSEMENTS:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"     {i}. {warning}")
        
        print("\n" + "="*80)
        
        if not self.issues:
            print("  ✅ SYSTÈME OPÉRATIONNEL")
            print("  Vous pouvez lancer l'application: python main.py")
        else:
            print("  ⚠️  RÉSOLVEZ LES PROBLÈMES AVANT DE CONTINUER")
            print("  Consultez le README.md pour plus d'informations")
        
        print("="*80 + "\n")
    
    def run_all_checks(self):
        """Execute toutes les vérifications"""
        self.print_header()
        
        self.check_python_version()
        self.check_dependencies()
        self.check_directories()
        self.check_forwardedevents()
        self.check_syslog()
        self.check_ollama()
        self.check_external_apis()
        self.check_monitored_devices()
        self.check_configuration()
        
        self.print_summary()


def main():
    """Point d'entrée"""
    try:
        checker = SystemChecker()
        checker.run_all_checks()
    except KeyboardInterrupt:
        print("\n\n⚠️  Vérification interrompue par l'utilisateur\n")
    except Exception as e:
        print(f"\n❌ ERREUR FATALE: {e}\n")
        import traceback
        traceback.print_exc()
    finally:
        # Cette partie s'exécutera quoi qu'il arrive (succès ou erreur)
        print("\n" + "─"*80)
        input("Appuyez sur ENTRÉE pour fermer cette fenêtre...")


if __name__ == "__main__":
    main()