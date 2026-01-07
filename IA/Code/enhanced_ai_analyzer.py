"""
Analyseur IA amélioré avec interface Ollama locale
Fichier : enhanced_ai_analyzer.py
"""
import requests
import json
import webbrowser
from config import (
    get_ollama_url, get_ollama_web_url,
    OLLAMA_MODEL, AI_TIMEOUT, MAX_TOKENS,
    ANTHROPIC_API_KEY, OPENAI_API_KEY, GROQ_API_KEY
)


class EnhancedAIAnalyzer:
    """Analyseur IA avec priorité sur Ollama local"""
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.ollama_api_url = get_ollama_url()
        self.ollama_web_url = get_ollama_web_url()
        self.ollama_available = False
        self.available_models = []
    
    def log(self, message):
        """Log un message"""
        if self.log_callback:
            try:
                self.log_callback(message)
            except:
                print(message)
        else:
            print(message)
    
    def check_ollama_endpoints(self):
        """Vérifie la disponibilité d'Ollama et liste les modèles"""
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
                    self.log(f"  ⚠️  Modèle '{OLLAMA_MODEL}' non trouvé, utilisation du premier disponible")
            else:
                self.log(f"  ❌ API répond avec code {response.status_code}")
        
        except requests.exceptions.ConnectionError:
            self.log(f"  ❌ Impossible de se connecter à l'API")
        except Exception as e:
            self.log(f"  ❌ Erreur: {str(e)}")
        
        # Vérifier interface web
        try:
            self.log(f"\n  🌐 Test interface web: {self.ollama_web_url}")
            response = requests.get(self.ollama_web_url, timeout=3)
            
            if response.status_code == 200:
                self.log(f"  ✅ Interface web accessible")
                self.log(f"  💡 Ouvrir dans le navigateur: {self.ollama_web_url}")
            else:
                self.log(f"  ⚠️  Interface web répond avec code {response.status_code}")
        
        except:
            self.log(f"  ⚠️  Interface web non accessible")
        
        # Résumé
        self.log("=" * 80)
        if self.ollama_available:
            self.log("✅ Ollama opérationnel - Analyses locales activées\n")
        else:
            self.log("⚠️  Ollama indisponible - Utilisation des API externes\n")
    
    def get_working_model(self):
        """Retourne le modèle à utiliser"""
        if OLLAMA_MODEL in self.available_models:
            return OLLAMA_MODEL
        elif self.available_models:
            return self.available_models[0]
        return OLLAMA_MODEL
    
    def open_ollama_web(self):
        """Ouvre l'interface web Ollama dans le navigateur"""
        try:
            webbrowser.open(self.ollama_web_url)
            self.log(f"🌐 Interface Ollama ouverte: {self.ollama_web_url}")
            return True
        except Exception as e:
            self.log(f"❌ Impossible d'ouvrir l'interface: {e}")
            return False
    
    def analyze_with_ollama(self, prompt):
        """Analyse avec Ollama local"""
        if not self.ollama_available:
            return None
        
        try:
            model = self.get_working_model()
            self.log(f"  🤖 Analyse avec Ollama ({model})...")
            
            response = requests.post(
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
                timeout=AI_TIMEOUT
            )
            
            if response.status_code == 200:
                result = response.json().get('response', '')
                if result:
                    self.log("  ✅ Analyse Ollama réussie")
                    return result
                else:
                    self.log("  ⚠️  Réponse Ollama vide")
            else:
                self.log(f"  ⚠️  Ollama erreur HTTP {response.status_code}")
        
        except requests.exceptions.Timeout:
            self.log(f"  ⚠️  Ollama timeout après {AI_TIMEOUT}s")
        except requests.exceptions.ConnectionError:
            self.log(f"  ⚠️  Ollama connexion perdue")
            self.ollama_available = False
        except Exception as e:
            self.log(f"  ⚠️  Ollama erreur: {e}")
        
        return None
    
    def analyze_with_claude(self, prompt):
        """Analyse avec Claude API (fallback)"""
        if not ANTHROPIC_API_KEY:
            return None
        
        try:
            self.log("  🤖 Tentative analyse avec Claude API...")
            response = requests.post(
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
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()['content'][0]['text']
                self.log("  ✅ Analyse Claude réussie")
                return result
        except Exception as e:
            self.log(f"  ⚠️  Claude API erreur: {e}")
        return None
    
    def analyze_with_openai(self, prompt):
        """Analyse avec OpenAI API (fallback)"""
        if not OPENAI_API_KEY:
            return None
        
        try:
            self.log("  🤖 Tentative analyse avec OpenAI...")
            response = requests.post(
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
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()['choices'][0]['message']['content']
                self.log("  ✅ Analyse OpenAI réussie")
                return result
        except Exception as e:
            self.log(f"  ⚠️  OpenAI API erreur: {e}")
        return None
    
    def analyze_with_groq(self, prompt):
        """Analyse avec Groq API (fallback)"""
        if not GROQ_API_KEY:
            return None
        
        try:
            self.log("  🤖 Tentative analyse avec Groq...")
            response = requests.post(
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
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()['choices'][0]['message']['content']
                self.log("  ✅ Analyse Groq réussie")
                return result
        except Exception as e:
            self.log(f"  ⚠️  Groq API erreur: {e}")
        return None
    
    def build_prompt(self, event, web_results=None):
        """Construit le prompt d'analyse optimisé"""
        # Déterminer le type d'appareil
        device_type = "Windows Server"
        if event.get('_is_syslog'):
            device_type = f"{event.get('_device_name', 'Équipement réseau')} ({event.get('_device_type', 'network')})"
        
        prompt = f"""Tu es un expert en sécurité informatique et administration système. Analyse cette erreur et fournis une solution concrète et actionnable.

CONTEXTE DE L'INCIDENT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Type d'appareil: {device_type}
Source: {event['source']}
Event ID: {event['event_id']}
Type d'erreur: {event['event_type']}
Ordinateur/IP: {event['computer']}
Horodatage: {event['time_generated']}
Priorité: {event.get('_priority', 5)}/10

MESSAGE D'ERREUR:
{event['message'][:800]}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        if web_results:
            prompt += f"""
INFORMATIONS TROUVÉES SUR LE WEB:
{web_results[:1500]}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        prompt += """
FOURNIS UNE ANALYSE STRUCTURÉE ET DÉTAILLÉE:

🔍 1. DIAGNOSTIC
   • Explication claire du problème en 2-3 phrases
   • Impact sur le système/réseau
   • Niveau de gravité réel

🎯 2. CAUSES PROBABLES
   • Liste de 2-3 causes possibles avec leurs probabilités
   • Contexte technique de chaque cause

⚡ 3. SOLUTION IMMÉDIATE (< 5 minutes)
   • Actions à faire MAINTENANT pour contenir le problème
   • Étapes numérotées et précises
   • Commandes exactes si applicable

🛠️ 4. RÉSOLUTION COMPLÈTE (solution durable)
   • Procédure détaillée pas à pas
   • Commandes PowerShell/CMD si nécessaire
   • Configuration à modifier
   • Vérifications à effectuer

🔒 5. PRÉVENTION
   • Mesures pour éviter la récurrence
   • Bonnes pratiques à mettre en place
   • Monitoring recommandé

IMPORTANT: 
- Sois TRÈS précis et technique
- Fournis des commandes EXACTES et testées
- Adapte-toi au type d'appareil (serveur Windows ou équipement réseau)
- Priorise la SÉCURITÉ et la STABILITÉ
- Réponds en FRANÇAIS

Commence ton analyse maintenant:"""

        return prompt
    
    def analyze(self, event, web_results=None):
        """Analyse l'erreur avec cascade de providers (Ollama prioritaire)"""
        prompt = self.build_prompt(event, web_results)
        
        # PRIORITÉ 1: Ollama local (plus rapide et privé)
        if self.ollama_available:
            result = self.analyze_with_ollama(prompt)
            if result:
                return result
        
        # FALLBACK: APIs externes
        self.log("  ⚠️  Ollama indisponible, utilisation des API externes...")
        
        providers = [
            ('Groq', self.analyze_with_groq),
            ('Claude', self.analyze_with_claude),
            ('OpenAI', self.analyze_with_openai)
        ]
        
        for name, func in providers:
            result = func(prompt)
            if result:
                return result
        
        # Si aucune IA n'a fonctionné
        self.log("  ⚠️  Aucune IA disponible, analyse basique")
        return self.fallback_analysis(event)
    
    def fallback_analysis(self, event):
        """Analyse de secours si aucune IA n'est disponible"""
        return f"""🔍 DIAGNOSTIC:
Erreur détectée - Event ID {event['event_id']} depuis {event['source']}
Aucun service d'analyse IA n'est actuellement disponible.

🎯 ANALYSE AUTOMATIQUE:
Cette erreur nécessite une investigation manuelle. Voici quelques pistes:

⚡ ACTIONS IMMÉDIATES RECOMMANDÉES:
1. Consulter l'Observateur d'événements Windows pour plus de détails
2. Rechercher "Event ID {event['event_id']} {event['source']}" sur Google
3. Vérifier les logs complets de l'application concernée
4. Consulter la documentation Microsoft ou du fabricant

🛠️ RESSOURCES UTILES:
• Event ID Database: https://www.eventid.net/search.asp?evtid={event['event_id']}
• Microsoft Docs: https://docs.microsoft.com/windows/
• TechNet Forums: https://social.technet.microsoft.com/

🔒 RECOMMANDATIONS:
1. Démarrez Ollama pour obtenir des analyses IA détaillées:
   - API: {self.ollama_api_url}
   - Interface: {self.ollama_web_url}
   
2. Ou configurez une clé API externe:
   - Anthropic Claude (ANTHROPIC_API_KEY)
   - OpenAI GPT (OPENAI_API_KEY)
   - Groq (GROQ_API_KEY)

💡 CONSEIL:
Pour des analyses précises et rapides, assurez-vous qu'Ollama est démarré
avec le modèle '{OLLAMA_MODEL}' installé.
"""
    
    def test_analysis(self):
        """Test rapide de l'analyseur"""
        self.log("\n🧪 TEST DE L'ANALYSEUR IA")
        self.log("=" * 80)
        
        test_event = {
            'source': 'Test',
            'event_id': 4625,
            'event_type': 'ERROR',
            'computer': 'TEST-PC',
            'time_generated': '2025-01-07 10:00:00',
            'message': 'Test de connexion échouée',
            '_priority': 8
        }
        
        result = self.analyze(test_event)
        
        if result and len(result) > 100:
            self.log("✅ Test réussi - Analyseur opérationnel")
            self.log(f"   Longueur de la réponse: {len(result)} caractères")
            return True
        else:
            self.log("❌ Test échoué - Vérifiez la configuration IA")
            return False