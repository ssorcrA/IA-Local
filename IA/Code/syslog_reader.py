"""
Lecteur Syslog - BORNE WIFI TRÈS SÉLECTIVE (seuil 9/10)
Fichier : syslog_reader.py - VERSION FINALE
✅ CORRECTIFS:
- Borne WiFi : seuil 9 (critiques uniquement)
- Stormshield : seuil 5 (surveillance normale)
- Switches : seuil 6 (surveillance normale)
"""
import os
import re
import json
import hashlib
from datetime import datetime, timedelta


class SyslogReader:
    """Lecteur Syslog avec Borne WiFi très sélective"""
    
    # 🔥 SEUILS AJUSTÉS - BORNE WIFI CRITIQUE UNIQUEMENT
    MONITORED_DEVICES = {
        '192.168.10.254': {
            'name': 'Stormshield UTM', 
            'type': 'firewall', 
            'icon': '🔥', 
            'min_priority': 5  # ✅ Surveillance normale - warnings + errors
        },
        '192.168.10.11': {
            'name': 'Borne WiFi', 
            'type': 'wifi', 
            'icon': '📡', 
            'min_priority': 9  # 🔥 TRÈS SÉLECTIF - Critiques uniquement
        },
        '192.168.10.15': {
            'name': 'Switch Principal', 
            'type': 'switch', 
            'icon': '🔌', 
            'min_priority': 6  # ✅ Surveillance normale - erreurs moyennes+
        },
        '192.168.10.16': {
            'name': 'Switch Secondaire', 
            'type': 'switch', 
            'icon': '🔌', 
            'min_priority': 6  # ✅ Surveillance normale
        },
        '192.168.10.10': {
            'name': 'Active Directory', 
            'type': 'server', 
            'icon': '🖥️', 
            'min_priority': 6  # ✅ Erreurs importantes
        },
        '192.168.10.110': {
            'name': 'Serveur-IA', 
            'type': 'server', 
            'icon': '🤖', 
            'min_priority': 7  # Critiques uniquement
        },
    }
    
    def __init__(self, log_callback=None, verbose=False):
        self.log_callback = log_callback
        self.verbose = verbose
        self.syslog_path = r"\\SRV-SYSLOG\surveillence$\syslog"
        self.state_file = r"C:\IA\.syslog_state.json"
        
        self.last_position = 0
        self.last_timestamp = None
        self.processed_hashes = set()
        self.stop_requested = False
        
        self.stats_total_lines = 0
        self.stats_by_device = {}
        self.stats_by_severity = {}
        self.stats_filtered_out = 0
        
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
        self.stop_requested = True
    
    def reset_stop(self):
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
            
            self.log("\n📡 ÉQUIPEMENTS SURVEILLÉS (seuils ajustés):")
            for ip, info in self.MONITORED_DEVICES.items():
                icon = "🔥" if info['min_priority'] == 9 else "✅"
                self.log(f"   {info['icon']} {ip} → {info['name']} (seuil: {info['min_priority']}/10) {icon if info['min_priority'] == 9 else ''}")
            
            return True
        except PermissionError:
            raise Exception("Accès refusé au fichier Syslog")
    
    def extract_ip_from_line(self, line):
        """Extrait l'IP de manière robuste"""
        # IP en début
        ip_match = re.match(r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
        if ip_match:
            ip = ip_match.group(1)
            if ip in self.MONITORED_DEVICES:
                return ip
        
        # Recherche début
        line_start = line[:50]
        for ip in self.MONITORED_DEVICES.keys():
            if ip in line_start:
                return ip
        
        # Recherche complète
        ip_pattern = r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'
        found_ips = re.findall(ip_pattern, line)
        
        for ip in found_ips:
            if ip in self.MONITORED_DEVICES:
                return ip
        
        return found_ips[0] if found_ips else None
    
    def get_device_info(self, ip):
        """Retourne les infos de l'appareil"""
        if ip in self.MONITORED_DEVICES:
            return self.MONITORED_DEVICES[ip]
        
        return {
            'name': f'Équipement {ip}',
            'type': 'unknown',
            'icon': '❓',
            'min_priority': 7
        }
    
    def extract_severity(self, line):
        """
        ✅ EXTRACTION SEVERITY - OPTIMISÉE
        """
        
        # FORMAT 1: Stormshield tabulations
        if '\t' in line:
            parts = line.split('\t')
            
            for i in range(min(10, len(parts))):
                field = parts[i].strip().lower()
                
                severity_map = {
                    'emerg': ('emergency', 10), 
                    'emergency': ('emergency', 10),
                    'alert': ('alert', 10),
                    'crit': ('critical', 10), 
                    'critical': ('critical', 10),
                    'err': ('error', 8), 
                    'error': ('error', 8),
                    'warning': ('warning', 7), 
                    'warn': ('warning', 7),
                    'notice': ('notice', 5),
                    'info': ('info', 3),
                    'informational': ('info', 3),
                    'debug': ('debug', 1),
                }
                
                if field in severity_map:
                    severity, priority = severity_map[field]
                    return severity, priority
        
        # FORMAT 2: Severity explicite
        line_lower = line.lower()
        
        severity_patterns = [
            (r'\bemerg(?:ency)?\b', 'emergency', 10),
            (r'\balert\b', 'alert', 10),
            (r'\bcrit(?:ical)?\b', 'critical', 10),
            (r'\berr(?:or)?\b', 'error', 8),
            (r'\bwarn(?:ing)?\b', 'warning', 7),
            (r'\bnotice\b', 'notice', 5),
            (r'\binfo(?:rmational)?\b', 'info', 3),
            (r'\bdebug\b', 'debug', 1),
        ]
        
        for pattern, severity, priority in severity_patterns:
            if re.search(pattern, line_lower):
                return severity, priority
        
        # ✅ FORMAT 3: MOTS-CLÉS INTRUSION
        critical_keywords = {
            # Intrusions directes
            'attack': 10, 'intrusion': 10, 'breach': 10, 'compromise': 10,
            'malware': 10, 'virus': 10, 'exploit': 10, 'hack': 10,
            
            # Blocages firewall
            'blocked': 8, 'denied': 8, 'drop': 8, 'reject': 8,
            'refused': 8, 'forbidden': 8,
            
            # Tentatives suspectes
            'unauthorized': 9, 'invalid': 7, 'illegal': 8,
            'suspicious': 8, 'anomaly': 8,
            
            # Scans
            'scan': 8, 'probe': 7, 'port scan': 9,
            
            # Auth
            'authentication failed': 8, 'login failed': 8,
            'brute': 9, 'brute force': 10,
            
            # Erreurs
            'fail': 6, 'failed': 6, 'failure': 6,
            'timeout': 5, 'error': 6,
            
            # Trafic malveillant
            'ddos': 10, 'dos': 9, 'flood': 9,
        }
        
        max_priority = 0
        matched_keywords = []
        
        for keyword, priority in critical_keywords.items():
            if keyword in line_lower:
                max_priority = max(max_priority, priority)
                matched_keywords.append(keyword)
        
        # Patterns avancés
        advanced_patterns = [
            (r'failed\s+login\s+attempt', 8),
            (r'multiple\s+failed\s+attempts', 9),
            (r'\d+\s+failed\s+attempts', 9),
            (r'access\s+denied\s+from', 8),
            (r'connection\s+refused\s+from', 7),
            (r'invalid\s+user', 8),
        ]
        
        for pattern, priority in advanced_patterns:
            if re.search(pattern, line_lower):
                max_priority = max(max_priority, priority)
        
        if max_priority > 0:
            severity_labels = {
                10: 'alert', 9: 'alert', 8: 'error',
                7: 'warning', 6: 'warning', 5: 'notice'
            }
            severity = severity_labels.get(max_priority, 'notice')
            return severity, max_priority
        
        # Par défaut
        return 'info', 3
    
    def should_create_ticket(self, ip, severity, priority):
        """✅ RÈGLE PAR APPAREIL - SEUILS AJUSTÉS"""
        device_info = self.get_device_info(ip)
        min_priority = device_info.get('min_priority', 7)
        
        return priority >= min_priority
    
    def parse_line(self, line):
        """Parse une ligne Syslog"""
        try:
            line = line.strip()
            if not line or len(line) < 20:
                return None
            
            # 1. IP
            ip = self.extract_ip_from_line(line)
            if not ip:
                return None
            
            # 2. Appareil
            device = self.get_device_info(ip)
            
            # 3. Severity + Priority
            severity, priority = self.extract_severity(line)
            
            # 4. ✅ VÉRIFIE SEUIL
            if not self.should_create_ticket(ip, severity, priority):
                self.stats_filtered_out += 1
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
            elif 'wifi' in line_lower or 'wlan' in line_lower:
                facility = "wifi"
            
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
            
        except Exception as e:
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
            'notice': 5500,
        }
        
        event_id = event_ids.get(severity, 5000)
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
        """Lecture normale (surveillance continue)"""
        if not os.path.exists(self.syslog_path):
            raise Exception("Fichier Syslog introuvable")
        
        events = []
        self.reset_stop()
        
        self.stats_total_lines = 0
        self.stats_by_device = {}
        self.stats_by_severity = {}
        self.stats_filtered_out = 0
        
        try:
            if not silent:
                self.log("📂 Lecture Syslog (surveillance)...")
            
            with open(self.syslog_path, 'r', encoding='utf-8', errors='replace') as f:
                all_lines = f.readlines()
            
            total_lines = len(all_lines)
            
            if self.last_position < total_lines:
                lines_to_process = all_lines[self.last_position:]
                if not silent:
                    self.log(f"   📖 Nouvelles lignes: {len(lines_to_process)}")
            else:
                if not silent:
                    self.log(f"   ✅ Aucune nouvelle ligne")
                self.save_state()
                return []
            
            latest_timestamp = self.last_timestamp
            
            for i, line in enumerate(lines_to_process):
                if i % 100 == 0 and self.stop_requested:
                    break
                
                self.stats_total_lines += 1
                
                if not line.strip():
                    continue
                
                log_entry = self.parse_line(line)
                
                if not log_entry:
                    continue
                
                if self.last_timestamp and log_entry['timestamp'] <= self.last_timestamp:
                    continue
                
                if not latest_timestamp or log_entry['timestamp'] > latest_timestamp:
                    latest_timestamp = log_entry['timestamp']
                
                if since_time and log_entry['timestamp'] < since_time:
                    continue
                
                event = self.convert_to_event(log_entry)
                events.append(event)
            
            self.last_position = total_lines
            
            if latest_timestamp:
                self.last_timestamp = latest_timestamp
            
            self.save_state()
            
            if not silent and events:
                self.log(f"\n📊 SYSLOG RÉSULTAT:")
                self.log(f"   • Lignes scannées: {self.stats_total_lines}")
                self.log(f"   📈 ÉVÉNEMENTS: {len(events)}")
                
                if self.stats_by_device:
                    self.log(f"\n📡 PAR ÉQUIPEMENT:")
                    for device, count in sorted(self.stats_by_device.items(), key=lambda x: x[1], reverse=True):
                        self.log(f"   • {device}: {count} incidents")
            
            return events
            
        except Exception as e:
            self.log(f"❌ Erreur Syslog: {str(e)}", silent=False)
            raise
    
    def read_initial_check(self, hours=24):
        """SCAN COMPLET"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        self.log(f"📅 SCAN COMPLET Syslog {hours}h...")
        
        if not os.path.exists(self.syslog_path):
            raise Exception("Fichier Syslog introuvable")
        
        events = []
        self.reset_stop()
        
        self.stats_total_lines = 0
        self.stats_by_device = {}
        self.stats_by_severity = {}
        self.stats_filtered_out = 0
        
        try:
            self.log("📂 Lecture COMPLÈTE du fichier...")
            
            with open(self.syslog_path, 'r', encoding='utf-8', errors='replace') as f:
                all_lines = f.readlines()
            
            self.log(f"   📖 Total lignes: {len(all_lines)}")
            
            for i, line in enumerate(all_lines):
                if i % 1000 == 0 and self.stop_requested:
                    break
                
                self.stats_total_lines += 1
                
                if not line.strip():
                    continue
                
                log_entry = self.parse_line(line)
                
                if not log_entry:
                    continue
                
                if log_entry['timestamp'] < cutoff_time:
                    continue
                
                event = self.convert_to_event(log_entry)
                events.append(event)
            
            self.log(f"\n📊 SCAN RÉSULTAT:")
            self.log(f"   • Lignes: {self.stats_total_lines}")
            self.log(f"   • Filtrées: {self.stats_filtered_out}")
            self.log(f"   📈 ÉVÉNEMENTS: {len(events)}")
            
            if self.stats_by_severity:
                self.log(f"\n📈 PAR SEVERITY:")
                for sev in ['emergency', 'alert', 'critical', 'error', 'warning', 'notice']:
                    if sev in self.stats_by_severity:
                        count = self.stats_by_severity[sev]
                        emoji = "🔴" if sev in ['emergency','alert','critical'] else "🟠"
                        self.log(f"   {emoji} {sev.upper()}: {count}")
            
            if self.stats_by_device:
                self.log(f"\n📡 PAR ÉQUIPEMENT:")
                for device, count in sorted(self.stats_by_device.items(), key=lambda x: x[1], reverse=True):
                    self.log(f"   • {device}: {count} incidents")
            
            return events
            
        except Exception as e:
            self.log(f"❌ Erreur: {str(e)}")
            raise
    
    def read_startup_check(self):
        """LECTURE DÉMARRAGE - 5 MINUTES"""
        cutoff_time = datetime.now() - timedelta(minutes=5)
        self.log(f"⏰ DÉMARRAGE - Scan 5 dernières minutes...")
        
        if not os.path.exists(self.syslog_path):
            raise Exception("Fichier Syslog introuvable")
        
        events = []
        self.reset_stop()
        
        self.stats_total_lines = 0
        self.stats_by_device = {}
        self.stats_by_severity = {}
        self.stats_filtered_out = 0
        
        try:
            with open(self.syslog_path, 'r', encoding='utf-8', errors='replace') as f:
                all_lines = f.readlines()
            
            total_lines = len(all_lines)
            self.log(f"   📖 Lignes: {total_lines}")
            
            self.last_position = total_lines
            
            for i, line in enumerate(all_lines):
                if i % 1000 == 0 and self.stop_requested:
                    break
                
                self.stats_total_lines += 1
                
                if not line.strip():
                    continue
                
                log_entry = self.parse_line(line)
                
                if not log_entry:
                    continue
                
                if log_entry['timestamp'] < cutoff_time:
                    continue
                
                event = self.convert_to_event(log_entry)
                events.append(event)
                
                if not self.last_timestamp or log_entry['timestamp'] > self.last_timestamp:
                    self.last_timestamp = log_entry['timestamp']
            
            self.save_state()
            
            self.log(f"\n📊 DÉMARRAGE:")
            self.log(f"   • Position: {self.last_position}")
            self.log(f"   📈 ÉVÉNEMENTS (5 min): {len(events)}")
            
            return events
            
        except Exception as e:
            self.log(f"❌ Erreur: {str(e)}")
            raise
    
    def read_new_events(self):
        """SURVEILLANCE CONTINUE"""
        return self.read_events(force_full_scan=False, silent=False)
    
    def reset(self):
        """Réinitialise le lecteur"""
        self.last_position = 0
        self.last_timestamp = None
        self.processed_hashes.clear()
        self.stop_requested = False
        self.save_state()