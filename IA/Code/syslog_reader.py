"""
Lecteur Syslog - VERSION CORRIGÉE
Fichier : syslog_reader.py
CORRECTIFS:
- Capture TOUS les warnings/errors/alerts
- Hash unique par message pour éviter les VRAIS doublons
- Pas de filtrage excessif
"""
import os
import re
import json
import hashlib
from datetime import datetime, timedelta


class SyslogReader:
    """Lecteur Syslog : capture TOUS les incidents"""
    
    MONITORED_DEVICES = {
        '192.168.10.254': {'name': 'Stormshield UTM', 'type': 'firewall', 'icon': '🔥'},
        '192.168.10.11': {'name': 'Borne WiFi', 'type': 'wifi', 'icon': '📡'},
        '192.168.10.15': {'name': 'Switch Principal', 'type': 'switch', 'icon': '🔌'},
        '192.168.10.16': {'name': 'Switch Secondaire', 'type': 'switch', 'icon': '🔌'},
        '192.168.10.10': {'name': 'Active Directory', 'type': 'server', 'icon': '🖥️'},
        '192.168.10.110': {'name': 'Serveur-IA', 'type': 'server', 'icon': '🤖'},
    }
    
    def __init__(self, log_callback=None, verbose=False):
        self.log_callback = log_callback
        self.verbose = verbose
        self.syslog_path = r"\\SRV-SYSLOG\surveillence$\syslog"
        self.state_file = r"C:\IA\.syslog_state.json"
        
        self.last_position = 0
        self.last_timestamp = None
        # 🔥 Hash pour éviter les VRAIS doublons (même message à la même seconde)
        self.processed_hashes = set()
        self.stop_requested = False
        
        self.stats_total_lines = 0
        self.stats_by_device = {}
        self.stats_by_severity = {}
        
        self.load_state()
    
    def log(self, message, silent=False):
        if silent:
            return
        if self.log_callback:
            try:
                self.log_callback(message)
            except:
                print(message)
        else:
            print(message)
    
    def load_state(self):
        """Charge l'état sauvegardé"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    self.last_position = state.get('last_position', 0)
                    last_ts = state.get('last_timestamp')
                    if last_ts:
                        self.last_timestamp = datetime.fromisoformat(last_ts)
        except:
            pass
    
    def save_state(self):
        """Sauvegarde l'état"""
        try:
            state = {
                'last_position': self.last_position,
                'last_timestamp': self.last_timestamp.isoformat() if self.last_timestamp else None,
                'last_save': datetime.now().isoformat()
            }
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
        except:
            pass
    
    def request_stop(self):
        """Demande l'arrêt"""
        self.stop_requested = True
    
    def reset_stop(self):
        """Réinitialise le flag d'arrêt"""
        self.stop_requested = False
    
    def check_availability(self):
        """Vérifie la disponibilité du fichier Syslog"""
        if not os.path.exists(self.syslog_path):
            raise Exception(f"Fichier Syslog introuvable: {self.syslog_path}")
        
        try:
            with open(self.syslog_path, 'r', encoding='utf-8', errors='replace') as f:
                f.read(100)
            
            size_mb = os.path.getsize(self.syslog_path) / (1024 * 1024)
            self.log(f"✅ Syslog détecté: {size_mb:.2f} MB")
            
            self.log("\n📡 ÉQUIPEMENTS SURVEILLÉS:")
            for ip, info in self.MONITORED_DEVICES.items():
                self.log(f"   {info['icon']} {ip} → {info['name']}")
            
            return True
        except PermissionError:
            raise Exception("Accès refusé au fichier Syslog")
    
    def extract_ip_from_line(self, line):
        """
        Extrait l'IP en début de ligne (appareil source)
        Format Syslog : "192.168.10.254 Jan 15 13:35:52 ..."
        """
        # 1. Chercher IP en DÉBUT de ligne
        line_start = line[:30]
        ip_match = re.search(r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line_start)
        
        if ip_match:
            ip = ip_match.group(1)
            if ip in self.MONITORED_DEVICES:
                return ip
            return ip
        
        # 2. Fallback : chercher n'importe quelle IP surveillée
        ip_pattern = r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'
        found_ips = re.findall(ip_pattern, line)
        
        for ip in found_ips:
            if ip in self.MONITORED_DEVICES:
                return ip
        
        # 3. Prendre la première IP trouvée
        return found_ips[0] if found_ips else None
    
    def get_device_info(self, ip):
        """Retourne les infos de l'appareil"""
        if ip in self.MONITORED_DEVICES:
            return self.MONITORED_DEVICES[ip]
        
        return {
            'name': f'Équipement {ip}',
            'type': 'unknown',
            'icon': '❓'
        }
    
    def extract_severity(self, line):
        """Extrait severity - CAPTURE TOUT"""
        line_lower = line.lower()
        
        # Severity explicite
        severity_patterns = [
            (r'\bemerg(?:ency)?\b', 'emergency', 10),
            (r'\balert\b', 'alert', 10),
            (r'\bcrit(?:ical)?\b', 'critical', 10),
            (r'\berr(?:or)?\b', 'error', 8),
            (r'\bwarn(?:ing)?\b', 'warning', 6),
            (r'\bnotice\b', 'notice', 4),
            (r'\binfo\b', 'info', 2),
            (r'\bdebug\b', 'debug', 1),
        ]
        
        for pattern, severity, priority in severity_patterns:
            if re.search(pattern, line_lower):
                return severity, priority
        
        # Mots-clés d'erreur
        error_keywords = {
            'fail': 8, 'failed': 8, 'failure': 8,
            'error': 8, 'denied': 8, 'reject': 8,
            'blocked': 8, 'drop': 8, 'attack': 10,
            'intrusion': 10, 'breach': 10, 'unauthorized': 9,
            'timeout': 6, 'unreachable': 6, 'invalid': 6
        }
        
        for keyword, priority in error_keywords.items():
            if keyword in line_lower:
                if priority >= 8:
                    return 'error', priority
                elif priority >= 6:
                    return 'warning', priority
        
        return 'info', 2
    
    def should_create_ticket(self, severity, priority):
        """
        🔥 RÈGLE : WARNING (6+) ou plus → TICKET
        """
        return priority >= 6
    
    def get_line_hash(self, line, timestamp):
        """
        🔥 HASH UNIQUE par message pour éviter les VRAIS doublons
        Combine: timestamp + message normalisé
        """
        # Normaliser le message (retirer IPs, nombres variables)
        normalized = line[20:220] if len(line) > 20 else line
        normalized = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', 'IP', normalized)
        normalized = re.sub(r'\d{2}:\d{2}:\d{2}', 'TIME', normalized)
        
        # Combiner avec timestamp (à la seconde près)
        hash_input = f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')}_{normalized}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:10]
    
    def parse_line(self, line):
        """Parse une ligne Syslog"""
        try:
            line = line.strip()
            if not line or len(line) < 20:
                return None
            
            # 1. Extraire l'IP (appareil source)
            ip = self.extract_ip_from_line(line)
            if not ip:
                return None
            
            # 2. Identifier l'appareil
            device = self.get_device_info(ip)
            
            # 3. Extraire severity et priorité
            severity, priority = self.extract_severity(line)
            
            # 4. Vérifier si ticket nécessaire
            if not self.should_create_ticket(severity, priority):
                return None
            
            # 5. Timestamp
            timestamp = datetime.now()
            try:
                time_match = re.search(r'(\w+)\s+(\d+)\s+(\d+:\d+:\d+)', line)
                if time_match:
                    year = datetime.now().year
                    month = time_match.group(1)
                    day = time_match.group(2)
                    time_str = time_match.group(3)
                    timestamp_str = f"{year} {month} {day} {time_str}"
                    timestamp = datetime.strptime(timestamp_str, "%Y %b %d %H:%M:%S")
            except:
                pass
            
            # 6. Facility
            facility = "syslog"
            line_lower = line.lower()
            if 'asqd' in line_lower or 'firewall' in line_lower:
                facility = "firewall"
            elif 'auth' in line_lower:
                facility = "auth"
            elif 'wifi' in line_lower:
                facility = "wifi"
            elif 'dhcp' in line_lower:
                facility = "dhcp"
            elif 'dns' in line_lower:
                facility = "dns"
            
            # 7. Stats
            self.stats_by_severity[severity] = self.stats_by_severity.get(severity, 0) + 1
            self.stats_by_device[device['name']] = self.stats_by_device.get(device['name'], 0) + 1
            
            return {
                'timestamp': timestamp,
                'ip': ip,
                'device': device,
                'facility': facility,
                'severity': severity,
                'priority': priority,
                'message': line,
                'raw_line': line
            }
            
        except:
            return None
    
    def convert_to_event(self, log_entry):
        """Convertit en format événement"""
        device = log_entry['device']
        severity = log_entry['severity']
        priority = log_entry['priority']
        ip = log_entry['ip']
        
        event_ids = {
            'emergency': 10000,
            'alert': 9000,
            'critical': 8000,
            'error': 7000,
            'warning': 6000,
        }
        
        event_id = event_ids.get(severity, 5000)
        
        # 🔥 HASH UNIQUE pour le record_number
        record_hash = int(hashlib.md5(log_entry['raw_line'].encode()).hexdigest()[:8], 16)
        
        return {
            'record_number': record_hash,
            'time_generated': log_entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            'source': f"{device['icon']} {device['name']} ({ip})",
            'event_id': event_id,
            'event_type': 'ERROR' if priority >= 7 else 'WARNING',
            'computer': ip,
            'message': log_entry['message'],
            '_priority': priority,
            '_is_syslog': True,
            '_device_type': device['type'],
            '_device_name': device['name'],
            '_device_ip': ip,
            '_severity': severity,
            '_facility': log_entry['facility']
        }
    
    def read_events(self, since_time=None, force_full_scan=False, silent=False):
        """🔥 LECTURE COMPLÈTE - Capture TOUS les incidents"""
        if not os.path.exists(self.syslog_path):
            raise Exception("Fichier Syslog introuvable")
        
        events = []
        self.reset_stop()
        
        # Reset stats
        self.stats_total_lines = 0
        self.stats_by_device = {}
        self.stats_by_severity = {}
        
        try:
            if not silent:
                self.log("📂 Lecture Syslog...")
            
            with open(self.syslog_path, 'r', encoding='utf-8', errors='replace') as f:
                all_lines = f.readlines()
            
            total_lines = len(all_lines)
            
            if force_full_scan or self.last_position == 0:
                lines_to_process = all_lines
                if not silent:
                    self.log(f"   📖 Scan complet: {len(lines_to_process)} lignes")
            else:
                if self.last_position < total_lines:
                    lines_to_process = all_lines[self.last_position:]
                else:
                    lines_to_process = []
            
            if not lines_to_process:
                self.save_state()
                return []
            
            new_hashes = set()
            latest_timestamp = self.last_timestamp
            
            for i, line in enumerate(lines_to_process):
                if i % 100 == 0 and self.stop_requested:
                    break
                
                self.stats_total_lines += 1
                
                if not line.strip():
                    continue
                
                # Parser
                log_entry = self.parse_line(line)
                
                if not log_entry:
                    continue
                
                # 🔥 Hash unique pour éviter les VRAIS doublons
                line_hash = self.get_line_hash(line, log_entry['timestamp'])
                
                if line_hash in self.processed_hashes:
                    continue
                
                new_hashes.add(line_hash)
                
                # Filtrer par temps
                if self.last_timestamp and log_entry['timestamp'] <= self.last_timestamp:
                    continue
                
                if not latest_timestamp or log_entry['timestamp'] > latest_timestamp:
                    latest_timestamp = log_entry['timestamp']
                
                if since_time and log_entry['timestamp'] < since_time:
                    continue
                
                # Convertir
                event = self.convert_to_event(log_entry)
                events.append(event)
            
            # Sauvegarder état
            if not force_full_scan:
                self.last_position = total_lines
            
            if latest_timestamp:
                self.last_timestamp = latest_timestamp
            
            self.processed_hashes.update(new_hashes)
            if len(self.processed_hashes) > 10000:
                self.processed_hashes = set(list(self.processed_hashes)[-10000:])
            
            self.save_state()
            
            # Stats
            if not silent:
                self.log(f"\n📊 SYSLOG RÉSULTAT:")
                self.log(f"   • Lignes scannées: {self.stats_total_lines}")
                self.log(f"   📊 TOTAL ÉVÉNEMENTS: {len(events)}")
                
                if self.stats_by_severity:
                    self.log(f"\n📈 PAR SEVERITY:")
                    for sev, count in sorted(self.stats_by_severity.items()):
                        emoji = "🔴" if sev in ['emergency','alert','critical'] else "🟠" if sev == 'error' else "🟡"
                        self.log(f"   {emoji} {sev.upper()}: {count}")
                
                if self.stats_by_device:
                    self.log(f"\n📡 PAR ÉQUIPEMENT:")
                    for device, count in sorted(self.stats_by_device.items(), key=lambda x: x[1], reverse=True):
                        device_ip = "N/A"
                        for ip, info in self.MONITORED_DEVICES.items():
                            if info['name'] == device:
                                device_ip = ip
                                break
                        self.log(f"   • {device} ({device_ip}): {count} incidents")
            
            return events
            
        except Exception as e:
            self.log(f"❌ Erreur Syslog: {str(e)}", silent=False)
            raise
    
    def read_initial_check(self, hours=24):
        """Vérification initiale"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        self.log(f"📅 Vérification Syslog {hours}h...")
        return self.read_events(since_time=cutoff_time, force_full_scan=True, silent=False)
    
    def read_new_events(self):
        """Surveillance continue"""
        return self.read_events(force_full_scan=False, silent=False)
    
    def reset(self):
        """Réinitialise le lecteur"""
        self.last_position = 0
        self.last_timestamp = None
        self.processed_hashes.clear()
        self.stop_requested = False
        self.save_state()