"""
Lecteur Syslog - CORRECTIF 0 ÉVÉNEMENTS
Fichier : syslog_reader.py - VERSION DEBUGGÉE v2
✅ CORRECTIFS APPLIQUÉS :
- ✅ Logs de diagnostic pour identifier pourquoi 0 événements
- ✅ Vérification étape par étape du parsing
- ✅ Compteurs détaillés
"""
import os
import re
import json
import hashlib
from datetime import datetime, timedelta
from device_detector import DeviceDetector


class SyslogReader:
    """Lecteur Syslog avec diagnostics étendus"""
    
    # 🔥 SEUILS ULTRA-BAS
    DEVICE_THRESHOLDS = {
        '192.168.10.254': 3,   # ✅ Stormshield - 3/10
        '192.168.10.11': 9,    # 🔥 Borne WiFi - 9/10 (critique seulement)
        '192.168.10.15': 3,    # ✅ Switch Principal - 3/10
        '192.168.10.16': 3,    # ✅ Switch Secondaire - 3/10
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
        
        # 🔥 COMPTEURS DE DIAGNOSTIC
        self.debug_total_lines = 0
        self.debug_empty_lines = 0
        self.debug_no_ip = 0
        self.debug_ip_found = {}
        self.debug_severity_found = {}
        self.debug_filtered_by_threshold = 0
        self.debug_duplicates = 0
        self.debug_passed = 0
        
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
    
    def reset_debug_counters(self):
        """Réinitialise les compteurs de diagnostic"""
        self.debug_total_lines = 0
        self.debug_empty_lines = 0
        self.debug_no_ip = 0
        self.debug_ip_found.clear()
        self.debug_severity_found.clear()
        self.debug_filtered_by_threshold = 0
        self.debug_duplicates = 0
        self.debug_passed = 0
    
    def show_debug_report(self):
        """Affiche un rapport de diagnostic"""
        self.log("\n" + "="*80, silent=False)
        self.log("🔬 RAPPORT DE DIAGNOSTIC SYSLOG", silent=False)
        self.log("="*80, silent=False)
        
        self.log(f"\n📊 TRAITEMENT DES LIGNES :", silent=False)
        self.log(f"   • Total lignes scannées : {self.debug_total_lines}", silent=False)
        self.log(f"   • Lignes vides ignorées : {self.debug_empty_lines}", silent=False)
        self.log(f"   • Lignes sans IP : {self.debug_no_ip}", silent=False)
        
        if self.debug_ip_found:
            self.log(f"\n📡 IP DÉTECTÉES :", silent=False)
            for ip, count in sorted(self.debug_ip_found.items(), key=lambda x: x[1], reverse=True):
                device = DeviceDetector.detect_from_ip(ip)
                name = device['name'] if device else 'Inconnu'
                threshold = self.DEVICE_THRESHOLDS.get(ip, 6)
                self.log(f"   • {ip} ({name}) : {count} lignes [seuil: {threshold}/10]", silent=False)
        
        if self.debug_severity_found:
            self.log(f"\n⚠️ SEVERITIES DÉTECTÉES :", silent=False)
            for sev, count in sorted(self.debug_severity_found.items(), key=lambda x: x[1], reverse=True):
                self.log(f"   • {sev.upper()} : {count}", silent=False)
        
        self.log(f"\n🔍 FILTRAGE :", silent=False)
        self.log(f"   • Filtrés par seuil : {self.debug_filtered_by_threshold}", silent=False)
        self.log(f"   • Doublons détectés : {self.debug_duplicates}", silent=False)
        self.log(f"   ✅ PASSÉS AU FILTRE : {self.debug_passed}", silent=False)
        
        self.log("="*80 + "\n", silent=False)
    
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
                    
                    self.processed_hashes = set(state.get('processed_hashes', []))
                    
                    if self.last_position > 0:
                        self.log(f"📌 Position reprise: ligne {self.last_position}", silent=False)
        except Exception as e:
            self.log(f"⚠️ Impossible de charger l'état: {e}", silent=False)
            self.last_position = 0
    
    def save_state(self):
        """Sauvegarde l'état + hashes"""
        try:
            state = {
                'last_position': self.last_position,
                'last_timestamp': self.last_timestamp.isoformat() if self.last_timestamp else None,
                'processed_hashes': list(self.processed_hashes)[-10000:],
                'last_save': datetime.now().isoformat()
            }
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.log(f"⚠️ Erreur sauvegarde état: {e}", silent=False)
    
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
            
            self.log("\n📡 ÉQUIPEMENTS RÉSEAU SURVEILLÉS (4 appareils) :")
            
            network_devices = [
                ('192.168.10.254', DeviceDetector.detect_from_ip('192.168.10.254')),
                ('192.168.10.11', DeviceDetector.detect_from_ip('192.168.10.11')),
                ('192.168.10.15', DeviceDetector.detect_from_ip('192.168.10.15')),
                ('192.168.10.16', DeviceDetector.detect_from_ip('192.168.10.16'))
            ]
            
            for ip, device in network_devices:
                threshold = self.DEVICE_THRESHOLDS.get(ip, 6)
                
                if threshold <= 3:
                    mode = "🟢 ULTRA-SENSIBLE (tout)"
                elif threshold == 5:
                    mode = "🟡 SENSIBLE (warnings+)"
                elif threshold == 9:
                    mode = "🔴 CRITIQUE SEULEMENT (9/10)"
                else:
                    mode = "🟡 ÉQUILIBRÉ"
                
                self.log(f"   {device['icon']} {ip} → {device['full_name']} (seuil: {threshold}/10 - {mode})")
            
            return True
        except PermissionError:
            raise Exception("Accès refusé au fichier Syslog")
    
    def extract_ip_from_line(self, line):
        """Extraction IP robuste"""
        ip_match = re.match(r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
        if ip_match:
            ip = ip_match.group(1)
            if ip in self.DEVICE_THRESHOLDS:
                return ip
        
        if '192.168.10.11' in line[:200]:
            return '192.168.10.11'
        
        line_start = line[:100]
        for target_ip in self.DEVICE_THRESHOLDS.keys():
            if target_ip in line_start:
                return target_ip
        
        ip_pattern = r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'
        found_ips = re.findall(ip_pattern, line)
        
        for ip in found_ips:
            if ip in self.DEVICE_THRESHOLDS:
                return ip
        
        return None
    
    def extract_severity(self, line):
        """Extraction severity optimisée"""
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
        """Règles par appareil"""
        min_priority = self.DEVICE_THRESHOLDS.get(ip, 6)
        return priority >= min_priority
    
    def generate_line_hash(self, line, ip):
        """Génère hash unique"""
        normalized = re.sub(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', '', line)
        normalized = re.sub(r'\w+\s+\d+\s+\d+:\d+:\d+', '', normalized)
        
        content = f"{ip}_{normalized[:200]}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def parse_line(self, line):
        """Parse ligne avec diagnostic"""
        try:
            self.debug_total_lines += 1
            
            line = line.strip()
            if not line or len(line) < 20:
                self.debug_empty_lines += 1
                return None
            
            # 🔥 DIAGNOSTIC : Extraction IP
            ip = self.extract_ip_from_line(line)
            if not ip:
                self.debug_no_ip += 1
                return None
            
            # 🔥 COMPTEUR IP
            self.debug_ip_found[ip] = self.debug_ip_found.get(ip, 0) + 1
            
            # Hash de déduplication
            line_hash = self.generate_line_hash(line, ip)
            if line_hash in self.processed_hashes:
                self.debug_duplicates += 1
                return None
            
            device_info = DeviceDetector.detect_from_ip(ip)
            
            if not device_info:
                return None
            
            # 🔥 DIAGNOSTIC : Extraction Severity
            severity, priority = self.extract_severity(line)
            
            # 🔥 COMPTEUR SEVERITY
            self.debug_severity_found[severity] = self.debug_severity_found.get(severity, 0) + 1
            
            # 🔥 DIAGNOSTIC : Filtrage par seuil
            if not self.should_create_ticket(ip, severity, priority):
                self.debug_filtered_by_threshold += 1
                return None
            
            # 🔥 PASSÉ TOUS LES FILTRES
            self.debug_passed += 1
            
            self.processed_hashes.add(line_hash)
            
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
            
        except Exception as e:
            return None
    
    def convert_to_event(self, log_entry):
        """Convertir avec SOURCE = Device détecté"""
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
        
        # 🔥 SOURCE = NOM COMPLET DEVICE (pas IP brute)
        source_display = f"{device['full_name']} ({ip})"
        
        return {
            'record_number': record_hash,
            'time_generated': log_entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            'source': source_display,  # ✅ SOURCE CORRECTE
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
        """Surveillance continue"""
        if not os.path.exists(self.syslog_path):
            raise Exception("Fichier Syslog introuvable")
        
        events = []
        self.reset_stop()
        
        # 🔥 RESET COMPTEURS
        self.reset_debug_counters()
        
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
                
                log_entry = self.parse_line(line)
                
                if not log_entry:
                    continue
                
                if self.last_timestamp and log_entry['timestamp'] <= self.last_timestamp:
                    continue
                
                if not latest_timestamp or log_entry['timestamp'] > latest_timestamp:
                    latest_timestamp = log_entry['timestamp']
                
                event = self.convert_to_event(log_entry)
                events.append(event)
            
            self.last_position = total_lines
            
            if latest_timestamp:
                self.last_timestamp = latest_timestamp
            
            self.save_state()
            
            # 🔥 AFFICHER RAPPORT SI 0 ÉVÉNEMENT
            if len(events) == 0 and self.debug_total_lines > 0:
                self.show_debug_report()
            
            return events
            
        except Exception as e:
            self.log(f"❌ Erreur Syslog: {str(e)}", silent=False)
            raise
    
    def read_initial_check(self, hours=24):
        """Scan complet"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        self.log(f"📅 SCAN COMPLET Syslog {hours}h...")
        
        if not os.path.exists(self.syslog_path):
            raise Exception("Fichier Syslog introuvable")
        
        events = []
        self.reset_stop()
        
        # 🔥 RESET COMPTEURS
        self.reset_debug_counters()
        
        try:
            self.log("📂 Lecture COMPLÈTE du fichier...")
            
            with open(self.syslog_path, 'r', encoding='utf-8', errors='replace') as f:
                all_lines = f.readlines()
            
            self.log(f"   📖 Total lignes: {len(all_lines)}")
            
            for i, line in enumerate(all_lines):
                if i % 1000 == 0 and self.stop_requested:
                    break
                
                if not line.strip():
                    continue
                
                log_entry = self.parse_line(line)
                
                if not log_entry:
                    continue
                
                if log_entry['timestamp'] < cutoff_time:
                    continue
                
                event = self.convert_to_event(log_entry)
                events.append(event)
            
            self.last_position = len(all_lines)
            self.save_state()
            
            # 🔥 TOUJOURS AFFICHER RAPPORT DIAGNOSTIC
            self.show_debug_report()
            
            self.log(f"\n📊 SCAN RÉSULTAT:")
            self.log(f"   ✅ ÉVÉNEMENTS RETOURNÉS: {len(events)}")
            
            return events
            
        except Exception as e:
            self.log(f"❌ Erreur: {str(e)}")
            raise
    
    def read_startup_check(self):
        """Lecture démarrage"""
        cutoff_time = datetime.now() - timedelta(minutes=5)
        self.log(f"⏰ DÉMARRAGE - Scan 5 dernières minutes...")
        
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
            self.log(f"📊 DÉMARRAGE: {len(events)} événements (5 min)")
            
            return events
            
        except Exception as e:
            self.log(f"❌ Erreur: {str(e)}")
            raise
    
    def reset(self):
        """Réinitialise le lecteur"""
        self.last_position = 0
        self.last_timestamp = None
        self.processed_hashes.clear()
        self.stop_requested = False
        self.save_state()