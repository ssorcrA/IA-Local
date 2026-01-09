"""
Gestionnaire de tickets avec STRUCTURE CORRECTE
Fichier : ticket_manager.py - VERSION CORRIGÉE
CORRECTIF: Catégorie > Event_ID > Tickets
"""
import os
import json
import re
from datetime import datetime, timedelta, date
from config import OUTPUT_DIR, CLEANUP_DAYS


class TicketManager:
    """Gère les tickets avec organisation : Catégorie/Event_ID/tickets"""
    
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
            'keywords': ['192.168.1.254', '192.168.10.254', 'Stormshield', 'firewall', 'utm'],
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
    
    def __init__(self, output_dir=OUTPUT_DIR):
        self.output_dir = output_dir
        self.ticket_index_file = os.path.join(output_dir, ".ticket_index.json")
        self.load_index()
        self.ensure_category_directories()
    
    def ensure_category_directories(self):
        """Crée les dossiers pour chaque catégorie"""
        for category in self.DEVICE_CATEGORIES.keys():
            category_path = os.path.join(self.output_dir, category)
            os.makedirs(category_path, exist_ok=True)
    
    def detect_category(self, event):
        """Détecte la catégorie d'un événement"""
        source = event.get('source', '').lower()
        computer = event.get('computer', '').lower()
        message = event.get('message', '').lower()
        
        full_text = f"{source} {computer} {message}"
        
        for category, info in self.DEVICE_CATEGORIES.items():
            if category == 'Autres':
                continue
            
            for keyword in info['keywords']:
                if keyword.lower() in full_text:
                    return category
        
        return 'Autres'
    
    def load_index(self):
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
        try:
            with open(self.ticket_index_file, 'w', encoding='utf-8') as f:
                json.dump(self.ticket_index, f, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde index: {e}")
    
    def get_ticket_key(self, event):
        """Génère une clé unique basée sur source + event_id + date"""
        category = self.detect_category(event)
        source = re.sub(r'[^\w\-_]', '_', event['source'])
        return f"{category}_{source}_{event['event_id']}_{date.today().isoformat()}"
    
    def get_priority_emoji(self, priority):
        if priority >= 9:
            return "🔴"
        elif priority >= 7:
            return "🟠"
        elif priority >= 5:
            return "🟡"
        elif priority >= 3:
            return "🟢"
        else:
            return "⚪"
    
    def get_priority_label(self, priority):
        emoji = self.get_priority_emoji(priority)
        if priority == 10:
            return f"{emoji} CRITIQUE 10/10"
        elif priority == 9:
            return f"{emoji} CRITIQUE 9/10"
        elif priority == 8:
            return f"🟠 HAUTE 8/10"
        elif priority == 7:
            return f"🟠 HAUTE 7/10"
        elif priority == 6:
            return f"🟡 MOYENNE 6/10"
        elif priority == 5:
            return f"🟡 MOYENNE 5/10"
        elif priority == 4:
            return f"🟢 BASSE 4/10"
        elif priority == 3:
            return f"🟢 BASSE 3/10"
        elif priority == 2:
            return f"🔵 INFO 2/10"
        else:
            return f"⚪ MINIMAL 1/10"
    
    def find_existing_ticket(self, event):
        """Cherche un ticket existant pour cet événement"""
        ticket_key = self.get_ticket_key(event)
        
        if ticket_key in self.ticket_index:
            ticket_path = self.ticket_index[ticket_key]
            if os.path.exists(ticket_path):
                return ticket_path
        
        return None
    
    def create_or_update_ticket(self, event, analysis, web_links, log_callback=None):
        """Crée ou met à jour un ticket"""
        existing_ticket = self.find_existing_ticket(event)
        
        if existing_ticket:
            return self.update_existing_ticket(existing_ticket, event, log_callback)
        else:
            return self.create_new_ticket(event, analysis, web_links, log_callback)
    
    def create_new_ticket(self, event, analysis, web_links, log_callback=None):
        """Crée un nouveau ticket - STRUCTURE CORRECTE"""
        try:
            # Détection de catégorie
            category = self.detect_category(event)
            category_info = self.DEVICE_CATEGORIES[category]
            
            # STRUCTURE: Catégorie > Event_ID > Tickets
            category_dir = os.path.join(self.output_dir, category)
            event_id_dir = os.path.join(category_dir, f"Event_{event['event_id']}")
            os.makedirs(event_id_dir, exist_ok=True)
            
            # Nom du fichier avec date et source
            today = date.today().isoformat()
            safe_source = re.sub(r'[^\w\-_]', '_', event['source'])[:30]
            
            ticket_file = os.path.join(
                event_id_dir,
                f"ticket_{today}_{safe_source}.txt"
            )
            
            # Informations
            grouped_count = event.get('_grouped_count', 1)
            affected_computers = event.get('_affected_computers', [event['computer']])
            priority = event.get('_priority', 5) + category_info['priority_boost']
            priority = min(priority, 10)
            
            priority_label = self.get_priority_label(priority)
            priority_emoji = self.get_priority_emoji(priority)
            
            # Section ressources web
            web_section = ""
            if web_links:
                web_section = "\n🌐 RESSOURCES WEB:\n"
                for i, link in enumerate(web_links, 1):
                    web_section += f"  [{i}] {link}\n"
            
            # Section ordinateurs
            computers_section = "\n💻 ORDINATEURS AFFECTÉS:\n"
            for i, computer in enumerate(affected_computers, 1):
                computers_section += f"  [{i}] {computer}\n"
            
            # Statut
            if priority >= 9:
                status = "🔴 CRITIQUE - ACTION IMMÉDIATE REQUISE"
            elif priority >= 7:
                status = "🟠 HAUTE - ACTION RAPIDE RECOMMANDÉE"
            elif priority >= 5:
                status = "🟡 MOYENNE - SURVEILLANCE NÉCESSAIRE"
            else:
                status = "🟢 BASSE - INFORMATION"
            
            content = f"""╔═══════════════════════════════════════════════════════════╗
║     {category_info['icon']} {category.upper()} - {priority_emoji} {priority_label}     ║
╚═══════════════════════════════════════════════════════════╝

📅 CRÉÉ LE: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
📊 OCCURRENCES: {grouped_count}
🔢 MACHINES AFFECTÉES: {len(affected_computers)}
⚠️ TYPE: {event['event_type']}
🎯 PRIORITÉ: {priority_label}
📌 STATUT: {status}
🏷️ CATÉGORIE: {category_info['icon']} {category}

───────────────────────────────────────────────────────────

📊 INFORMATIONS TECHNIQUES:
  • Source: {event['source']}
  • Event ID: {event['event_id']}
  • Première détection: {event['time_generated']}
{computers_section}
───────────────────────────────────────────────────────────

📄 MESSAGE D'ERREUR:
{event['message'][:500]}...

───────────────────────────────────────────────────────────

📜 HISTORIQUE DES OCCURRENCES:

[1] {event['time_generated']} - Record #{event['record_number']}
    Computer: {event['computer']}
    Message: {event['message'][:200]}...

───────────────────────────────────────────────────────────

🤖 ANALYSE & SOLUTION:
{analysis}
{web_section}
───────────────────────────────────────────────────────────

📋 ACTIONS RECOMMANDÉES:
"""
            
            if priority >= 9:
                content += """  1. ⚠️ BLOQUER IMMÉDIATEMENT l'accès si nécessaire
  2. 🔍 INVESTIGUER en urgence la source
  3. 📞 ALERTER l'équipe de sécurité
  4. 📋 DOCUMENTER tous les détails
  5. 🛡️ APPLIQUER les correctifs de sécurité
"""
            elif priority >= 7:
                content += """  1. 🔍 ANALYSER rapidement la situation
  2. 🛠️ APPLIQUER les solutions proposées
  3. 📊 SURVEILLER l'évolution
  4. 📝 DOCUMENTER les actions prises
"""
            elif priority >= 5:
                content += """  1. 📋 PLANIFIER une intervention
  2. 🔍 VÉRIFIER si le problème persiste
  3. 🛠️ APPLIQUER les correctifs recommandés
"""
            else:
                content += """  1. 📊 MONITORER la situation
  2. 📝 NOTER pour référence future
  3. ✅ APPLIQUER si temps disponible
"""
            
            content += f"""
───────────────────────────────────────────────────────────

📌 STATUT ACTUEL: NOUVEAU
🔔 NÉCESSITE ACTION: {"OUI - URGENT" if priority >= 7 else "OUI" if priority >= 5 else "SURVEILLANCE"}
⏰ DERNIÈRE MISE À JOUR: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
📈 TENDANCE: NOUVELLE DÉTECTION

═══════════════════════════════════════════════════════════
"""
            
            with open(ticket_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Indexer
            ticket_key = self.get_ticket_key(event)
            self.ticket_index[ticket_key] = ticket_file
            self.save_index()
            
            if log_callback:
                if grouped_count > 1:
                    log_callback(f"  ✅ Ticket groupé créé: {category}/Event_{event['event_id']}")
                else:
                    log_callback(f"  ✅ Nouveau ticket: {category}/Event_{event['event_id']}/{os.path.basename(ticket_file)}")
            
            return ticket_file
            
        except Exception as e:
            if log_callback:
                log_callback(f"  ❌ Erreur création ticket: {e}")
            return None
    
    def update_existing_ticket(self, ticket_path, event, log_callback=None):
        """Met à jour un ticket existant"""
        try:
            with open(ticket_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Incrémenter occurrences
            occurrence_match = re.search(r'📊 OCCURRENCES: (\d+)', content)
            current_count = int(occurrence_match.group(1)) if occurrence_match else 1
            new_count = current_count + 1
            
            content = re.sub(
                r'📊 OCCURRENCES: \d+',
                f'📊 OCCURRENCES: {new_count}',
                content
            )
            
            # Ajouter PC si nécessaire
            computers_section = re.search(r'💻 ORDINATEURS AFFECTÉS:\n(.*?)\n───', content, re.DOTALL)
            if computers_section and event['computer'] not in computers_section.group(1):
                machines_count = len(re.findall(r'\[\d+\]', computers_section.group(1)))
                new_machines_count = machines_count + 1
                
                new_computer_line = f"  [{new_machines_count}] {event['computer']}\n"
                content = content.replace(
                    computers_section.group(0),
                    computers_section.group(0).replace('\n───', f"{new_computer_line}\n───")
                )
                
                content = re.sub(
                    r'🔢 MACHINES AFFECTÉES: \d+',
                    f'🔢 MACHINES AFFECTÉES: {new_machines_count}',
                    content
                )
            
            # Ajouter dans historique
            new_occurrence = f"\n[{new_count}] {event['time_generated']} - Record #{event['record_number']}\n    Computer: {event['computer']}\n    Message: {event['message'][:200]}...\n"
            
            history_marker = "📜 HISTORIQUE DES OCCURRENCES:"
            if history_marker in content:
                parts = content.split("───────────────────────────────────────────────────────────")
                
                for i, part in enumerate(parts):
                    if history_marker in part:
                        parts[i] = part + new_occurrence
                        break
                
                content = "───────────────────────────────────────────────────────────".join(parts)
            
            # MAJ heure
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            content = re.sub(
                r'⏰ DERNIÈRE MISE À JOUR: .+',
                f'⏰ DERNIÈRE MISE À JOUR: {now}',
                content
            )
            
            # MAJ tendance
            if new_count >= 10:
                trend = "EN AUGMENTATION RAPIDE ⚠️"
            elif new_count >= 5:
                trend = "EN AUGMENTATION"
            else:
                trend = "STABLE"
            
            content = re.sub(
                r'📈 TENDANCE: .+',
                f'📈 TENDANCE: {trend} ({new_count} occurrences)',
                content
            )
            
            with open(ticket_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            if log_callback:
                log_callback(f"  🔄 Ticket mis à jour: {new_count} occurrence(s)")
            
            return ticket_path
            
        except Exception as e:
            if log_callback:
                log_callback(f"  ❌ Erreur mise à jour ticket: {e}")
            return None
    
    def cleanup_old_tickets(self, days=CLEANUP_DAYS):
        """Nettoie les vieux tickets"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            cleaned = 0
            
            # Parcourir chaque catégorie
            for category in self.DEVICE_CATEGORIES.keys():
                category_path = os.path.join(self.output_dir, category)
                if not os.path.exists(category_path):
                    continue
                
                # Parcourir chaque Event_ID
                for event_folder in os.listdir(category_path):
                    event_path = os.path.join(category_path, event_folder)
                    
                    if not os.path.isdir(event_path):
                        continue
                    
                    # Parcourir les tickets
                    for ticket_file in os.listdir(event_path):
                        if not ticket_file.startswith('ticket_'):
                            continue
                        
                        ticket_path = os.path.join(event_path, ticket_file)
                        
                        if not os.path.isfile(ticket_path):
                            continue
                        
                        file_date = datetime.fromtimestamp(os.path.getmtime(ticket_path))
                        
                        if file_date < cutoff_date:
                            os.remove(ticket_path)
                            cleaned += 1
                    
                    # Supprimer dossier Event_ID vide
                    if not os.listdir(event_path):
                        os.rmdir(event_path)
            
            # Nettoyer index
            self.ticket_index = {
                k: v for k, v in self.ticket_index.items()
                if os.path.exists(v)
            }
            self.save_index()
            
            return cleaned
            
        except Exception as e:
            print(f"Erreur nettoyage: {e}")
            return 0