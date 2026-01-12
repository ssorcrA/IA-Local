"""
Analyseur IA avec ARRÊT IMMÉDIAT garanti
Fichier : enhanced_ai_analyzer.py - VERSION CORRIGÉE
CORRECTIFS:
- Arrêt immédiat des requêtes HTTP
- Fermeture de session garantie
- Timeout raisonnable pour API externes
"""
import requests
import json
import webbrowser
import threading
from config import (
    get_ollama_url, get_ollama_web_url,
    OLLAMA_MODEL, MAX_TOKENS,
    ANTHROPIC_API_KEY, OPENAI_API_KEY, GROQ_API_KEY
)


class EnhancedAIAnalyzer:
    """Analyseur IA avec arrêt immédiat garanti"""
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.ollama_api_url = get_ollama_url()
        self.ollama_web_url = get_ollama_web_url()
        self.ollama_available = False
        self.available_models = []
        self.stop_requested = False
        self.current_session = None
        self.current_thread = None
    
    def log(self, message):
        """Log un message"""
        if self.log_callback:
            try:
                self.log_callback(message)
            except:
                print(message)
        else:
            print(message)
    
    def request_stop(self):
        """Demande l'arrêt IMMÉDIAT de l'analyse"""
        self.stop_requested = True
        self.log("🛑 Arrêt demandé pour l'analyseur IA")
        
        # Fermer la session HTTP en cours
        if self.current_session:
            try:
                self.current_session.close()
                self.log("  ✓ Session HTTP fermée")
            except:
                pass
        
        # Marquer la session comme None
        self.current_session = None
    
    def reset_stop(self):
        """Réinitialise le flag d'arrêt"""
        self.stop_requested = False
        self.current_session = None
    
    def check_ollama_endpoints(self):
        """Vérifie la disponibilité d'Ollama"""
        self.log("\n🔍 VÉRIFICATION OLLAMA")
        self.log("=" * 80)
        
        # Vérifier API
        try:
            self.log(f"  📡 Test API: {self.ollama_api_url}")
            response = requests.get(
                f"{self.ollama_api_url}/api/tags",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.available_models = [model['name'] for model in data.get('models', [])]
                self.ollama_available = True
                
                self.log(f"  ✅ API Ollama accessible")
                self.log(f"  📦 Modèles disponibles: {len(self.available_models)}")
                
                for model in self.available_models:
                    icon = "🤖" if model == OLLAMA_MODEL else "  "
                    self.log(f"     {icon} {model}")
                
                if OLLAMA_MODEL in self.available_models:
                    self.log(f"  ✓ Modèle configuré '{OLLAMA_MODEL}' trouvé")
                else:
                    self.log(f"  ⚠️ Modèle '{OLLAMA_MODEL}' non trouvé")
            else:
                self.log(f"  ❌ API répond avec code {response.status_code}")
                self.ollama_available = False
        
        except requests.exceptions.ConnectionError:
            self.log(f"  ❌ Impossible de se connecter à l'API")
            self.ollama_available = False
        except Exception as e:
            self.log(f"  ❌ Erreur: {str(e)}")
            self.ollama_available = False
        
        self.log("=" * 80)
        if self.ollama_available:
            self.log("✅ Ollama opérationnel - Analyses locales activées\n")
        else:
            self.log("⚠️ Ollama indisponible - Utilisation des API externes\n")
    
    def get_working_model(self):
        """Retourne le modèle à utiliser"""
        if OLLAMA_MODEL in self.available_models:
            return OLLAMA_MODEL
        elif self.available_models:
            return self.available_models[0]
        return OLLAMA_MODEL
    
    def analyze_with_ollama(self, prompt):
        """Analyse avec Ollama local - avec timeout"""
        if not self.ollama_available or self.stop_requested:
            return None
        
        try:
            model = self.get_working_model()
            self.log(f"  🤖 Analyse avec Ollama ({model})...")
            
            # Créer une nouvelle session
            self.current_session = requests.Session()
            
            # Timeout de 60 secondes pour Ollama
            response = self.current_session.post(
                f'{self.ollama_api_url}/api/generate',
                json={
                    'model': model,
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'temperature': 0.7,
                        'num_predict': MAX_TOKENS
                    }
                },
                timeout=60  # Timeout raisonnable
            )
            
            # Vérifier si arrêt demandé
            if self.stop_requested:
                self.log("  🛑 Analyse annulée")
                return None
            
            if response.status_code == 200:
                result = response.json().get('response', '')
                if result:
                    self.log("  ✅ Analyse Ollama réussie")
                    return result
                else:
                    self.log("  ⚠️ Réponse Ollama vide")
                    return None
            else:
                self.log(f"  ⚠️ Ollama erreur HTTP {response.status_code}")
                return None
        
        except requests.exceptions.Timeout:
            self.log(f"  ⏱️ Ollama timeout après 60s")
            return None
        except requests.exceptions.ConnectionError:
            if self.stop_requested:
                self.log(f"  🛑 Connexion interrompue")
            else:
                self.log(f"  ⚠️ Ollama connexion perdue")
                self.ollama_available = False
            return None
        except Exception as e:
            if self.stop_requested:
                self.log(f"  🛑 Analyse interrompue")
            else:
                self.log(f"  ⚠️ Ollama erreur: {e}")
            return None
        finally:
            self.current_session = None
    
    def analyze_with_claude(self, prompt):
        """Analyse avec Claude API"""
        if not ANTHROPIC_API_KEY or self.stop_requested:
            return None
        
        try:
            self.log("  🤖 Tentative analyse avec Claude API...")
            self.current_session = requests.Session()
            
            response = self.current_session.post(
                'https://api.anthropic.com/v1/messages',
                headers={
                    'x-api-key': ANTHROPIC_API_KEY,
                    'anthropic-version': '2023-06-01',
                    'content-type': 'application/json'
                },
                json={
                    'model': 'claude-sonnet-4-20250514',
                    'max_tokens': MAX_TOKENS,
                    'messages': [{'role': 'user', 'content': prompt}]
                },
                timeout=60
            )
            
            if self.stop_requested:
                return None
            
            if response.status_code == 200:
                result = response.json()['content'][0]['text']
                self.log("  ✅ Analyse Claude réussie")
                return result
        except Exception as e:
            if not self.stop_requested:
                self.log(f"  ⚠️ Claude API erreur: {e}")
        finally:
            self.current_session = None
        return None
    
    def analyze_with_openai(self, prompt):
        """Analyse avec OpenAI API"""
        if not OPENAI_API_KEY or self.stop_requested:
            return None
        
        try:
            self.log("  🤖 Tentative analyse avec OpenAI...")
            self.current_session = requests.Session()
            
            response = self.current_session.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {OPENAI_API_KEY}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'gpt-4o-mini',
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_tokens': MAX_TOKENS
                },
                timeout=60
            )
            
            if self.stop_requested:
                return None
            
            if response.status_code == 200:
                result = response.json()['choices'][0]['message']['content']
                self.log("  ✅ Analyse OpenAI réussie")
                return result
        except Exception as e:
            if not self.stop_requested:
                self.log(f"  ⚠️ OpenAI API erreur: {e}")
        finally:
            self.current_session = None
        return None
    
    def analyze_with_groq(self, prompt):
        """Analyse avec Groq API"""
        if not GROQ_API_KEY or self.stop_requested:
            return None
        
        try:
            self.log("  🤖 Tentative analyse avec Groq...")
            self.current_session = requests.Session()
            
            response = self.current_session.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {GROQ_API_KEY}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'llama-3.3-70b-versatile',
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_tokens': MAX_TOKENS
                },
                timeout=60
            )
            
            if self.stop_requested:
                return None
            
            if response.status_code == 200:
                result = response.json()['choices'][0]['message']['content']
                self.log("  ✅ Analyse Groq réussie")
                return result
        except Exception as e:
            if not self.stop_requested:
                self.log(f"  ⚠️ Groq API erreur: {e}")
        finally:
            self.current_session = None
        return None
    
    def build_prompt(self, event, web_results=None):
        """Construit le prompt d'analyse"""
        device_type = "Windows Server"
        if event.get('_is_syslog'):
            device_type = f"{event.get('_device_name', 'Équipement réseau')} ({event.get('_device_type', 'network')})"
        
        prompt = f"""Tu es un expert en sécurité informatique. Analyse cette erreur et fournis une solution concrète.

CONTEXTE DE L'INCIDENT:
┌─────────────────────────────────────────────────────────┐
Type d'appareil: {device_type}
Source: {event['source']}
Event ID: {event['event_id']}
Type d'erreur: {event['event_type']}
Ordinateur/IP: {event['computer']}
Horodatage: {event['time_generated']}
Priorité: {event.get('_priority', 5)}/10

MESSAGE D'ERREUR:
{event['message'][:800]}
└─────────────────────────────────────────────────────────┘
"""

        if web_results:
            prompt += f"""
INFORMATIONS TROUVÉES SUR LE WEB:
{web_results[:1500]}
"""

        prompt += """
FOURNIS UNE ANALYSE STRUCTURÉE:

🔍 1. DIAGNOSTIC
   • Explication claire du problème
   • Impact sur le système

⚡ 2. SOLUTION IMMÉDIATE
   • Actions à faire MAINTENANT
   • Commandes exactes si applicable

🛠️ 3. RÉSOLUTION COMPLÈTE
   • Procédure détaillée pas à pas
   • Configuration à modifier

🔒 4. PRÉVENTION
   • Mesures pour éviter la récurrence

Réponds en FRANÇAIS et sois PRÉCIS."""

        return prompt
    
    def analyze(self, event, web_results=None):
        """Analyse l'erreur avec cascade de providers"""
        # Réinitialiser le flag d'arrêt
        self.reset_stop()
        
        prompt = self.build_prompt(event, web_results)
        
        self.log(f"\n🔬 ANALYSE IA EN COURS...")
        self.log(f"   Source: {event['source']}")
        self.log(f"   Event ID: {event['event_id']}")
        
        # PRIORITÉ 1: Ollama local
        if self.ollama_available and not self.stop_requested:
            result = self.analyze_with_ollama(prompt)
            if result:
                return result
        
        if self.stop_requested:
            self.log("  🛑 Analyse interrompue")
            return self.fallback_analysis(event)
        
        # FALLBACK: APIs externes
        self.log("  ⚠️ Ollama indisponible, utilisation des API externes...")
        
        providers = [
            ('Groq', self.analyze_with_groq),
            ('Claude', self.analyze_with_claude),
            ('OpenAI', self.analyze_with_openai)
        ]
        
        for name, func in providers:
            if self.stop_requested:
                break
            result = func(prompt)
            if result:
                return result
        
        # Si aucune IA n'a fonctionné
        self.log("  ⚠️ Aucune IA disponible, analyse basique")
        return self.fallback_analysis(event)
    
    def fallback_analysis(self, event):
        """Analyse de secours"""
        return f"""🔍 DIAGNOSTIC:
Erreur détectée - Event ID {event['event_id']} depuis {event['source']}
Aucun service d'analyse IA n'est actuellement disponible.

⚡ ACTIONS IMMÉDIATES RECOMMANDÉES:
1. Consulter l'Observateur d'événements Windows
2. Rechercher "Event ID {event['event_id']} {event['source']}" sur Google
3. Vérifier les logs complets

🔒 RECOMMANDATIONS:
Démarrez Ollama pour obtenir des analyses IA détaillées.
"""