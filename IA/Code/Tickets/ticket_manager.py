"""
TICKET MANAGER - DÉTECTION DOUBLONS 30 MINUTES
Fichier : ticket_manager.py - VERSION AVEC FENÊTRE 30 MIN

✅ CORRECTIFS :
1. Fenêtre fixe de 30 minutes pour TOUS les doublons
2. Clé précise : device_name + event_id + severity
3. Vérification AVANT tout traitement
4. Nettoyage automatique du cache
"""
import os
import json
import re
from datetime import datetime, timedelta, date
from config import OUTPUT_DIR, CLEANUP_DAYS
from device_detector import DeviceDetector


class TicketManager:
    # 🔥 FENÊTRE FIXE : 30 MINUTES POUR TOUS
    DUPLICATE_WINDOW_MINUTES = 30
    
    def __init__(self, output_dir=OUTPUT_DIR):
        self.output_dir = output_dir
        self.ticket_index_file = os.path.join(output_dir, ".ticket_index.json")
        self.recent_tickets_file = os.path.join(output_dir, ".recent_tickets.json")
        
        self.load_index()
        self.load_recent_tickets()
        self.ensure_device_directories()
        
        # Stats
        self.stats_created = 0
        self.stats_updated = 0
        self.stats_duplicates = 0
    
    def ensure_device_directories(self):
        """Crée dossiers d'appareils"""
        devices = DeviceDetector.get_all_devices()
        
        for device in devices:
            folder_name = device['folder']
            device_path = os.path.join(self.output_dir, folder_name)
            os.makedirs(device_path, exist_ok=True)
        
        os.makedirs(os.path.join(self.output_dir, 'Autres'), exist_ok=True)
    
    def load_recent_tickets(self):
        """
        🔥 CHARGE TICKETS RÉCENTS (30 minutes)
        Nettoyage automatique des anciennes entrées
        """
        try:
            if os.path.exists(self.recent_tickets_file):
                with open(self.recent_tickets_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Garder seulement les 30 dernières minutes
                    cutoff = datetime.now() - timedelta(minutes=self.DUPLICATE_WINDOW_MINUTES)
                    
                    self.recent_tickets = {
                        k: v for k, v in data.items()
                        if datetime.fromisoformat(v['timestamp']) > cutoff
                    }
            else:
                self.recent_tickets = {}
        except:
            self.recent_tickets = {}
    
    def save_recent_tickets(self):
        """Sauvegarde tickets récents"""
        try:
            # Nettoyer avant sauvegarde
            cutoff = datetime.now() - timedelta(minutes=self.DUPLICATE_WINDOW_MINUTES)
            
            self.recent_tickets = {
                k: v for k, v in self.recent_tickets.items()
                if datetime.fromisoformat(v['timestamp']) > cutoff
            }
            
            with open(self.recent_tickets_file, 'w', encoding='utf-8') as f:
                json.dump(self.recent_tickets, f, indent=2)
        except:
            pass
    
    def is_duplicate_within_timewindow(self, event):
        """
        🔥 VÉRIFICATION DOUBLON - FENÊTRE FIXE 30 MIN
        
        Clé : device_name + event_id + severity
        Fenêtre : TOUJOURS 30 minutes (fixe)
        
        Returns:
            True si doublon détecté (< 30 min)
            False sinon
        """
        device_info, device_ip = DeviceDetector.detect_from_event(event)
        
        if not device_info:
            return False
        
        device_name = device_info['name']
        event_id = event.get('event_id', 0)
        severity = event.get('_severity', 'unknown').lower()
        
        # 🔥 CLÉ PRÉCISE
        dedup_key = f"{device_name}_{event_id}_{severity}"
        
        # 🔥 FENÊTRE FIXE : 30 MINUTES
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(minutes=self.DUPLICATE_WINDOW_MINUTES)
        
        # Nettoyer anciennes entrées
        keys_to_remove = []
        for key, data in self.recent_tickets.items():
            timestamp = datetime.fromisoformat(data['timestamp'])
            if timestamp < cutoff_time:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.recent_tickets[key]
        
        # Vérifier si doublon
        if dedup_key in self.recent_tickets:
            last_time = datetime.fromisoformat(self.recent_tickets[dedup_key]['timestamp'])
            time_diff = (current_time - last_time).total_seconds() / 60
            
            if time_diff < self.DUPLICATE_WINDOW_MINUTES:
                # 🔥 DOUBLON DÉTECTÉ
                self.stats_duplicates += 1
                return True
        
        # ✅ Pas de doublon
        return False
    
    def mark_ticket_recent(self, event, ticket_path):
        """
        🔥 MARQUE TICKET COMME RÉCENT
        Enregistre dans le cache avec timestamp
        """
        device_info, device_ip = DeviceDetector.detect_from_event(event)
        
        if not device_info:
            return
        
        device_name = device_info['name']
        event_id = event.get('event_id', 0)
        severity = event.get('_severity', 'unknown').lower()
        
        dedup_key = f"{device_name}_{event_id}_{severity}"
        
        self.recent_tickets[dedup_key] = {
            'timestamp': datetime.now().isoformat(),
            'event_id': event_id,
            'device': device_name,
            'ip': device_ip,
            'severity': severity,
            'path': ticket_path
        }
        
        self.save_recent_tickets()
    
    def detect_device_from_event(self, event):
        """Détection appareil - RETOURNE LE FOLDER"""
        device_info, device_ip = DeviceDetector.detect_from_event(event)
        
        if device_info:
            return device_info['folder']
        
        return 'Autres'
    
    def get_ticket_key(self, event):
        """Clé unique ticket pour index (par jour)"""
        device_folder = self.detect_device_from_event(event)
        event_id = event.get('event_id', 0)
        severity = event.get('_severity', 'unknown')
        today = date.today().isoformat()
        return f"{device_folder}_{event_id}_{severity}_{today}"
    
    def load_index(self):
        """Charge index"""
        try:
            if os.path.exists(self.ticket_index_file):
                with open(self.ticket_index_file, 'r', encoding='utf-8') as f:
                    self.ticket_index = json.load(f)
            else:
                self.ticket_index = {}
        except:
            self.ticket_index = {}
    
    def save_index(self):
        """Sauvegarde index"""
        try:
            with open(self.ticket_index_file, 'w', encoding='utf-8') as f:
                json.dump(self.ticket_index, f, indent=2)
        except:
            pass
    
    def get_priority_emoji(self, priority):
        """Emoji priorité"""
        if priority >= 9:
            return "🔴"
        elif priority >= 7:
            return "🟠"
        elif priority >= 5:
            return "🟡"
        else:
            return "🟢"
    
    def get_priority_label(self, priority):
        """Label priorité"""
        emoji = self.get_priority_emoji(priority)
        labels = {
            10: f"{emoji} CRITIQUE 10/10", 
            9: f"{emoji} CRITIQUE 9/10",
            8: f"🟠 HAUTE 8/10", 
            7: f"🟠 HAUTE 7/10",
            6: f"🟡 MOYENNE 6/10", 
            5: f"🟡 MOYENNE 5/10",
            4: f"🟢 BASSE 4/10",
        }
        return labels.get(priority, f"🟢 BASSE {priority}/10")
    
    def find_existing_ticket(self, event):
        """Trouve ticket existant du jour"""
        ticket_key = self.get_ticket_key(event)
        if ticket_key in self.ticket_index:
            ticket_path = self.ticket_index[ticket_key]
            if os.path.exists(ticket_path):
                return ticket_path
        return None
    
    def create_or_update_ticket(self, event, analysis, web_links, log_callback=None):
        """
        🔥 CRÉATION/MAJ AVEC VÉRIFICATION DOUBLON 30 MIN
        
        ÉTAPES :
        1. Vérifier doublon < 30 min → RETOUR SILENCIEUX
        2. Chercher ticket existant du jour → MAJ
        3. Sinon → CRÉER nouveau
        
        Returns:
            (success: bool, is_new: bool)
        """
        
        # 🔥 ÉTAPE 1 : VÉRIFIER DOUBLON (< 30 MIN)
        is_duplicate = self.is_duplicate_within_timewindow(event)
        
        if is_duplicate:
            # ✅ RETOUR SILENCIEUX - Doublon détecté
            return False, False
        
        # 🔥 ÉTAPE 2 : CHERCHER TICKET DU JOUR
        existing_ticket = self.find_existing_ticket(event)
        
        if existing_ticket:
            # Mettre à jour ticket existant
            if log_callback:
                ticket_name = os.path.basename(existing_ticket)
                log_callback(f"  📝 MAJ ticket existant : {ticket_name}")
            
            self.stats_updated += 1
            success = self.update_existing_ticket(existing_ticket, event, log_callback)
            
            if success:
                self.mark_ticket_recent(event, existing_ticket)
                
                if log_callback:
                    log_callback(f"  📂 Chemin : {existing_ticket}")
            
            return success, False  # ✅ Succès, pas nouveau
        
        else:
            # 🔥 ÉTAPE 3 : CRÉER NOUVEAU TICKET
            if log_callback:
                log_callback(f"  ✨ Création nouveau ticket")
            
            self.stats_created += 1
            ticket_path = self.create_new_ticket(event, analysis, web_links, log_callback)
            success = ticket_path is not None
            
            if success:
                self.mark_ticket_recent(event, ticket_path)
                
                if log_callback:
                    ticket_name = os.path.basename(ticket_path)
                    log_callback(f"  ✅ Ticket créé : {ticket_name}")
                    log_callback(f"  📂 Chemin : {ticket_path}")
            
            return success, True  # ✅ Succès, nouveau
    
    def create_new_ticket(self, event, analysis, web_links, log_callback=None):
        """Crée nouveau ticket"""
        try:
            # Détection device complète
            device_info, device_ip = DeviceDetector.detect_from_event(event)
            
            if device_info:
                device_folder = device_info['folder']
                device_icon = device_info['icon']
                device_name = device_info['name']
                device_full_name = device_info['full_name']
                device_description = device_info['description']
            else:
                device_folder = 'Autres'
                device_icon = '❓'
                device_name = 'Inconnu'
                device_full_name = 'Appareil non identifié'
                device_description = 'Source inconnue'
                device_ip = event.get('computer', 'N/A')
            
            device_path = os.path.join(self.output_dir, device_folder)
            os.makedirs(device_path, exist_ok=True)
            
            error_type = f"Event_{event.get('event_id', 0)}"
            error_type_path = os.path.join(device_path, error_type)
            os.makedirs(error_type_path, exist_ok=True)
            
            severity = event.get('_severity', 'unknown')
            today = date.today().isoformat()
            ticket_file = os.path.join(error_type_path, f"ticket_{today}_{severity}.txt")
            
            priority = event.get('_priority', 5)
            priority_label = self.get_priority_label(priority)
            priority_emoji = self.get_priority_emoji(priority)
            
            web_section = ""
            if web_links:
                web_section = "\n🌐 RESSOURCES WEB:\n"
                for i, link in enumerate(web_links, 1):
                    web_section += f"  [{i}] {link}\n"
            
            if priority >= 9:
                status = "🔴 CRITIQUE - ACTION IMMÉDIATE"
            elif priority >= 7:
                status = "🟠 HAUTE - ACTION RAPIDE"
            else:
                status = "🟡 SURVEILLANCE"
            
            if event.get('_is_syslog'):
                source_type = "Syslog (Réseau)"
                device_type_display = event.get('_device_type', 'network').upper()
            else:
                source_type = "Windows Event"
                device_type_display = "WINDOWS"
            
            source_display = f"{device_full_name} ({device_ip})"
            
            content = f"""╔═══════════════════════════════════╗
║  {device_icon} {device_folder.upper()} - {priority_emoji} {priority_label}  ║
╚═══════════════════════════════════╝

📅 CRÉÉ: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
📊 OCCURRENCES: 1
🎯 PRIORITÉ: {priority_label}
📌 STATUT: {status}

╔═══════════════════════════════════╗
║  IDENTIFICATION DE L'APPAREIL         ║
╚═══════════════════════════════════╝

{device_icon} APPAREIL: {device_full_name}
🔢 IP: {device_ip}
🏷️ NOM COURT: {device_name}
📂 DOSSIER: {device_folder}
📝 DESCRIPTION: {device_description}
🔧 TYPE: {device_type_display}

╔═══════════════════════════════════╗
║  DÉTAILS DE L'INCIDENT                ║
╚═══════════════════════════════════╝

📡 SOURCE: {source_display}
📋 TYPE: {source_type}
🆔 EVENT ID: {event['event_id']}
⚠️ CATÉGORIE: {event['event_type']}
🔢 SEVERITY: {severity.upper()}
📅 DÉTECTION: {event['time_generated']}

────────────────────────────────────────────────────────────────────────────────

📄 MESSAGE:
{event['message'][:500]}{'...' if len(event['message']) > 500 else ''}

────────────────────────────────────────────────────────────────────────────────

🤖 ANALYSE IA:
{analysis}
{web_section}
────────────────────────────────────────────────────────────────────────────────

⏰ MAJ: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
            
            with open(ticket_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            ticket_key = self.get_ticket_key(event)
            self.ticket_index[ticket_key] = ticket_file
            self.save_index()
            
            return ticket_file
            
        except Exception as e:
            if log_callback:
                log_callback(f"  ❌ Erreur création: {e}", "error")
            return None
    
    def update_existing_ticket(self, ticket_path, event, log_callback=None):
        """MAJ ticket existant"""
        try:
            with open(ticket_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            occurrence_match = re.search(r'📊 OCCURRENCES: (\d+)', content)
            current_count = int(occurrence_match.group(1)) if occurrence_match else 1
            new_count = current_count + 1
            
            content = re.sub(
                r'📊 OCCURRENCES: \d+', 
                f'📊 OCCURRENCES: {new_count}', 
                content
            )
            
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            content = re.sub(r'⏰ MAJ: .+', f'⏰ MAJ: {now}', content)
            
            with open(ticket_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            if log_callback:
                log_callback(f"  ❌ Erreur MAJ: {e}", "error")
            return False
    
    def cleanup_old_tickets(self, days=CLEANUP_DAYS):
        """Nettoie vieux tickets"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            cleaned = 0
            
            for device_folder in os.listdir(self.output_dir):
                device_path = os.path.join(self.output_dir, device_folder)
                if not os.path.isdir(device_path) or device_folder.startswith('.'):
                    continue
                
                for error_type_folder in os.listdir(device_path):
                    error_type_path = os.path.join(device_path, error_type_folder)
                    if not os.path.isdir(error_type_path):
                        continue
                    
                    for ticket_file in os.listdir(error_type_path):
                        if not ticket_file.startswith('ticket_'):
                            continue
                        
                        ticket_path = os.path.join(error_type_path, ticket_file)
                        if not os.path.isfile(ticket_path):
                            continue
                        
                        file_date = datetime.fromtimestamp(os.path.getmtime(ticket_path))
                        if file_date < cutoff_date:
                            os.remove(ticket_path)
                            cleaned += 1
                    
                    if not os.listdir(error_type_path):
                        os.rmdir(error_type_path)
            
            self.ticket_index = {
                k: v for k, v in self.ticket_index.items() 
                if os.path.exists(v)
            }
            self.save_index()
            
            return cleaned
            
        except Exception as e:
            print(f"Erreur nettoyage: {e}")
            return 0
    
    def get_stats(self):
        """
        🔥 STATS AVEC DOUBLONS
        """
        return {
            'created': self.stats_created,
            'updated': self.stats_updated,
            'duplicates_ignored': self.stats_duplicates,
            'total': self.stats_created + self.stats_updated
        }
    
    def reset_stats(self):
        """Reset stats"""
        self.stats_created = 0
        self.stats_updated = 0
        self.stats_duplicates = 0