"""
Lecteur Syslog - SEUILS AJUSTÉS
Fichier : syslog_reader.py - SEUILS +1

✅ AJUSTEMENT SEUILS :
- Stormshield : 3 → 4 (+1)
- Borne WiFi : 9 (INCHANGÉ - reste critique seulement)
- Switch Principal : 3 → 4 (+1)
- Switch Secondaire : 3 → 4 (+1)
"""
import os
import re
import json
import hashlib
from datetime import datetime, timedelta
from device_detector import DeviceDetector


class SyslogReader:
    """Lecteur Syslog 100% silencieux avec seuils ajustés"""
    
    # 🔥 SEUILS AJUSTÉS (+1)
    DEVICE_THRESHOLDS = {
        '192.168.10.254': 4,   # ✅ Stormshield - 4/10 (était 3)
        '192.168.10.11': 9,    # 🔥 Borne WiFi - 9/10 (INCHANGÉ - critique seulement)
        '192.168.10.15': 4,    # ✅ Switch Principal - 4/10 (était 3)
        '192.168.10.16': 4,    # ✅ Switch Secondaire - 4/10 (était 3)
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
        
        # Compteurs pour rapport
        self.stats_total_lines = 0
        self.stats_events_passed = 0
        self.stats_by_device = {}
        
        self.load_state()
    
    def log(self, message, silent=False):
        """Log avec option silent"""
        if silent:
            return
        if self.log_callback:
            try:
                self.log_callback(message)
            except:
                print(message)
        else:
            print(message)
    
    def reset_stats(self):
        """Reset compteurs"""
        self.stats_total_lines = 0
        self.stats_events_passed = 0
        self.stats_by_device.clear()
    
    def show_compact_report(self, events_count):
        """📊 RAPPORT COMPACT"""
        if events_count == 0:
            return
        
        self.log("\n" + "="*80, silent=False)
        self.log(f"📡 SYSLOG - {events_count} événement(s) réseau", silent=False)
        
        if self.stats_by_device:
            for device, count in sorted(self.stats_by_device.items(), 
                                       key=lambda x: x[1], 
                                       reverse=True):
                device_info = DeviceDetector.detect_from_ip(device)
                icon = device_info['icon'] if device_info else '📟'
                name = device_info['name'] if device_info else device
                self.log(f"   {icon} {name}: {count}", silent=False)
        
        self.log("="*80, silent=False)
    
    def load_state(self):
        """Charge état"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    self.last_position = state.get('last_position', 0)
                    last_ts = state.get('last_timestamp')
                    if last_ts:
                        self.last_timestamp = datetime.fromisoformat(last_ts)
                    
                    self.processed_hashes = set(state.get('processed_hashes', []))
        except:
            self.last_position = 0
    
    def save_state(self):
        """Sauvegarde état"""
        try:
            state = {
                'last_position': self.last_position,
                'last_timestamp': self.last_timestamp.isoformat() if self.last_timestamp else None,
                'processed_hashes': list(self.processed_hashes)[-10000:],
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
        """Vérification Syslog avec nouveaux seuils"""
        if not os.path.exists(self.syslog_path):
            raise Exception(f"Fichier Syslog introuvable: {self.syslog_path}")
        
        try:
            with open(self.syslog_path, 'r', encoding='utf-8', errors='replace') as f:
                f.read(100)
            
            size_mb = os.path.getsize(self.syslog_path) / (1024 * 1024)
            self.log(f"✅ Syslog détecté: {size_mb:.2f} MB")
            
            self.log("\n📡 ÉQUIPEMENTS RÉSEAU SURVEILLÉS (4 appareils) :")
            
            network_devices = [
                ('192.168.10.254', DeviceDetector.detect_from_ip('192.168.10.254')),
                ('192.168.10.11', DeviceDetector.detect_from_ip('192.168.10.11')),
                ('192.168.10.15', DeviceDetector.detect_from_ip('192.168.10.15')),
                ('192.168.10.16', DeviceDetector.detect_from_ip('192.168.10.16'))
            ]
            
            for ip, device in network_devices:
                threshold = self.DEVICE_THRESHOLDS.get(ip, 6)
                
                if threshold <= 4:
                    mode = "🟢 SENSIBLE (warnings+)"
                elif threshold == 5:
                    mode = "🟡 ÉQUILIBRÉ"
                elif threshold == 9:
                    mode = "🔴 CRITIQUE SEULEMENT (9/10)"
                else:
                    mode = "🟡 STANDARD"
                
                self.log(f"   {device['icon']} {ip} → {device['full_name']} (seuil: {threshold}/10 - {mode})")
            
            return True
        except PermissionError:
            raise Exception("Accès refusé au fichier Syslog")
    
    def extract_ip_from_line(self, line):
        """Extraction IP"""
        ip_match = re.match(r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
        if ip_match:
            ip = ip_match.group(1)
            if ip in self.DEVICE_THRESHOLDS:
                return ip
        
        for target_ip in self.DEVICE_THRESHOLDS.keys():
            if target_ip in line[:100]:
                return target_ip
        
        return None
    
    def extract_severity(self, line):
        """Extraction severity"""
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
        
        critical_keywords = {
            'attack': 10, 'intrusion': 10, 'breach': 10,
            'malware': 10, 'virus': 10, 'exploit': 10,
            'blocked': 8, 'denied': 8, 'drop': 8, 'reject': 8,
            'unauthorized': 9, 'invalid': 7,
            'suspicious': 8, 'anomaly': 8,
            'scan': 8, 'probe': 7,
            'authentication failed': 8, 'login failed': 8,
            'brute': 9, 'fail': 6, 'error': 6,
            'timeout': 5,
            'ddos': 10, 'dos': 9, 'flood': 9,
        }
        
        max_priority = 0
        
        for keyword, priority in critical_keywords.items():
            if keyword in line_lower:
                max_priority = max(max_priority, priority)
        
        if max_priority > 0:
            severity_labels = {
                10: 'alert', 9: 'alert', 8: 'error',
                7: 'warning', 6: 'warning', 5: 'notice'
            }
            severity = severity_labels.get(max_priority, 'notice')
            return severity, max_priority
        
        return 'info', 3
    
    def should_create_ticket(self, ip, severity, priority):
        """Règles par appareil avec nouveaux seuils"""
        min_priority = self.DEVICE_THRESHOLDS.get(ip, 6)
        return priority >= min_priority
    
    def generate_line_hash(self, line, ip):
        """Hash unique"""
        normalized = re.sub(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', '', line)
        normalized = re.sub(r'\w+\s+\d+\s+\d+:\d+:\d+', '', normalized)
        
        content = f"{ip}_{normalized[:200]}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def parse_line(self, line):
        """🔥 PARSING 100% SILENCIEUX"""
        try:
            line = line.strip()
            if not line or len(line) < 20:
                return None
            
            ip = self.extract_ip_from_line(line)
            if not ip:
                return None
            
            line_hash = self.generate_line_hash(line, ip)
            if line_hash in self.processed_hashes:
                return None
            
            device_info = DeviceDetector.detect_from_ip(ip)
            
            if not device_info:
                return None
            
            severity, priority = self.extract_severity(line)
            
            if not self.should_create_ticket(ip, severity, priority):
                return None
            
            self.processed_hashes.add(line_hash)
            
            self.stats_by_device[ip] = self.stats_by_device.get(ip, 0) + 1
            
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
            
            facility = "syslog"
            line_lower = line.lower()
            if 'asqd' in line_lower or 'firewall' in line_lower:
                facility = "firewall"
            elif 'auth' in line_lower:
                facility = "auth"
            elif 'wifi' in line_lower or 'wlan' in line_lower:
                facility = "wifi"
            
            return {
                'timestamp': timestamp,
                'ip': ip,
                'device': device_info,
                'facility': facility,
                'severity': severity,
                'priority': priority,
                'message': line,
                'raw_line': line,
                'line_hash': line_hash
            }
            
        except:
            return None
    
    def convert_to_event(self, log_entry):
        """Convertir en event"""
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
        record_hash = int(log_entry['line_hash'][:8], 16)
        
        source_display = f"{device['full_name']} ({ip})"
        
        return {
            'record_number': record_hash,
            'time_generated': log_entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            'source': source_display,
            'event_id': event_id,
            'event_type': 'ERROR' if priority >= 7 else 'WARNING',
            'computer': ip,
            'message': log_entry['message'],
            
            '_priority': priority,
            '_is_syslog': True,
            '_device_type': device['type'],
            '_device_name': device['name'],
            '_device_full_name': device['full_name'],
            '_device_ip': ip,
            '_device_icon': device['icon'],
            '_device_folder': device['folder'],
            '_device_description': device['description'],
            '_severity': severity,
            '_facility': log_entry['facility']
        }
    
    def read_new_events(self):
        """🔥 SURVEILLANCE 100% SILENCIEUSE"""
        if not os.path.exists(self.syslog_path):
            raise Exception("Fichier Syslog introuvable")
        
        events = []
        self.reset_stop()
        self.reset_stats()
        
        try:
            with open(self.syslog_path, 'r', encoding='utf-8', errors='replace') as f:
                all_lines = f.readlines()
            
            total_lines = len(all_lines)
            
            if self.last_position >= total_lines:
                return []
            
            new_lines = all_lines[self.last_position:]
            latest_timestamp = self.last_timestamp
            
            for i, line in enumerate(new_lines):
                if i % 100 == 0 and self.stop_requested:
                    break
                
                if not line.strip():
                    continue
                
                self.stats_total_lines += 1
                
                log_entry = self.parse_line(line)
                
                if not log_entry:
                    continue
                
                if self.last_timestamp and log_entry['timestamp'] <= self.last_timestamp:
                    continue
                
                if not latest_timestamp or log_entry['timestamp'] > latest_timestamp:
                    latest_timestamp = log_entry['timestamp']
                
                event = self.convert_to_event(log_entry)
                events.append(event)
                self.stats_events_passed += 1
            
            self.last_position = total_lines
            
            if latest_timestamp:
                self.last_timestamp = latest_timestamp
            
            self.save_state()
            
            if len(events) > 0:
                self.show_compact_report(len(events))
            
            return events
            
        except Exception as e:
            self.log(f"❌ Erreur Syslog: {str(e)}", silent=False)
            raise
    
    def read_initial_check(self, hours=24):
        """📅 SCAN INITIAL"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        self.log(f"📅 SCAN COMPLET Syslog {hours}h...")
        
        if not os.path.exists(self.syslog_path):
            raise Exception("Fichier Syslog introuvable")
        
        events = []
        self.reset_stop()
        self.reset_stats()
        
        try:
            with open(self.syslog_path, 'r', encoding='utf-8', errors='replace') as f:
                all_lines = f.readlines()
            
            for i, line in enumerate(all_lines):
                if i % 1000 == 0 and self.stop_requested:
                    break
                
                if not line.strip():
                    continue
                
                self.stats_total_lines += 1
                
                log_entry = self.parse_line(line)
                
                if not log_entry:
                    continue
                
                if log_entry['timestamp'] < cutoff_time:
                    continue
                
                event = self.convert_to_event(log_entry)
                events.append(event)
                self.stats_events_passed += 1
            
            self.last_position = len(all_lines)
            self.save_state()
            
            self.log(f"\n📊 SCAN SYSLOG RÉSULTAT:")
            self.log(f"   • Lignes scannées: {self.stats_total_lines}")
            self.log(f"   ✅ ÉVÉNEMENTS TROUVÉS: {len(events)}")
            
            if self.stats_by_device:
                self.log(f"\n📡 PAR APPAREIL:")
                for ip, count in sorted(self.stats_by_device.items(), 
                                       key=lambda x: x[1], 
                                       reverse=True):
                    device_info = DeviceDetector.detect_from_ip(ip)
                    icon = device_info['icon'] if device_info else '📟'
                    name = device_info['name'] if device_info else ip
                    threshold = self.DEVICE_THRESHOLDS.get(ip, 6)
                    self.log(f"   {icon} {name}: {count} (seuil: {threshold}/10)")
            
            return events
            
        except Exception as e:
            self.log(f"❌ Erreur: {str(e)}")
            raise
    
    def read_startup_check(self):
        """Démarrage - 5 min"""
        cutoff_time = datetime.now() - timedelta(minutes=5)
        
        if not os.path.exists(self.syslog_path):
            raise Exception("Fichier Syslog introuvable")
        
        events = []
        self.reset_stop()
        
        try:
            with open(self.syslog_path, 'r', encoding='utf-8', errors='replace') as f:
                all_lines = f.readlines()
            
            total_lines = len(all_lines)
            self.last_position = total_lines
            
            for line in all_lines:
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
            
            return events
            
        except Exception as e:
            self.log(f"❌ Erreur: {str(e)}")
            raise
    
    def reset(self):
        """Réinitialise"""
        self.last_position = 0
        self.last_timestamp = None
        self.processed_hashes.clear()
        self.stop_requested = False
        self.save_state()