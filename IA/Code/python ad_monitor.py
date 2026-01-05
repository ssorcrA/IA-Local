import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import os
from datetime import datetime, timedelta, date
import requests
import threading
import re
from pathlib import Path
import traceback
import sys
from urllib.parse import quote_plus

# Vérification des imports optionnels
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    print("ATTENTION: beautifulsoup4 n'est pas installé")
    print("Installez avec: pip install beautifulsoup4")

try:
    import win32evtlog
    import win32evtlogutil
    WINDOWS_EVENTS_AVAILABLE = True
except ImportError:
    WINDOWS_EVENTS_AVAILABLE = False
    print("ATTENTION: pywin32 n'est pas installé")
    print("Installez avec: pip install pywin32")


# ============================================================================
# CLASSE ANALYSEUR IA - GESTION MULTI-PROVIDERS
# ============================================================================

class AIAnalyzer:
    """Gère les analyses IA avec plusieurs providers"""
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        
        # Charger les clés API depuis les variables d'environnement
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY', '')
        self.openai_key = os.getenv('OPENAI_API_KEY', '')
        self.groq_key = os.getenv('GROQ_API_KEY', '')
        
    def log(self, message):
        """Log un message"""
        if self.log_callback:
            try:
                self.log_callback(message)
            except:
                print(message)
        else:
            print(message)
    
    def analyze_with_ollama(self, prompt):
        """Analyse avec Ollama (local)"""
        try:
            self.log("  🤖 Tentative analyse avec Ollama...")
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': 'llama3.2',
                    'prompt': prompt,
                    'stream': False
                },
                timeout=90
            )
            
            if response.status_code == 200:
                result = response.json().get('response', '')
                if result:
                    self.log("  ✅ Analyse Ollama réussie")
                    return result
        except Exception as e:
            self.log(f"  ⚠️  Ollama indisponible: {e}")
        return None
    
    def analyze_with_claude(self, prompt):
        """Analyse avec Claude API"""
        if not self.anthropic_key:
            return None
        
        try:
            self.log("  🤖 Tentative analyse avec Claude API...")
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers={
                    'x-api-key': self.anthropic_key,
                    'anthropic-version': '2023-06-01',
                    'content-type': 'application/json'
                },
                json={
                    'model': 'claude-sonnet-4-20250514',
                    'max_tokens': 1500,
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
        """Analyse avec OpenAI API"""
        if not self.openai_key:
            return None
        
        try:
            self.log("  🤖 Tentative analyse avec OpenAI...")
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {self.openai_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'gpt-4o-mini',
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_tokens': 1500
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
        """Analyse avec Groq API (rapide et gratuit)"""
        if not self.groq_key:
            return None
        
        try:
            self.log("  🤖 Tentative analyse avec Groq...")
            response = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {self.groq_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'llama-3.3-70b-versatile',
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_tokens': 1500
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
    
    def analyze(self, event, web_results=None):
        """Analyse l'erreur avec cascade de providers"""
        
        # Construire le prompt
        prompt = f"""Tu es un expert en Active Directory et Windows Server. Analyse cette erreur et fournis une solution concrète.

ERREUR:
- Source: {event['source']}
- Event ID: {event['event_id']}
- Type: {event['event_type']}
- Ordinateur: {event['computer']}
- Message: {event['message'][:600]}

{'INFORMATIONS WEB TROUVÉES:' + web_results if web_results else ''}

FOURNIS UNE RÉPONSE STRUCTURÉE AVEC:
1. 🔍 DIAGNOSTIC: Explication claire du problème (2-3 phrases)
2. 🎯 CAUSES PROBABLES: Liste de 2-3 causes possibles
3. ⚡ SOLUTION RAPIDE: Actions immédiates à faire (étapes numérotées)
4. 🛠️ RÉSOLUTION COMPLÈTE: Procédure détaillée si nécessaire
5. 🔒 PRÉVENTION: Comment éviter ce problème à l'avenir

Sois concis, technique et orienté ACTION. Réponds en français."""

        # Cascade de providers (du plus rapide au plus lent)
        providers = [
            ('Ollama', self.analyze_with_ollama),
            ('Groq', self.analyze_with_groq),
            ('Claude', self.analyze_with_claude),
            ('OpenAI', self.analyze_with_openai)
        ]
        
        for name, func in providers:
            result = func(prompt)
            if result:
                return result
        
        # Si aucune IA n'a fonctionné
        self.log("  ⚠️ Aucune IA disponible, analyse basique")
        return self.fallback_analysis(event)
    
    def fallback_analysis(self, event):
        """Analyse de secours si aucune IA n'est disponible"""
        return f"""🔍 DIAGNOSTIC:
Erreur Windows détectée - Event ID {event['event_id']} depuis {event['source']}

🎯 ANALYSE AUTOMATIQUE:
Cette erreur nécessite une investigation manuelle car aucun service d'analyse IA n'est disponible.

⚡ ACTIONS RECOMMANDÉES:
1. Consulter l'Observateur d'événements Windows pour plus de détails
2. Rechercher "Event ID {event['event_id']} {event['source']}" sur Google
3. Vérifier les logs complets de l'application concernée
4. Consulter la documentation Microsoft

🛠️ RESSOURCES:
- Event ID Database: https://www.eventid.net/search.asp?evtid={event['event_id']}
- Microsoft Docs: https://docs.microsoft.com/windows/

💡 CONSEIL:
Configurez une clé API (Anthropic, OpenAI ou Groq) pour obtenir des analyses IA détaillées.
"""


# ============================================================================
# CLASSE WEB SEARCHER - RECHERCHE SANS OUVRIR NAVIGATEUR
# ============================================================================

class WebSearcher:
    """Recherche des solutions sur le web sans ouvrir le navigateur"""
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8'
        })
        self.enabled = BS4_AVAILABLE
    
    def log(self, message):
        if self.log_callback:
            try:
                self.log_callback(message)
            except:
                print(message)
        else:
            print(message)
    
    def search(self, event):
        """Recherche des solutions pour l'erreur"""
        if not self.enabled:
            self.log("  ⚠️ Recherche web désactivée (beautifulsoup4 manquant)")
            return None
            
        try:
            query = f"Event ID {event['event_id']} {event['source']} solution Windows"
            search_url = f"https://www.google.com/search?q={quote_plus(query)}&hl=fr&lr=lang_fr&num=10"
            
            self.log(f"  🔍 Recherche web: {query}")
            
            response = self.session.get(search_url, timeout=10)
            
            if response.status_code != 200:
                self.log(f"  ⚠️  Recherche échouée (HTTP {response.status_code})")
                return None
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                if '/url?q=' in href:
                    url = href.split('/url?q=')[1].split('&')[0]
                    
                    if 'google.com' not in url and 'youtube.com' not in url:
                        title = link.get_text(strip=True)
                        
                        if url and url.startswith('http'):
                            links.append({'url': url, 'title': title})
                            
                            if len(links) >= 2:
                                break
            
            if not links:
                self.log("  ⚠️  Aucun lien trouvé")
                return None
            
            self.log(f"  ✅ {len(links)} lien(s) trouvé(s)")
            
            results = []
            for i, link_data in enumerate(links, 1):
                self.log(f"  📄 Récupération source {i}: {link_data['url'][:60]}...")
                
                content = self.fetch_page_content(link_data['url'])
                
                results.append({
                    'url': link_data['url'],
                    'title': link_data['title'],
                    'content': content
                })
            
            return self.format_results(results)
            
        except Exception as e:
            self.log(f"  ⚠️ Erreur recherche web: {e}")
            return None
    
    def fetch_page_content(self, url):
        """Récupère le contenu d'une page"""
        try:
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
                    tag.decompose()
                
                text = soup.get_text(separator=' ', strip=True)
                text = re.sub(r'\s+', ' ', text).strip()
                
                return text[:800] + '...' if len(text) > 800 else text
            
            return "Contenu non disponible"
            
        except Exception as e:
            return f"Erreur récupération: {str(e)}"
    
    def format_results(self, results):
        """Formate les résultats de recherche"""
        formatted = "\n\n"
        
        for i, result in enumerate(results, 1):
            formatted += f"""{'='*60}
📄 SOURCE {i}: {result['title'][:80]}
🔗 {result['url']}
{'='*60}

{result['content']}

"""
        
        return formatted


# ============================================================================
# CLASSE TICKET MANAGER - GESTION ANTI-DOUBLONS
# ============================================================================

class TicketManager:
    """Gère les tickets avec système anti-doublons"""
    
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.ticket_index_file = os.path.join(output_dir, ".ticket_index.json")
        self.load_index()
    
    def load_index(self):
        """Charge l'index des tickets existants"""
        try:
            if os.path.exists(self.ticket_index_file):
                with open(self.ticket_index_file, 'r', encoding='utf-8') as f:
                    self.ticket_index = json.load(f)
            else:
                self.ticket_index = {}
        except Exception as e:
            print(f"Erreur chargement index: {e}")
            self.ticket_index = {}
    
    def save_index(self):
        """Sauvegarde l'index"""
        try:
            with open(self.ticket_index_file, 'w', encoding='utf-8') as f:
                json.dump(self.ticket_index, f, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde index: {e}")
    
    def get_ticket_key(self, event):
        """Génère une clé unique pour identifier un type d'erreur"""
        return f"{event['source']}_{event['event_id']}_{date.today().isoformat()}"
    
    def find_existing_ticket(self, event):
        """Trouve un ticket existant pour cette erreur aujourd'hui"""
        ticket_key = self.get_ticket_key(event)
        
        if ticket_key in self.ticket_index:
            ticket_path = self.ticket_index[ticket_key]
            if os.path.exists(ticket_path):
                return ticket_path
        
        return None
    
    def create_or_update_ticket(self, event, analysis, web_links, log_callback=None):
        """Crée un nouveau ticket ou met à jour un existant"""
        existing_ticket = self.find_existing_ticket(event)
        
        if existing_ticket:
            return self.update_existing_ticket(existing_ticket, event, log_callback)
        else:
            return self.create_new_ticket(event, analysis, web_links, log_callback)
    
    def create_new_ticket(self, event, analysis, web_links, log_callback=None):
        """Crée un nouveau ticket"""
        try:
            safe_source = re.sub(r'[^\w\-_]', '_', event['source'])
            ticket_dir = os.path.join(self.output_dir, f"{safe_source}_EventID_{event['event_id']}")
            os.makedirs(ticket_dir, exist_ok=True)
            
            today = date.today().isoformat()
            ticket_file = os.path.join(ticket_dir, f"ticket_{today}.txt")
            
            web_section = ""
            if web_links:
                web_section = "\n🌐 RESSOURCES WEB:\n"
                for i, link in enumerate(web_links, 1):
                    web_section += f"  [{i}] {link}\n"
            
            content = f"""╔══════════════════════════════════════════════════════════════╗
║                    TICKET D'ERREUR AD                        ║
╚══════════════════════════════════════════════════════════════╝

📅 CRÉÉ LE: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
🔢 OCCURRENCES: 1
⚠️  TYPE: {event['event_type']}

─────────────────────────────────────────────────────────────

📊 INFORMATIONS TECHNIQUES:
  • Source: {event['source']}
  • Event ID: {event['event_id']}
  • Ordinateur: {event['computer']}

─────────────────────────────────────────────────────────────

📝 HISTORIQUE DES OCCURRENCES:

[1] {event['time_generated']} - Record #{event['record_number']}
    Message: {event['message'][:200]}...

─────────────────────────────────────────────────────────────

🤖 ANALYSE & SOLUTION:
{analysis}
{web_section}
─────────────────────────────────────────────────────────────

📌 STATUT: NOUVEAU
🔍 NÉCESSITE ACTION: OUI
⏰ DERNIÈRE MISE À JOUR: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

═══════════════════════════════════════════════════════════════
"""
            
            with open(ticket_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            ticket_key = self.get_ticket_key(event)
            self.ticket_index[ticket_key] = ticket_file
            self.save_index()
            
            if log_callback:
                log_callback(f"  ✅ Nouveau ticket: {os.path.basename(ticket_file)}")
            
            return ticket_file
            
        except Exception as e:
            if log_callback:
                log_callback(f"  ❌ Erreur création ticket: {e}")
            return None
    
    def update_existing_ticket(self, ticket_path, event, log_callback=None):
        """Met à jour un ticket existant avec une nouvelle occurrence"""
        try:
            with open(ticket_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            occurrence_match = re.search(r'🔢 OCCURRENCES: (\d+)', content)
            current_count = int(occurrence_match.group(1)) if occurrence_match else 1
            new_count = current_count + 1
            
            content = re.sub(
                r'🔢 OCCURRENCES: \d+',
                f'🔢 OCCURRENCES: {new_count}',
                content
            )
            
            new_occurrence = f"\n[{new_count}] {event['time_generated']} - Record #{event['record_number']}\n    Message: {event['message'][:200]}...\n"
            
            history_marker = "📝 HISTORIQUE DES OCCURRENCES:"
            if history_marker in content:
                parts = content.split("─────────────────────────────────────────────────────────────")
                
                for i, part in enumerate(parts):
                    if history_marker in part:
                        parts[i] = part + new_occurrence
                        break
                
                content = "─────────────────────────────────────────────────────────────".join(parts)
            
            content = re.sub(
                r'⏰ DERNIÈRE MISE À JOUR: .+',
                f'⏰ DERNIÈRE MISE À JOUR: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                content
            )
            
            with open(ticket_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            if log_callback:
                log_callback(f"  🔄 Ticket mis à jour ({new_count} occurrences): {os.path.basename(ticket_path)}")
            
            return ticket_path
            
        except Exception as e:
            if log_callback:
                log_callback(f"  ❌ Erreur mise à jour ticket: {e}")
            return None
    
    def cleanup_old_tickets(self, days=30):
        """Nettoie les tickets de plus de X jours"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            cleaned = 0
            
            for folder in os.listdir(self.output_dir):
                folder_path = os.path.join(self.output_dir, folder)
                if not os.path.isdir(folder_path) or folder.startswith('.'):
                    continue
                
                for ticket_file in os.listdir(folder_path):
                    if not ticket_file.startswith('ticket_'):
                        continue
                    
                    ticket_path = os.path.join(folder_path, ticket_file)
                    file_date = datetime.fromtimestamp(os.path.getmtime(ticket_path))
                    
                    if file_date < cutoff_date:
                        os.remove(ticket_path)
                        cleaned += 1
                
                if not os.listdir(folder_path):
                    os.rmdir(folder_path)
            
            self.ticket_index = {
                k: v for k, v in self.ticket_index.items()
                if os.path.exists(v)
            }
            self.save_index()
            
            return cleaned
            
        except Exception as e:
            print(f"Erreur nettoyage: {e}")
            return 0


# ============================================================================
# CLASSE PRINCIPALE - INTERFACE GRAPHIQUE
# ============================================================================

class ADMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AD Log Monitor - Interface de surveillance")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2b2b2b')
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Configuration
        self.log_file = r"C:\IA\JournalTransfert\ForwardedEvents.evtx"
        self.output_dir = r"C:\IA\Tickets"
        self.history_file = r"C:\IA\historique.json"
        self.last_record = 0
        self.monitoring = False
        self.monitor_thread = None
        
        # Créer les répertoires
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        except Exception as e:
            print(f"Erreur création répertoires: {e}")
        
        # Initialiser l'interface d'abord
        self.create_widgets()
        
        # Puis initialiser les composants
        try:
            self.ticket_manager = TicketManager(self.output_dir)
            self.ai_analyzer = AIAnalyzer(log_callback=self.log_message)
            self.web_searcher = WebSearcher(log_callback=self.log_message)
            
            self.load_history()
            self.check_requirements()
            
        except Exception as e:
            error_msg = f"Erreur lors de l'initialisation:\n{str(e)}\n\n{traceback.format_exc()}"
            self.log_message(error_msg)
            print(error_msg)
    
    def on_closing(self):
        """Gère la fermeture de l'application"""
        if self.monitoring:
            if messagebox.askokcancel("Quitter", "La surveillance est active. Voulez-vous vraiment quitter?"):
                self.monitoring = False
                self.root.destroy()
        else:
            self.root.destroy()
    
    def check_requirements(self):
        """Vérifie que tous les prérequis sont OK"""
        issues = []
        
        if not WINDOWS_EVENTS_AVAILABLE:
            issues.append("❌ pywin32 non installé (pip install pywin32)")
        
        if not BS4_AVAILABLE:
            issues.append("⚠️ beautifulsoup4 non installé - recherche web désactivée (pip install beautifulsoup4)")
        
        # Vérifier l'accès au log ForwardedEvents
        if WINDOWS_EVENTS_AVAILABLE:
            try:
                hand = win32evtlog.OpenEventLog(None, "ForwardedEvents")
                win32evtlog.CloseEventLog(hand)
                self.log_message("✅ Log 'ForwardedEvents' accessible")
            except Exception as e:
                issues.append(f"❌ Log 'ForwardedEvents' inaccessible: {str(e)}")
                issues.append("   → Vérifiez que le collecteur d'événements est configuré")
                issues.append("   → Lancez l'application en tant qu'Administrateur")
        
        # Vérifier si le fichier physique existe
        if os.path.exists(self.log_file):
            file_size = os.path.getsize(self.log_file) / (1024*1024)  # en MB
            self.log_message(f"✅ Fichier log trouvé: {self.log_file} ({file_size:.2f} MB)")
        else:
            issues.append(f"⚠️ Fichier log physique introuvable: {self.log_file}")
            issues.append("   → Le log peut quand même fonctionner s'il est accessible via Windows")
        
        # Vérifier Ollama
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=2)
            if response.status_code == 200:
                self.log_message("✅ Ollama est accessible")
            else:
                issues.append("⚠️  Ollama ne répond pas correctement")
        except:
            issues.append("⚠️  Ollama n'est pas accessible (optionnel)")
        
        # Vérifier les clés API
        api_status = []
        if self.ai_analyzer.anthropic_key:
            api_status.append("Claude API")
        if self.ai_analyzer.openai_key:
            api_status.append("OpenAI")
        if self.ai_analyzer.groq_key:
            api_status.append("Groq")
        
        if api_status:
            self.log_message(f"✅ APIs configurées: {', '.join(api_status)}")
        else:
            issues.append("⚠️  Aucune clé API configurée (optionnel)")
        
        if issues:
            self.log_message("\n⚠️  PROBLÈMES DÉTECTÉS:")
            for issue in issues:
                self.log_message(f"  {issue}")
            self.log_message("\nCertains problèmes sont optionnels. L'application peut fonctionner partiellement.\n")
        else:
            self.log_message("\n✅ Tous les prérequis sont OK!\n")
    
    def load_history(self):
        """Charge l'historique des erreurs traitées"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.last_record = data.get('last_record', 0)
            else:
                self.last_record = 0
        except Exception as e:
            print(f"Erreur chargement historique: {e}")
            self.last_record = 0
    
    def save_history(self):
        """Sauvegarde l'historique"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump({'last_record': self.last_record}, f)
        except Exception as e:
            print(f"Erreur sauvegarde historique: {e}")
    
    def create_widgets(self):
        """Crée l'interface graphique"""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#2b2b2b')
        style.configure('TLabel', background='#2b2b2b', foreground='#ffffff', font=('Segoe UI', 10))
        style.configure('TButton', font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'), foreground='#4CAF50')
        
        # Header
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill='x', padx=10, pady=10)
        
        title_label = ttk.Label(header_frame, text="🛡️ AD Log Monitor v2.0", style='Title.TLabel')
        title_label.pack(side='left')
        
        # Boutons de contrôle
        control_frame = ttk.Frame(header_frame)
        control_frame.pack(side='right')
        
        self.start_button = tk.Button(control_frame, text="▶ Démarrer", 
                                      command=self.start_monitoring,
                                      bg='#4CAF50', fg='white', font=('Segoe UI', 10, 'bold'),
                                      padx=15, pady=5, relief='flat', cursor='hand2')
        self.start_button.pack(side='left', padx=5)
        
        self.stop_button = tk.Button(control_frame, text="⏸ Arrêter", 
                                     command=self.stop_monitoring,
                                     bg='#f44336', fg='white', font=('Segoe UI', 10, 'bold'),
                                     padx=15, pady=5, relief='flat', cursor='hand2', state='disabled')
        self.stop_button.pack(side='left', padx=5)
        
        refresh_button = tk.Button(control_frame, text="🔄 Rafraîchir", 
                                   command=self.refresh_tickets,
                                   bg='#2196F3', fg='white', font=('Segoe UI', 10, 'bold'),
                                   padx=15, pady=5, relief='flat', cursor='hand2')
        refresh_button.pack(side='left', padx=5)
        
        check_24h_button = tk.Button(control_frame, text="🕐 Check 24h", 
                                     command=self.initial_check,
                                     bg='#FF9800', fg='white', font=('Segoe UI', 10, 'bold'),
                                     padx=15, pady=5, relief='flat', cursor='hand2')
        check_24h_button.pack(side='left', padx=5)
        
        cleanup_button = tk.Button(control_frame, text="🧹 Nettoyer", 
                                   command=self.cleanup_old_tickets,
                                   bg='#9C27B0', fg='white', font=('Segoe UI', 10, 'bold'),
                                   padx=15, pady=5, relief='flat', cursor='hand2')
        cleanup_button.pack(side='left', padx=5)
        
        # Status bar
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="⏹ Arrêté", 
                                      font=('Segoe UI', 10, 'bold'))
        self.status_label.pack(side='left')
        
        self.last_check_label = ttk.Label(status_frame, text="Dernière vérification: Jamais", 
                                         font=('Segoe UI', 9))
        self.last_check_label.pack(side='right')
        
        # Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Onglet 1: Surveillance
        monitor_frame = ttk.Frame(self.notebook)
        self.notebook.add(monitor_frame, text="📊 Surveillance")
        self.create_monitor_tab(monitor_frame)
        
        # Onglet 2: Historique
        history_frame = ttk.Frame(self.notebook)
        self.notebook.add(history_frame, text="📁 Historique")
        self.create_history_tab(history_frame)
        
        # Onglet 3: Détails
        detail_frame = ttk.Frame(self.notebook)
        self.notebook.add(detail_frame, text="📄 Détails")
        self.create_detail_tab(detail_frame)
        
        # Footer
        footer_frame = ttk.Frame(self.root)
        footer_frame.pack(fill='x', padx=10, pady=10)
        
        self.stats_label = ttk.Label(footer_frame, text="Tickets: 0 | Aujourd'hui: 0", 
                                     font=('Segoe UI', 9))
        self.stats_label.pack(side='left')
    
    def create_monitor_tab(self, parent):
        """Onglet de surveillance"""
        console_label = ttk.Label(parent, text="Console:", 
                                 font=('Segoe UI', 11, 'bold'))
        console_label.pack(anchor='w', padx=10, pady=(10, 5))
        
        self.console = scrolledtext.ScrolledText(parent, wrap=tk.WORD, 
                                                 height=25,
                                                 bg='#1e1e1e', fg='#00ff00',
                                                 font=('Consolas', 9),
                                                 insertbackground='white')
        self.console.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.log_message("="*70)
        self.log_message("      AD LOG MONITOR v2.0 - Recherche web intégrée")
        self.log_message("="*70)
        self.log_message(f"\n📂 Fichier: {self.log_file}")
        self.log_message(f"📁 Tickets: {self.output_dir}")
        self.log_message(f"\n💡 Click '🕐 Check 24h' pour analyser les 24 dernières heures")
        self.log_message("💡 Click '▶ Démarrer' pour la surveillance continue")
        self.log_message("💡 Système anti-doublons: 1 ticket par erreur/jour\n")
    
    def create_history_tab(self, parent):
        """Onglet historique"""
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(search_frame, text="🔍 Recherche:", font=('Segoe UI', 10)).pack(side='left', padx=5)
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        search_entry.pack(side='left', padx=5)
        search_entry.bind('<KeyRelease>', lambda e: self.filter_tickets())
        
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        columns = ('Date', 'Type', 'Source', 'Event ID', 'Ordinateur', 'Occurrences')
        self.ticket_tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', height=20)
        
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.ticket_tree.yview)
        hsb = ttk.Scrollbar(list_frame, orient="horizontal", command=self.ticket_tree.xview)
        self.ticket_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.ticket_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        self.ticket_tree.heading('#0', text='Dossier')
        self.ticket_tree.column('#0', width=250)
        
        for col in columns:
            self.ticket_tree.heading(col, text=col)
            self.ticket_tree.column(col, width=100)
        
        self.ticket_tree.bind('<Double-1>', self.open_ticket)
        
        # Charger les tickets après création de l'interface
        self.root.after(100, self.load_tickets)
    
    def create_detail_tab(self, parent):
        """Onglet détails"""
        self.detail_text = scrolledtext.ScrolledText(parent, wrap=tk.WORD,
                                                     bg='#1e1e1e', fg='#ffffff',
                                                     font=('Consolas', 10))
        self.detail_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.detail_text.insert('1.0', "Double-cliquez sur un ticket dans l'onglet Historique.")
    
    def log_message(self, message):
        """Log un message"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.console.insert(tk.END, f"[{timestamp}] {message}\n")
            self.console.see(tk.END)
            self.root.update_idletasks()
        except Exception as e:
            print(f"Erreur log: {e} - {message}")
    
    def analyze_and_create_ticket(self, event):
        """Analyse une erreur et crée un ticket"""
        try:
            web_results = self.web_searcher.search(event)
            analysis = self.ai_analyzer.analyze(event, web_results)
            
            web_links = []
            if web_results:
                for match in re.finditer(r'🔗 (https?://[^\s]+)', web_results):
                    web_links.append(match.group(1))
            
            self.ticket_manager.create_or_update_ticket(
                event, 
                analysis, 
                web_links,
                log_callback=self.log_message
            )
            
        except Exception as e:
            self.log_message(f"  ❌ Erreur: {e}")
    
    def initial_check(self):
        """Vérification 24h"""
        if not WINDOWS_EVENTS_AVAILABLE:
            messagebox.showerror("Erreur", "pywin32 requis: pip install pywin32")
            return
        
        # Vérifier l'accès au log
        try:
            test_hand = win32evtlog.OpenEventLog(None, "ForwardedEvents")
            win32evtlog.CloseEventLog(test_hand)
        except Exception as e:
            error_msg = f"""Impossible d'accéder au log 'ForwardedEvents'.

Erreur: {str(e)}

SOLUTIONS:
1. Lancez l'application en tant qu'Administrateur
2. Vérifiez que le service 'Journaux d'événements Windows' est démarré
3. Configurez le collecteur d'événements:
   - Ouvrez 'Observateur d'événements'
   - Allez dans 'Abonnements'
   - Créez un abonnement pour collecter les événements
4. Vérifiez que le fichier existe:
   {self.log_file}"""
            
            messagebox.showerror("Erreur d'accès au log", error_msg)
            self.log_message(f"❌ {error_msg}")
            return
        
        self.log_message("\n" + "="*70)
        self.log_message("🔍 VÉRIFICATION 24 HEURES - ForwardedEvents")
        self.log_message("="*70)
        thread = threading.Thread(target=self._initial_check_thread, daemon=True)
        thread.start()
    
    def _initial_check_thread(self):
        """Thread vérification"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=24)
            events = self.read_event_log(since=cutoff_time)
            
            if events:
                self.log_message(f"\n⚠️  {len(events)} erreur(s) détectée(s)\n")
                for i, event in enumerate(events, 1):
                    self.log_message(f"[{i}/{len(events)}] {event['source']} - Event {event['event_id']}")
                    self.analyze_and_create_ticket(event)
                self.save_history()
                self.root.after(0, self.refresh_tickets)
                self.log_message(f"\n✅ Terminé: {len(events)} ticket(s)\n")
            else:
                self.log_message("\n✅ Aucune erreur\n")
        except Exception as e:
            self.log_message(f"❌ Erreur: {e}\n{traceback.format_exc()}")
    
    def read_event_log(self, since=None):
        """Lit les événements du fichier ForwardedEvents.evtx"""
        if not WINDOWS_EVENTS_AVAILABLE:
            raise Exception("pywin32 requis")
        
        try:
            # Ouvrir le fichier EVTX
            # Pour un fichier .evtx, on utilise le nom du log "ForwardedEvents" 
            # ou le chemin complet du fichier
            
            # Essayer d'abord avec le nom du log
            log_name = "ForwardedEvents"
            
            try:
                hand = win32evtlog.OpenEventLog(None, log_name)
                self.log_message(f"✅ Ouverture du log '{log_name}' réussie")
            except Exception as e1:
                # Si ça échoue, essayer avec le chemin du fichier
                # Note: win32evtlog ne peut pas lire directement les fichiers .evtx
                # Il faut utiliser le nom du log système
                self.log_message(f"⚠️  Impossible d'ouvrir '{log_name}': {e1}")
                raise Exception(f"Impossible d'ouvrir le log ForwardedEvents. Vérifiez que:\n"
                              f"1. Le service 'Event Log' est démarré\n"
                              f"2. Le fichier existe: {self.log_file}\n"
                              f"3. Vous avez les droits administrateur\n"
                              f"4. Le collecteur d'événements est configuré")
            
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
            
            events = []
            total_read = 0
            
            self.log_message("📖 Lecture des événements en cours...")
            
            while True:
                try:
                    event_records = win32evtlog.ReadEventLog(hand, flags, 0)
                    if not event_records:
                        break
                    
                    for event in event_records:
                        total_read += 1
                        
                        # Filtrer uniquement les erreurs et warnings
                        if event.EventType not in [win32evtlog.EVENTLOG_ERROR_TYPE, 
                                                  win32evtlog.EVENTLOG_WARNING_TYPE]:
                            continue
                        
                        # Filtrer par date si spécifié
                        if since and event.TimeGenerated < since:
                            continue
                        
                        # Éviter les doublons
                        if not since and event.RecordNumber <= self.last_record:
                            continue
                        
                        # Extraire les données de l'événement
                        event_data = {
                            'record_number': event.RecordNumber,
                            'time_generated': event.TimeGenerated.Format(),
                            'source': event.SourceName or "Unknown",
                            'event_id': event.EventID & 0xFFFF,
                            'event_type': 'ERROR' if event.EventType == win32evtlog.EVENTLOG_ERROR_TYPE else 'WARNING',
                            'computer': event.ComputerName or "Unknown",
                            'message': win32evtlogutil.SafeFormatMessage(event, log_name) or "N/A"
                        }
                        events.append(event_data)
                        
                        # Mettre à jour le dernier record traité
                        if event.RecordNumber > self.last_record:
                            self.last_record = event.RecordNumber
                    
                    # Limiter la lecture pour éviter une surcharge
                    if total_read >= 10000:
                        self.log_message(f"⚠️  Limite de 10000 événements atteinte")
                        break
                        
                except Exception as read_error:
                    self.log_message(f"⚠️  Erreur lecture: {read_error}")
                    break
            
            win32evtlog.CloseEventLog(hand)
            self.log_message(f"📊 {total_read} événements lus, {len(events)} erreurs/warnings trouvées")
            
            return events
            
        except Exception as e:
            error_detail = f"Erreur lecture log: {str(e)}"
            self.log_message(f"❌ {error_detail}")
            raise Exception(error_detail)
    
    def start_monitoring(self):
        """Démarre la surveillance"""
        if not WINDOWS_EVENTS_AVAILABLE:
            messagebox.showerror("Erreur", "pywin32 requis")
            return
        
        # Vérifier l'accès au log
        try:
            test_hand = win32evtlog.OpenEventLog(None, "ForwardedEvents")
            win32evtlog.CloseEventLog(test_hand)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'accéder au log 'ForwardedEvents':\n{str(e)}\n\nLancez l'application en tant qu'Administrateur.")
            return
        
        self.monitoring = True
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.status_label.config(text="▶ Surveillance active", foreground='#4CAF50')
        
        self.log_message("\n🚀 SURVEILLANCE DÉMARRÉE (vérification toutes les 60s)\n")
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Arrête"""
        self.monitoring = False
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.status_label.config(text="⏹ Arrêté", foreground='#f44336')
        self.log_message("\n🛑 Arrêté\n")
    
    def _monitor_loop(self):
        """Boucle surveillance"""
        while self.monitoring:
            try:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.root.after(0, lambda t=now: self.last_check_label.config(text=f"Dernière: {t}"))
                
                events = self.read_event_log()
                
                if events:
                    self.log_message(f"\n⚠️  {len(events)} erreur(s)!")
                    for event in events:
                        self.log_message(f"  → {event['source']} - Event {event['event_id']}")
                        self.analyze_and_create_ticket(event)
                    self.save_history()
                    self.root.after(0, self.refresh_tickets)
                else:
                    self.log_message("✅ Aucune erreur")
                
                for _ in range(60):
                    if not self.monitoring:
                        break
                    threading.Event().wait(1)
                
            except Exception as e:
                self.log_message(f"❌ {e}")
                threading.Event().wait(60)
    
    def cleanup_old_tickets(self):
        """Nettoie"""
        if messagebox.askyesno("Nettoyage", "Supprimer tickets 30j+?"):
            cleaned = self.ticket_manager.cleanup_old_tickets(30)
            if cleaned:
                self.log_message(f"🧹 {cleaned} ticket(s) supprimé(s)")
                self.refresh_tickets()
            else:
                self.log_message("✅ Rien à nettoyer")
    
    def load_tickets(self):
        """Charge tickets"""
        try:
            self.ticket_tree.delete(*self.ticket_tree.get_children())
            
            if not os.path.exists(self.output_dir):
                return
            
            total = 0
            today_count = 0
            today = datetime.now().date()
            
            for folder in sorted(os.listdir(self.output_dir)):
                folder_path = os.path.join(self.output_dir, folder)
                if not os.path.isdir(folder_path) or folder.startswith('.'):
                    continue
                
                folder_id = self.ticket_tree.insert('', 'end', text=folder, open=False)
                
                tickets = [f for f in os.listdir(folder_path) if f.startswith('ticket_')]
                tickets.sort(reverse=True)
                
                for ticket in tickets:
                    ticket_path = os.path.join(folder_path, ticket)
                    total += 1
                    
                    try:
                        with open(ticket_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        date_match = re.search(r'📅 CRÉÉ LE: (.+)', content)
                        type_match = re.search(r'⚠️  TYPE: (.+)', content)
                        source_match = re.search(r'Source: (.+)', content)
                        event_id_match = re.search(r'Event ID: (\d+)', content)
                        computer_match = re.search(r'Ordinateur: (.+)', content)
                        occ_match = re.search(r'🔢 OCCURRENCES: (\d+)', content)
                        
                        date_str = date_match.group(1) if date_match else 'N/A'
                        type_str = type_match.group(1) if type_match else 'N/A'
                        source_str = source_match.group(1) if source_match else 'N/A'
                        event_id = event_id_match.group(1) if event_id_match else 'N/A'
                        computer = computer_match.group(1) if computer_match else 'N/A'
                        occ = occ_match.group(1) if occ_match else '1'
                        
                        file_date = datetime.fromtimestamp(os.path.getmtime(ticket_path)).date()
                        if file_date == today:
                            today_count += 1
                        
                        self.ticket_tree.insert(folder_id, 'end', text=ticket,
                                              values=(date_str, type_str, source_str, event_id, computer, occ),
                                              tags=(ticket_path,))
                    except Exception as e:
                        print(f"Erreur lecture ticket {ticket}: {e}")
                        continue
            
            self.stats_label.config(text=f"Tickets: {total} | Aujourd'hui: {today_count}")
        except Exception as e:
            print(f"Erreur chargement tickets: {e}")
            self.log_message(f"⚠️ Erreur chargement tickets: {e}")
    
    def filter_tickets(self):
        """Filtre"""
        search = self.search_var.get().lower()
        for item in self.ticket_tree.get_children():
            self._filter_item(item, search)
    
    def _filter_item(self, item, search):
        """Filtre récursif"""
        text = self.ticket_tree.item(item, 'text').lower()
        values = ' '.join([str(v).lower() for v in self.ticket_tree.item(item, 'values')])
        
        match = search in text or search in values
        children_match = any(self._filter_item(c, search) for c in self.ticket_tree.get_children(item))
        
        if match or children_match or not search:
            self.ticket_tree.reattach(item, '', 'end')
            return True
        else:
            self.ticket_tree.detach(item)
            return False
    
    def open_ticket(self, event):
        """Ouvre ticket"""
        selection = self.ticket_tree.selection()
        if not selection:
            return
        
        tags = self.ticket_tree.item(selection[0], 'tags')
        if tags:
            ticket_path = tags[0]
            if os.path.isfile(ticket_path):
                try:
                    with open(ticket_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    self.detail_text.delete('1.0', tk.END)
                    self.detail_text.insert('1.0', content)
                    self.notebook.select(2)
                except Exception as e:
                    messagebox.showerror("Erreur", f"Impossible d'ouvrir:\n{e}")
    
    def refresh_tickets(self):
        """Rafraîchit"""
        self.load_tickets()
        self.log_message("🔄 Rafraîchi")


def main():
    """Point d'entrée principal avec gestion d'erreur globale"""
    try:
        root = tk.Tk()
        app = ADMonitorGUI(root)
        root.mainloop()
    except Exception as e:
        error_msg = f"ERREUR FATALE:\n{str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)
        
        # Essayer d'afficher une messagebox
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Erreur Fatale", error_msg)
        except:
            pass
        
        input("\nAppuyez sur Entrée pour fermer...")


if __name__ == "__main__":
    main()