"""
Lecteur de logs Syslog - VERSION CORRIGÉE COMPLÈTE
Fichier : syslog_reader.py
CORRECTIFS:
- Logs masqués en mode surveillance
- Sauvegarde de la dernière position + timestamp
- Aucun doublon
- Arrêt immédiat quand demandé
"""
import os
import re
import json
from datetime import datetime, timedelta


class SyslogReader:
    """Lit et analyse les logs Syslog SANS DOUBLONS"""
    
    MONITORED_DEVICES = {
        '192.168.1.254': {'name': 'Stormshield', 'type': 'firewall', 'icon': '🔥'},
        '192.168.10.254': {'name': 'Stormshield', 'type': 'firewall', 'icon': '🔥'},
        '192.168.1.15': {'name': 'Switch', 'type': 'switch', 'icon': '🔌'},
        '192.168.1.11': {'name': 'Borne WiFi', 'type': 'wifi', 'icon': '📡'}
    }
    
    FACILITY_SEVERITY_MAP = {
        'emerg': 10, 'emergency': 10,
        'alert': 9,
        'crit': 10, 'critical': 10,
        'err': 8, 'error': 8,
        'warning': 6, 'warn': 6,
        'notice': 4,
        'info': 3,
        'debug': 2,
    }
    
    CRITICAL_KEYWORDS = {
        'attack': 10, 'intrusion': 10, 'breach': 10,
        'exploit': 9, 'malware': 10, 'virus': 10,
        'fail': 7, 'failed': 7, 'failure': 7,
        'authentication': 7, 'unauthorized': 9,
        'deny': 8, 'denied': 8, 'drop': 8, 'dropped': 8,
        'block': 8, 'blocked': 8, 'reject': 8,
        'error': 7, 'critical': 9, 'alert': 9,
    }
    
    INTRUSION_PATTERNS = [
        (r'authentication.*fail', 9, "Échec d'authentification"),
        (r'login.*fail', 9, "Échec de connexion"),
        (r'invalid.*user', 8, "Utilisateur invalide"),
        (r'access.*denied', 8, "Accès refusé"),
        (r'unauthorized.*access', 9, "Accès non autorisé"),
        (r'brute.*force', 10, "Attaque brute force"),
        (r'port.*scan', 9, "Scan de ports"),
        (r'intrusion.*detect', 10, "Intrusion détectée"),
        (r'blocked.*ip', 8, "IP bloquée"),
    ]
    
    def __init__(self, log_callback=None, verbose=False):
        self.log_callback = log_callback
        self.verbose = verbose
        self.syslog_path = r"\\SRV-SYSLOG\surveillence$\syslog"
        self.state_file = r"C:\IA\.syslog_state.json"
        
        # État de lecture
        self.last_position = 0
        self.last_timestamp = None  # NOUVEAU: dernière heure de log traité
        self.processed_hashes = set()
        
        self.stop_requested = False
        
        # Charger l'état
        self.load_state()
        
        # Statistiques
        self.stats_total_lines = 0
        self.stats_intrusions = 0
        self.stats_high_priority = 0
    
    def log(self, message, silent=False):
        """Log un message (peut être silencieux)"""
        if silent:
            return  # Ne rien afficher en mode silencieux
        
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
        """Charge l'état de lecture précédent"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    self.last_position = state.get('last_position', 0)
                    last_ts = state.get('last_timestamp')
                    
                    if last_ts:
                        self.last_timestamp = datetime.fromisoformat(last_ts)
                    
                    self.debug(f"État chargé: position={self.last_position}, last_time={self.last_timestamp}")
        except Exception as e:
            self.debug(f"Erreur chargement état: {e}")
    
    def save_state(self):
        """Sauvegarde l'état de lecture"""
        try:
            state = {
                'last_position': self.last_position,
                'last_timestamp': self.last_timestamp.isoformat() if self.last_timestamp else None,
                'last_save': datetime.now().isoformat()
            }
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
            
            self.debug(f"État sauvegardé: position={self.last_position}")
        except Exception as e:
            self.debug(f"Erreur sauvegarde état: {e}")
    
    def request_stop(self):
        """Demande d'arrêt immédiat"""
        self.stop_requested = True
        self.log("🛑 Arrêt demandé pour le lecteur Syslog", silent=False)
    
    def reset_stop(self):
        self.stop_requested = False
    
    def get_priority_emoji(self, priority):
        if priority >= 9:
            return "🔴"
        elif priority >= 7:
            return "🟠"
        elif priority >= 5:
            return "🟡"
        else:
            return "🟢"
    
    def check_availability(self):
        """Vérifie la disponibilité du fichier Syslog"""
        if not os.path.exists(self.syslog_path):
            raise Exception(f"Fichier Syslog introuvable: {self.syslog_path}")
        
        try:
            with open(self.syslog_path, 'r', encoding='utf-8', errors='replace') as f:
                f.read(100)
            
            size_mb = os.path.getsize(self.syslog_path) / (1024 * 1024)
            self.log(f"✓ Fichier Syslog détecté: {size_mb:.2f} MB")
            
            if self.last_position > 0:
                self.log(f"📌 Reprise depuis position: {self.last_position}")
            if self.last_timestamp:
                self.log(f"⏰ Dernier événement traité: {self.last_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            
            return True
        except PermissionError:
            raise Exception("Accès refusé au fichier Syslog")
    
    def get_line_hash(self, line):
        """Génère un hash court d'une ligne"""
        core = line[20:220] if len(line) > 20 else line
        return hash(core) % 10000000
    
    def parse_syslog_line(self, line):
        """Parse une ligne Syslog format Stormshield"""
        try:
            line = line.strip()
            if not line or len(line) < 20:
                return None
            
            # Recherche IP au début
            found_ip = None
            for ip in self.MONITORED_DEVICES.keys():
                if line.startswith(ip):
                    found_ip = ip
                    break
            
            if not found_ip:
                return None
            
            # Extraction timestamp
            timestamp = datetime.now()
            time_match = re.search(r'(\w+)\s+(\d+)\s+(\d+:\d+:\d+)', line)
            if time_match:
                try:
                    current_year = datetime.now().year
                    time_str = f"{current_year} {time_match.group(1)} {time_match.group(2)} {time_match.group(3)}"
                    timestamp = datetime.strptime(time_str, "%Y %b %d %H:%M:%S")
                except:
                    pass
            
            # Extraction facility et severity
            facility = "syslog"
            severity = "notice"
            
            fac_sev_match = re.search(r'\d+\s+(\w+)\s+(emerg|alert|crit|err|error|warning|warn|notice|info|debug)\b', line, re.IGNORECASE)
            if fac_sev_match:
                facility = fac_sev_match.group(1)
                severity = fac_sev_match.group(2).lower()
            
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
        """Calcule la priorité"""
        max_score = 0
        found_indicators = []
        
        full_text = f"{log_entry['facility']} {log_entry['message']}".lower()
        
        # 1. Patterns d'intrusion
        for pattern, score, description in self.INTRUSION_PATTERNS:
            if re.search(pattern, full_text, re.IGNORECASE):
                max_score = max(max_score, score)
                found_indicators.append(f"{description}({score})")
        
        # 2. Severity explicite
        severity = log_entry.get('severity', '').lower()
        if severity and severity in self.FACILITY_SEVERITY_MAP:
            severity_score = self.FACILITY_SEVERITY_MAP[severity]
            max_score = max(max_score, severity_score)
            found_indicators.append(f"severity:{severity}({severity_score})")
        
        # 3. Mots-clés
        for keyword, score in self.CRITICAL_KEYWORDS.items():
            if keyword in full_text:
                max_score = max(max_score, score)
                found_indicators.append(f"{keyword}({score})")
        
        # 4. Boost pour facility firewall
        facility = log_entry.get('facility', '').lower()
        if facility in ['firewall', 'asqd', 'filter', 'security', 'auth']:
            if max_score > 0:
                max_score = min(max_score + 2, 10)
                found_indicators.append(f"facility_boost")
        
        if max_score == 0:
            max_score = 2
        
        return max_score, found_indicators
    
    def should_process_log(self, log_entry):
        """Détermine si un log doit être traité"""
        if log_entry['ip'] not in self.MONITORED_DEVICES:
            return False, "IP non surveillée", 0
        
        priority, indicators = self.get_event_priority(log_entry)
        
        # Détection spéciale intrusions
        is_intrusion = any('intrusion' in str(ind).lower() or 'fail' in str(ind).lower() 
                          or 'attack' in str(ind).lower() or 'denied' in str(ind).lower()
                          for ind in indicators)
        
        if is_intrusion:
            self.stats_intrusions += 1
            return True, f"🚨 INTRUSION: {', '.join(indicators[:2])}", max(priority, 8)
        
        if priority >= 7:
            self.stats_high_priority += 1
            return True, f"🔴 Priorité critique: {priority}/10", priority
        
        if priority >= 6:
            facility = log_entry.get('facility', '').lower()
            if facility in ['firewall', 'asqd', 'filter', 'security']:
                return True, f"🛡️ Firewall/Sécurité: {priority}/10", priority
        
        return False, f"Priorité trop basse ({priority}/10)", priority
    
    def convert_to_event_format(self, log_entry):
        """Convertit en format événement standard"""
        device_info = self.MONITORED_DEVICES.get(
            log_entry['ip'], 
            {'name': 'Unknown', 'icon': '❓', 'type': 'unknown'}
        )
        
        priority, indicators = self.get_event_priority(log_entry)
        
        severity_ids = {
            'emerg': 10000, 'alert': 9000, 'crit': 8000,
            'err': 7000, 'error': 7000,
            'warning': 6000, 'warn': 6000,
            'notice': 5000,
            'info': 4000,
            'debug': 3000
        }
        
        severity = log_entry.get('severity', 'notice')
        event_id = severity_ids.get(severity, 5000)
        
        indicators_str = " | ".join(indicators[:3]) if indicators else ""
        
        return {
            'record_number': hash(log_entry['raw_line']) % 1000000,
            'time_generated': log_entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            'source': f"{device_info['icon']} {device_info['name']} ({log_entry['ip']})",
            'event_id': event_id,
            'event_type': 'ERROR' if priority >= 7 else 'WARNING',
            'computer': log_entry['ip'],
            'message': f"[{log_entry['facility']}.{severity}] {log_entry['message'][:400]}\n🔍 Détection: {indicators_str}",
            '_priority': priority,
            '_is_syslog': True,
            '_device_type': device_info.get('type', 'unknown'),
            '_device_name': device_info['name'],
            '_severity': severity,
            '_indicators': indicators
        }
    
    def read_events(self, since_time=None, force_full_scan=False, silent=False):
        """
        Lit les événements Syslog SANS DOUBLONS
        silent=True: mode surveillance (aucun log sauf résultats)
        """
        if not os.path.exists(self.syslog_path):
            raise Exception(f"Fichier Syslog introuvable")
        
        events = []
        
        self.reset_stop()
        self.stats_total_lines = 0
        self.stats_intrusions = 0
        self.stats_high_priority = 0
        
        try:
            if not silent:
                self.log(f"📂 Lecture du fichier Syslog...")
            
            # Lire tout le fichier
            with open(self.syslog_path, 'r', encoding='utf-8', errors='replace') as f:
                all_lines = f.readlines()
            
            total_lines = len(all_lines)
            
            # Déterminer quelles lignes lire
            if force_full_scan or self.last_position == 0:
                lines_to_process = all_lines
                if not silent:
                    self.log(f"   📖 Lecture complète: {len(lines_to_process)} lignes")
            else:
                if self.last_position < total_lines:
                    lines_to_process = all_lines[self.last_position:]
                    # MODE SILENCIEUX: ne rien afficher
                else:
                    lines_to_process = []
                    # MODE SILENCIEUX: ne rien afficher
            
            if not lines_to_process:
                self.save_state()
                return []
            
            # Traitement
            new_hashes = set()
            latest_timestamp = self.last_timestamp
            
            for i, line in enumerate(lines_to_process):
                # Vérifier arrêt tous les 50 lignes
                if i % 50 == 0 and self.stop_requested:
                    if not silent:
                        self.log(f"   🛑 Arrêt demandé à {i}/{len(lines_to_process)}")
                    break
                
                self.stats_total_lines += 1
                
                if not line.strip():
                    continue
                
                # Vérifier si déjà traité (anti-doublon)
                line_hash = self.get_line_hash(line)
                if line_hash in self.processed_hashes:
                    continue
                
                new_hashes.add(line_hash)
                
                log_entry = self.parse_syslog_line(line)
                
                if log_entry:
                    # NOUVEAU: Vérifier le timestamp pour éviter les anciens logs
                    if self.last_timestamp and log_entry['timestamp'] <= self.last_timestamp:
                        continue  # Ignorer les logs plus anciens
                    
                    # Mettre à jour le dernier timestamp
                    if not latest_timestamp or log_entry['timestamp'] > latest_timestamp:
                        latest_timestamp = log_entry['timestamp']
                    
                    # Filtrer par date si nécessaire
                    if since_time and log_entry['timestamp'] < since_time:
                        continue
                    
                    should_process, reason, adjusted_priority = self.should_process_log(log_entry)
                    
                    if should_process:
                        event = self.convert_to_event_format(log_entry)
                        event['_priority'] = adjusted_priority
                        events.append(event)
                        
                        # MODE SILENCIEUX: ne rien afficher pendant le scan
            
            # Mettre à jour l'état
            if not force_full_scan:
                self.last_position = total_lines
            
            # Mettre à jour le dernier timestamp
            if latest_timestamp:
                self.last_timestamp = latest_timestamp
            
            # Mettre à jour les hash traités
            self.processed_hashes.update(new_hashes)
            if len(self.processed_hashes) > 10000:
                self.processed_hashes = set(list(self.processed_hashes)[-10000:])
            
            self.save_state()
            
            # Affichage final (uniquement si des événements trouvés ET pas en mode silencieux)
            if events:
                if not silent:
                    self.log(f"\n📊 RÉSULTAT SYSLOG:")
                    self.log(f"   • Total scanné: {self.stats_total_lines} lignes")
                    self.log(f"   🚨 Intrusions détectées: {self.stats_intrusions}")
                    self.log(f"   🟠 Haute priorité: {self.stats_high_priority}")
                    self.log(f"   📊 TOTAL CAPTURÉ: {len(events)}")
                else:
                    # En mode silencieux, juste un résumé minimaliste
                    self.log(f"📊 Syslog: {len(events)} événement(s) détecté(s)", silent=False)
            
            return events
            
        except Exception as e:
            self.log(f"❌ Erreur lecture Syslog: {str(e)}", silent=False)
            raise Exception(f"Erreur lecture Syslog: {str(e)}")
    
    def read_initial_check(self, hours=24):
        """Vérification initiale"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        self.log(f"📅 Vérification Syslog des {hours} dernières heures...")
        self.log(f"   Recherche depuis: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return self.read_events(since_time=cutoff_time, force_full_scan=True, silent=False)
    
    def read_new_events(self):
        """Surveillance continue - MODE SILENCIEUX"""
        # MODE SILENCIEUX: aucun log pendant le scan
        return self.read_events(force_full_scan=False, silent=True)
    
    def get_device_stats(self):
        """Statistiques des appareils surveillés"""
        stats = []
        for ip, info in self.MONITORED_DEVICES.items():
            stats.append(f"{info['icon']} {info['name']} ({ip})")
        return stats
    
    def reset(self):
        """Réinitialise le lecteur"""
        self.last_position = 0
        self.last_timestamp = None
        self.processed_hashes.clear()
        self.stop_requested = False
        self.save_state()
        self.log("🔄 Lecteur Syslog réinitialisé")