"""
Lecteur Syslog OPTIMISÉ - Détection Temps Réel
Fichier : syslog_reader.py - REMPLACER L'ANCIEN
CORRECTIFS MAJEURS:
- Parser adapté au format réel des logs
- Détection des warnings ET errors
- Lecture toutes les 10 secondes
- Surveillance continue optimisée
"""
import os
import re
import json
from datetime import datetime, timedelta


class SyslogReader:
    """Lecteur Syslog optimisé pour détection temps réel"""
    
    MONITORED_DEVICES = {
        '192.168.10.254': {'name': 'Stormshield', 'type': 'firewall', 'icon': '🔥'},
        '192.168.10.10': {'name': 'Active Directory', 'type': 'server', 'icon': '🖥️'},
        '192.168.10.110': {'name': 'Serveur-IA', 'type': 'server', 'icon': '🤖'},
        '192.168.10.15': {'name': 'Switch Principal', 'type': 'switch', 'icon': '🔌'},
        '192.168.10.16': {'name': 'Switch Secondaire', 'type': 'switch', 'icon': '🔌'},
        '192.168.10.11': {'name': 'Borne WiFi', 'type': 'wifi', 'icon': '📡'}
    }
    
    # CORRECTIF: Scores ajustés pour détecter plus d'événements
    SEVERITY_SCORES = {
        'emerg': 10, 'emergency': 10, 'panic': 10,
        'alert': 9,
        'crit': 10, 'critical': 10,
        'err': 8, 'error': 8,
        'warning': 7, 'warn': 7,  # AUGMENTÉ de 6 à 7
        'notice': 5,  # AUGMENTÉ de 4 à 5
        'info': 3,
        'debug': 2,
    }
    
    CRITICAL_KEYWORDS = {
        # Sécurité - Niveau 10
        'attack': 10, 'intrusion': 10, 'breach': 10, 'exploit': 10,
        'malware': 10, 'virus': 10, 'ransomware': 10,
        
        # Authentification - Niveau 9
        'authentication': 9, 'unauthorized': 9, 'fail': 9, 'failed': 9,
        
        # Réseau - Niveau 8
        'deny': 8, 'denied': 8, 'drop': 8, 'dropped': 8,
        'block': 8, 'blocked': 8, 'reject': 8, 'rejected': 8,
        
        # Système - Niveau 7
        'error': 7, 'critical': 7, 'alert': 7, 'warning': 6,
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
        self.stats_warnings = 0
        self.stats_errors = 0
        self.stats_criticals = 0
        
        self.load_state()
    
    def log(self, message, silent=False):
        """Log un message"""
        if silent:
            return
        if self.log_callback:
            try:
                self.log_callback(message)
            except:
                print(message)
        else:
            print(message)
    
    def debug(self, message):
        if self.verbose:
            self.log(f"   [DEBUG] {message}")
    
    def load_state(self):
        """Charge l'état de lecture"""
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
        self.log("🛑 Arrêt Syslog demandé")
    
    def reset_stop(self):
        self.stop_requested = False
    
    def check_availability(self):
        """Vérifie la disponibilité"""
        if not os.path.exists(self.syslog_path):
            raise Exception(f"Fichier Syslog introuvable: {self.syslog_path}")
        
        try:
            with open(self.syslog_path, 'r', encoding='utf-8', errors='replace') as f:
                f.read(100)
            
            size_mb = os.path.getsize(self.syslog_path) / (1024 * 1024)
            self.log(f"✓ Syslog détecté: {size_mb:.2f} MB")
            return True
        except PermissionError:
            raise Exception("Accès refusé au fichier Syslog")
    
    def parse_syslog_line(self, line):
        """
        CORRECTIF FINAL: Parser adapté au FORMAT EXACT de vos logs
        Format: IP  Month Day Time Priority User Severity Timestamp Hostname Message
        Colonnes: [IP] [Mois Jour Heure] [Priority] [User] [SEVERITY] [ISO-Timestamp] [Hostname] [Message]
        
        Exemple: 192.168.10.254  Jan 12 08:58:54 1    user   warning    2026-01-14T09:01:31+01:00 SN310A41KL181A7 asqd...
        """
        try:
            line = line.strip()
            if not line or len(line) < 40:
                return None
            
            # MÉTHODE ROBUSTE: Split par espaces multiples et extraction par position
            parts = re.split(r'\s+', line)
            
            if len(parts) < 8:
                return None
            
            # 1. IP (première colonne)
            found_ip = parts[0]
            
            # Vérifier si IP surveillée
            if found_ip not in self.MONITORED_DEVICES:
                return None
            
            # 2. Timestamp (colonnes 1-3: Jan 12 08:49:40)
            timestamp = datetime.now()
            try:
                year = datetime.now().year
                month = parts[1]  # Jan
                day = parts[2]    # 12
                time_str = parts[3]  # 08:49:40
                timestamp_str = f"{year} {month} {day} {time_str}"
                timestamp = datetime.strptime(timestamp_str, "%Y %b %d %H:%M:%S")
            except:
                pass
            
            # 3. SEVERITY (colonne 5 - APRÈS "user")
            # Format: IP Mois Jour Heure Priority User [SEVERITY] ...
            #         0  1    2   3    4        5    [6]
            severity = "notice"
            if len(parts) > 5:
                potential_severity = parts[5].lower()
                # Vérifier que c'est bien une severity valide
                valid_severities = ['emerg', 'emergency', 'alert', 'crit', 'critical', 
                                  'err', 'error', 'warning', 'warn', 'notice', 'info', 'debug']
                if potential_severity in valid_severities:
                    severity = potential_severity
            
            # 4. Facility (chercher "asqd", "firewall", etc. dans le message)
            facility = "syslog"
            # Chercher dans les parties restantes
            for part in parts[7:]:
                if part in ['asqd', 'firewall', 'auth', 'kernel', 'system']:
                    facility = part
                    break
            
            result = {
                'timestamp': timestamp,
                'ip': found_ip,
                'facility': facility,
                'severity': severity,
                'message': line,
                'raw_line': line
            }
            
            return result
            
        except Exception as e:
            self.debug(f"✗ Erreur parsing: {e}")
            return None
    
    def get_event_priority(self, log_entry):
        """Calcule la priorité (1-10)"""
        max_score = 0
        indicators = []
        
        full_text = f"{log_entry['facility']} {log_entry['message']}".lower()
        
        # 1. Score basé sur severity
        severity = log_entry.get('severity', '').lower()
        if severity in self.SEVERITY_SCORES:
            sev_score = self.SEVERITY_SCORES[severity]
            max_score = max(max_score, sev_score)
            indicators.append(f"severity:{severity}({sev_score})")
        
        # 2. Score basé sur mots-clés
        for keyword, score in self.CRITICAL_KEYWORDS.items():
            if keyword in full_text:
                max_score = max(max_score, score)
                indicators.append(f"{keyword}({score})")
        
        # 3. Boost pour firewall
        facility = log_entry.get('facility', '').lower()
        if facility in ['firewall', 'asqd', 'filter', 'security', 'auth']:
            if max_score > 0:
                max_score = min(max_score + 1, 10)
                indicators.append("firewall_boost")
        
        # Score par défaut
        if max_score == 0:
            max_score = 3
        
        return max_score, indicators
    
    def should_process_log(self, log_entry):
        """
        CORRECTIF ULTRA-PERMISSIF: Détecte TOUT ce qui est >= notice
        Retourne: (should_process, reason, priority)
        """
        if log_entry['ip'] not in self.MONITORED_DEVICES:
            return False, "IP non surveillée", 0
        
        # CORRECTIF: Unpacker correctement le tuple
        priority, indicators = self.get_event_priority(log_entry)
        
        severity = log_entry.get('severity', 'notice').lower()
        facility = log_entry.get('facility', '').lower()
        
        # RÈGLE 1: TOUJOURS détecter les severities critiques
        if severity in ['emerg', 'emergency', 'alert', 'crit', 'critical']:
            self.stats_criticals += 1
            return True, f"🔴 CRITIQUE: {severity.upper()}", 10
        
        # RÈGLE 2: TOUJOURS détecter les errors
        if severity in ['err', 'error']:
            self.stats_errors += 1
            return True, f"🔴 ERROR: {severity.upper()}", 8
        
        # RÈGLE 3: TOUJOURS détecter les warnings
        if severity in ['warning', 'warn']:
            self.stats_warnings += 1
            return True, f"🟡 WARNING: {severity.upper()}", 7
        
        # RÈGLE 4: Détecter notices SI facility importante OU mots-clés critiques
        if severity == 'notice':
            # Facilities importantes
            critical_facilities = ['firewall', 'asqd', 'security', 'auth', 'filter']
            has_critical_facility = any(cf in facility for cf in critical_facilities)
            
            # Mots-clés critiques
            message_lower = log_entry.get('message', '').lower()
            critical_words = ['attack', 'fail', 'failed', 'deny', 'denied', 'drop', 'dropped',
                            'block', 'blocked', 'reject', 'rejected', 'unauthorized',
                            'intrusion', 'breach', 'malware', 'virus']
            has_critical_word = any(word in message_lower for word in critical_words)
            
            if has_critical_facility or has_critical_word:
                self.stats_warnings += 1
                return True, f"🟡 NOTICE importante: {facility}", 6
        
        # RÈGLE 5: Pour les équipements critiques, être plus permissif
        device_info = self.MONITORED_DEVICES.get(log_entry['ip'], {})
        if device_info.get('type') == 'firewall':
            # Pour firewall: capturer même les notices normaux si priorité >= 4
            if priority >= 4:
                self.stats_warnings += 1
                return True, f"🛡️ Firewall (p{priority})", priority
        
        # Par défaut: ignorer
        return False, f"Notice standard (p{priority})", priority
    
    def convert_to_event_format(self, log_entry):
        """Convertit en format événement"""
        device_info = self.MONITORED_DEVICES.get(
            log_entry['ip'], 
            {'name': 'Unknown', 'icon': '❓', 'type': 'unknown'}
        )
        
        priority, indicators = self.get_event_priority(log_entry)
        
        severity_ids = {
            'emerg': 10000, 'alert': 9000, 'crit': 8000,
            'err': 7000, 'error': 7000,
            'warning': 6000, 'warn': 6000,
            'notice': 5000, 'info': 4000, 'debug': 3000
        }
        
        severity = log_entry.get('severity', 'notice')
        event_id = severity_ids.get(severity, 5000)
        
        return {
            'record_number': hash(log_entry['raw_line']) % 1000000,
            'time_generated': log_entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            'source': f"{device_info['icon']} {device_info['name']} ({log_entry['ip']})",
            'event_id': event_id,
            'event_type': 'ERROR' if priority >= 7 else 'WARNING',
            'computer': log_entry['ip'],
            'message': f"[{log_entry['facility']}.{severity}] {log_entry['message'][:400]}",
            '_priority': priority,
            '_is_syslog': True,
            '_device_type': device_info.get('type', 'unknown'),
            '_device_name': device_info['name'],
            '_severity': severity,
            '_indicators': indicators
        }
    
    def get_line_hash(self, line):
        """Hash court d'une ligne"""
        core = line[20:220] if len(line) > 20 else line
        return hash(core) % 10000000
    
    def read_events(self, since_time=None, force_full_scan=False, silent=False):
        """
        Lecture des événements
        OPTIMISÉ: Lecture incrémentale rapide
        """
        if not os.path.exists(self.syslog_path):
            raise Exception("Fichier Syslog introuvable")
        
        events = []
        self.reset_stop()
        
        self.stats_total_lines = 0
        self.stats_warnings = 0
        self.stats_errors = 0
        self.stats_criticals = 0
        
        try:
            if not silent:
                self.log("📂 Lecture Syslog...")
            
            # Lire le fichier
            with open(self.syslog_path, 'r', encoding='utf-8', errors='replace') as f:
                all_lines = f.readlines()
            
            total_lines = len(all_lines)
            
            # Déterminer quelles lignes lire
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
            
            # Traitement
            new_hashes = set()
            latest_timestamp = self.last_timestamp
            
            for i, line in enumerate(lines_to_process):
                if i % 50 == 0 and self.stop_requested:
                    break
                
                self.stats_total_lines += 1
                
                if not line.strip():
                    continue
                
                # Anti-doublon
                line_hash = self.get_line_hash(line)
                if line_hash in self.processed_hashes:
                    continue
                
                new_hashes.add(line_hash)
                
                # Parser
                log_entry = self.parse_syslog_line(line)
                
                if log_entry:
                    # Vérifier timestamp
                    if self.last_timestamp and log_entry['timestamp'] <= self.last_timestamp:
                        continue
                    
                    # Mettre à jour dernier timestamp
                    if not latest_timestamp or log_entry['timestamp'] > latest_timestamp:
                        latest_timestamp = log_entry['timestamp']
                    
                    # Filtrer par date si nécessaire
                    if since_time and log_entry['timestamp'] < since_time:
                        continue
                    
                    # Vérifier si doit être traité
                    should_process, reason, priority = self.should_process_log(log_entry)
                    
                    if should_process:
                        event = self.convert_to_event_format(log_entry)
                        event['_priority'] = priority
                        events.append(event)
            
            # Sauvegarder état
            if not force_full_scan:
                self.last_position = total_lines
            
            if latest_timestamp:
                self.last_timestamp = latest_timestamp
            
            # Mettre à jour hashes
            self.processed_hashes.update(new_hashes)
            if len(self.processed_hashes) > 10000:
                self.processed_hashes = set(list(self.processed_hashes)[-10000:])
            
            self.save_state()
            
            # Affichage résumé (uniquement si événements ET pas silencieux)
            if events and not silent:
                self.log(f"\n📊 SYSLOG RÉSULTAT:")
                self.log(f"   • Lignes scannées: {self.stats_total_lines}")
                self.log(f"   🔴 Critiques: {self.stats_criticals}")
                self.log(f"   🟡 Warnings: {self.stats_warnings}")
                self.log(f"   📊 TOTAL: {len(events)}")
            
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
        """
        OPTIMISÉ: Surveillance continue SILENCIEUSE
        Mode rapide pour détection temps réel
        """
        return self.read_events(force_full_scan=False, silent=True)
    
    def reset(self):
        """Réinitialise"""
        self.last_position = 0
        self.last_timestamp = None
        self.processed_hashes.clear()
        self.stop_requested = False
        self.save_state()
        self.log("🔄 SyslogReader réinitialisé")