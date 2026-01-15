"""
TICKET MANAGER - AVEC DÉTECTION DOUBLONS 30 MINUTES
Fichier : ticket_manager.py - VERSION FINALE CORRIGÉE
🔥 CORRECTIF : Retourne TOUJOURS (success: bool, is_new: bool)
"""
import os
import json
import re
import hashlib
from datetime import datetime, timedelta, date
from config import OUTPUT_DIR, CLEANUP_DAYS


class TicketManager:
    def __init__(self, output_dir=OUTPUT_DIR):
        self.output_dir = output_dir
        self.ticket_index_file = os.path.join(output_dir, ".ticket_index.json")
        self.recent_tickets_file = os.path.join(output_dir, ".recent_tickets.json")
        
        self.load_index()
        self.load_recent_tickets()
        self.ensure_device_directories()
        
        self.stats_created = 0
        self.stats_updated = 0
    
    def ensure_device_directories(self):
        """Crée tous les dossiers d'appareils"""
        devices = [
            'Serveur AD', 
            'Serveur IA', 
            'Stormshield',
            'Switch Principal', 
            'Switch Secondaire',
            'Borne WiFi', 
            'Autres'
        ]
        for device in devices:
            device_path = os.path.join(self.output_dir, device)
            os.makedirs(device_path, exist_ok=True)
    
    def load_recent_tickets(self):
        """🔥 Charge les tickets récents (pour détection doublons)"""
        try:
            if os.path.exists(self.recent_tickets_file):
                with open(self.recent_tickets_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Nettoyer les tickets de plus de 30 minutes
                    cutoff = datetime.now() - timedelta(minutes=30)
                    self.recent_tickets = {
                        k: v for k, v in data.items()
                        if datetime.fromisoformat(v['timestamp']) > cutoff
                    }
            else:
                self.recent_tickets = {}
        except:
            self.recent_tickets = {}
    
    def save_recent_tickets(self):
        """🔥 Sauvegarde les tickets récents"""
        try:
            with open(self.recent_tickets_file, 'w', encoding='utf-8') as f:
                json.dump(self.recent_tickets, f, indent=2)
        except:
            pass
    
    def is_duplicate_within_30min(self, event):
        """
        🔥 DÉTECTION DOUBLON - 30 MINUTES
        Retourne True si même nom événement + < 30 min
        """
        device = self.detect_device_from_source(event)
        event_name = self.get_event_name_for_dedup(event)
        
        # Clé unique: appareil + nom événement
        dedup_key = f"{device}_{event_name}"
        
        if dedup_key in self.recent_tickets:
            last_time = datetime.fromisoformat(self.recent_tickets[dedup_key]['timestamp'])
            time_diff = (datetime.now() - last_time).total_seconds() / 60  # en minutes
            
            if time_diff < 30:
                # C'est un doublon
                return True, time_diff
        
        return False, 0
    
    def mark_ticket_recent(self, event):
        """🔥 Marque un ticket comme récent"""
        device = self.detect_device_from_source(event)
        event_name = self.get_event_name_for_dedup(event)
        
        dedup_key = f"{device}_{event_name}"
        
        self.recent_tickets[dedup_key] = {
            'timestamp': datetime.now().isoformat(),
            'event_id': event.get('event_id', 0),
            'device': device
        }
        
        self.save_recent_tickets()
    
    def get_event_name_for_dedup(self, event):
        """
        🔥 Génère un nom d'événement pour détection doublons
        Basé sur Event ID + mots-clés principaux du message
        """
        event_id = event.get('event_id', 0)
        message = event.get('message', '').lower()
        
        # Extraire les mots-clés significatifs (sans les détails variables)
        # Retirer IPs, timestamps, nombres
        message_clean = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', '', message)
        message_clean = re.sub(r'\d{4}-\d{2}-\d{2}', '', message_clean)
        message_clean = re.sub(r'\d{2}:\d{2}:\d{2}', '', message_clean)
        message_clean = re.sub(r'\b\d+\b', '', message_clean)
        
        # Extraire mots significatifs (> 4 lettres)
        words = re.findall(r'\b[a-z]{4,}\b', message_clean)
        # Garder les 5 premiers mots significatifs
        keywords = '_'.join(words[:5]) if words else 'generic'
        
        return f"Event_{event_id}_{keywords}"
    
    def should_force_ticket_creation(self, event):
        """
        🔥 RÈGLE STORMSHIELD/BORNE WIFI
        ALERT et WARNING = ticket automatique (sauf doublon 30 min)
        """
        device = self.detect_device_from_source(event)
        severity = event.get('_severity', '').lower()
        
        # 🔥 Appareils concernés
        if device not in ['Stormshield', 'Borne WiFi']:
            return False
        
        # 🔥 Severities concernées
        if severity not in ['alert', 'warning', 'error', 'critical', 'emergency']:
            return False
        
        # 🔥 Vérifier si doublon récent
        is_dup, time_diff = self.is_duplicate_within_30min(event)
        
        if is_dup:
            # C'est un doublon récent, ne pas créer de ticket
            return False
        
        # OK pour créer un ticket
        return True
    
    def detect_device_from_source(self, event):
        """
        🔥 DÉTECTION APPAREIL - VERSION ROBUSTE COMPLÈTE
        Priorité : IP > Computer > Source > Device_name > Analyse message
        """
        
        # 🔥 ÉTAPE 1 : IP DIRECTE (la plus fiable)
        device_ip = event.get('_device_ip', '').strip()
        
        ip_to_device = {
            '192.168.10.254': 'Stormshield',
            '192.168.10.11': 'Borne WiFi',
            '192.168.10.15': 'Switch Principal',
            '192.168.10.16': 'Switch Secondaire',
            '192.168.10.10': 'Serveur AD',
            '192.168.10.110': 'Serveur IA',
        }
        
        if device_ip in ip_to_device:
            return ip_to_device[device_ip]
        
        # 🔥 ÉTAPE 2 : CHAMP COMPUTER (IP ou hostname)
        computer = event.get('computer', '').strip()
        
        if computer in ip_to_device:
            return ip_to_device[computer]
        
        # Computer peut contenir un hostname
        computer_lower = computer.lower()
        if 'stormshield' in computer_lower or 'firewall' in computer_lower:
            return 'Stormshield'
        elif 'wifi' in computer_lower or 'borne' in computer_lower or 'wap' in computer_lower:
            return 'Borne WiFi'
        elif 'switch' in computer_lower:
            if '15' in computer or 'principal' in computer_lower or 'main' in computer_lower:
                return 'Switch Principal'
            elif '16' in computer or 'secondaire' in computer_lower or 'secondary' in computer_lower:
                return 'Switch Secondaire'
            else:
                return 'Switch Principal'
        elif 'ad' in computer_lower or 'dc' in computer_lower or 'domain' in computer_lower:
            return 'Serveur AD'
        elif 'ia' in computer_lower or 'ai' in computer_lower or 'ollama' in computer_lower:
            return 'Serveur IA'
        
        # 🔥 ÉTAPE 3 : SOURCE (contient souvent l'appareil)
        source = event.get('source', '').strip()
        source_lower = source.lower()
        
        # Vérifier IP dans source
        for ip, device in ip_to_device.items():
            if ip in source:
                return device
        
        # Vérifier mots-clés dans source
        if 'stormshield' in source_lower or 'firewall' in source_lower:
            return 'Stormshield'
        elif 'wifi' in source_lower or 'borne' in source_lower or 'wap' in source_lower:
            return 'Borne WiFi'
        elif 'switch' in source_lower:
            if '15' in source or 'principal' in source_lower:
                return 'Switch Principal'
            elif '16' in source or 'secondaire' in source_lower:
                return 'Switch Secondaire'
            else:
                return 'Switch Principal'
        elif 'ad' in source_lower or 'active directory' in source_lower or 'ldap' in source_lower:
            return 'Serveur AD'
        elif 'ia' in source_lower or 'serveur-ia' in source_lower or 'ollama' in source_lower:
            return 'Serveur IA'
        
        # 🔥 ÉTAPE 4 : DEVICE_NAME (depuis syslog_reader)
        device_name = event.get('_device_name', '').strip()
        
        if device_name:
            device_name_lower = device_name.lower()
            
            if 'stormshield' in device_name_lower:
                return 'Stormshield'
            elif 'wifi' in device_name_lower or 'borne' in device_name_lower:
                return 'Borne WiFi'
            elif 'switch' in device_name_lower:
                if 'principal' in device_name_lower:
                    return 'Switch Principal'
                elif 'secondaire' in device_name_lower:
                    return 'Switch Secondaire'
                else:
                    return 'Switch Principal'
            elif 'active directory' in device_name_lower or 'ad' in device_name_lower:
                return 'Serveur AD'
            elif 'serveur-ia' in device_name_lower or 'ia' in device_name_lower:
                return 'Serveur IA'
        
        # Dernier recours
        return 'Autres'
    
    def get_ticket_key(self, event):
        """Clé unique pour identifier un ticket"""
        device = self.detect_device_from_source(event)
        message = event.get('message', '')
        msg_hash = hashlib.md5(message[:200].encode()).hexdigest()[:12]
        today = date.today().isoformat()
        return f"{device}_{msg_hash}_{today}"
    
    def load_index(self):
        """Charge l'index des tickets"""
        try:
            if os.path.exists(self.ticket_index_file):
                with open(self.ticket_index_file, 'r', encoding='utf-8') as f:
                    self.ticket_index = json.load(f)
            else:
                self.ticket_index = {}
        except:
            self.ticket_index = {}
    
    def save_index(self):
        """Sauvegarde l'index"""
        try:
            with open(self.ticket_index_file, 'w', encoding='utf-8') as f:
                json.dump(self.ticket_index, f, indent=2)
        except:
            pass
    
    def get_priority_emoji(self, priority):
        """Emoji selon priorité"""
        if priority >= 9:
            return "🔴"
        elif priority >= 7:
            return "🟠"
        elif priority >= 5:
            return "🟡"
        else:
            return "🟢"
    
    def get_priority_label(self, priority):
        """Label selon priorité"""
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
        """Trouve un ticket existant"""
        ticket_key = self.get_ticket_key(event)
        if ticket_key in self.ticket_index:
            ticket_path = self.ticket_index[ticket_key]
            if os.path.exists(ticket_path):
                return ticket_path
        return None
    
    def create_or_update_ticket(self, event, analysis, web_links, log_callback=None):
        """
        🔥 Crée ou met à jour un ticket
        ✅ CORRECTION : Retourne TOUJOURS (success: bool, is_new: bool)
        """
        # 🔥 VÉRIFIER SI DOUBLON RÉCENT (< 30 min)
        is_dup, time_diff = self.is_duplicate_within_30min(event)
        
        if is_dup:
            if log_callback:
                log_callback(f"  📄 Doublon récent ({time_diff:.0f} min), ticket ignoré")
            return False, False  # ✅ Pas de ticket créé, pas nouveau
        
        # Chercher ticket existant
        existing_ticket = self.find_existing_ticket(event)
        
        if existing_ticket:
            if log_callback:
                log_callback(f"  📝 Mise à jour ticket existant")
            self.stats_updated += 1
            success = self.update_existing_ticket(existing_ticket, event, log_callback)
            
            # Marquer comme récent
            if success:
                self.mark_ticket_recent(event)
            
            return success, False  # ✅ Succès mais pas nouveau
        else:
            if log_callback:
                log_callback(f"  ✨ Création nouveau ticket")
            self.stats_created += 1
            ticket_path = self.create_new_ticket(event, analysis, web_links, log_callback)
            success = ticket_path is not None
            
            # Marquer comme récent
            if success:
                self.mark_ticket_recent(event)
            
            return success, True  # ✅ Succès et nouveau
    
    def create_new_ticket(self, event, analysis, web_links, log_callback=None):
        """Crée un nouveau ticket"""
        try:
            device = self.detect_device_from_source(event)
            device_path = os.path.join(self.output_dir, device)
            os.makedirs(device_path, exist_ok=True)
            
            error_type = f"Event_{event.get('event_id', 0)}"
            error_type_path = os.path.join(device_path, error_type)
            os.makedirs(error_type_path, exist_ok=True)
            
            msg_hash = hashlib.md5(event.get('message', '')[:200].encode()).hexdigest()[:12]
            today = date.today().isoformat()
            ticket_file = os.path.join(error_type_path, f"ticket_{today}_{msg_hash}.txt")
            
            priority = event.get('_priority', 5)
            priority_label = self.get_priority_label(priority)
            priority_emoji = self.get_priority_emoji(priority)
            severity = event.get('_severity', 'unknown')
            
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
                device_name = event.get('_device_name', device)
                device_ip = event.get('_device_ip', 'N/A')
                device_type = event.get('_device_type', 'unknown').upper()
                
                source_display = f"{device_name} ({device_ip})"
                type_display = f"Syslog - {device_type}"
            else:
                source_display = event.get('source', 'Unknown')
                type_display = "Windows Event"
            
            content = f"""╔═══════════════════════════════════╗
║  {device.upper()} - {priority_emoji} {priority_label}  ║
╚═══════════════════════════════════╝

📅 CRÉÉ: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
📊 OCCURRENCES: 1
🎯 PRIORITÉ: {priority_label}
📌 STATUT: {status}
🏷️ APPAREIL: {device}
📂 TYPE: {error_type}
🔢 SEVERITY: {severity.upper()}

────────────────────────────────────────────────────

📊 INFORMATIONS:
  • Source: {source_display}
  • Type: {type_display}
  • Event ID: {event['event_id']}
  • Catégorie: {event['event_type']}
  • Détection: {event['time_generated']}

────────────────────────────────────────────────────

📄 MESSAGE:
{event['message'][:500]}{'...' if len(event['message']) > 500 else ''}

────────────────────────────────────────────────────

🤖 ANALYSE:
{analysis}
{web_section}
────────────────────────────────────────────────────

⏰ MAJ: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
            
            with open(ticket_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            ticket_key = self.get_ticket_key(event)
            self.ticket_index[ticket_key] = ticket_file
            self.save_index()
            
            if log_callback:
                log_callback(f"  ✅ {device}/{error_type}")
            
            return ticket_file
            
        except Exception as e:
            if log_callback:
                log_callback(f"  ❌ Erreur création: {e}", "error")
            return None
    
    def update_existing_ticket(self, ticket_path, event, log_callback=None):
        """Met à jour un ticket existant"""
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
        """Nettoie les vieux tickets"""
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
        """Retourne les statistiques"""
        return {
            'created': self.stats_created,
            'updated': self.stats_updated,
            'total': self.stats_created + self.stats_updated
        }
    
    def reset_stats(self):
        """Réinitialise les stats"""
        self.stats_created = 0
        self.stats_updated = 0