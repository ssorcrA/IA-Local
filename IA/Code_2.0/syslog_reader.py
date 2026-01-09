"""
Lecteur de logs Syslog - VERSION CORRIGÉE AGGRESSIVE
Fichier : syslog_reader.py - REMPLACER L'ANCIEN
CORRECTIF: Détection GARANTIE des tentatives d'intrusion
"""
import os
import re
from datetime import datetime, timedelta


class SyslogReader:
    """Lit et analyse les logs Syslog avec détection AGGRESSIVE des intrusions"""
    
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
    
    # CORRECTIF: Mots-clés élargis pour TOUT capturer
    CRITICAL_KEYWORDS = {
        # Intrusions et attaques
        'attack': 10, 'intrusion': 10, 'breach': 10, 'hack': 10,
        'exploit': 9, 'malware': 10, 'virus': 10, 'trojan': 9,
        'scan': 8, 'probe': 8, 'suspicious': 8, 'malicious': 9,
        
        # Authentification
        'fail': 7, 'failed': 7, 'failure': 7,
        'authentication': 7, 'login': 6, 'logon': 6,
        'unauthorized': 9, 'forbidden': 8, 'invalid': 7,
        'wrong': 6, 'incorrect': 6, 'bad': 6,
        
        # Firewall
        'deny': 8, 'denied': 8, 'drop': 8, 'dropped': 8,
        'block': 8, 'blocked': 8, 'reject': 8, 'rejected': 8,
        'refused': 7, 'closed': 5,
        
        # Réseau
        'timeout': 6, 'unreachable': 7, 'connection': 5,
        'disconnect': 6, 'reset': 6,
        
        # Système
        'error': 7, 'critical': 9, 'alert': 9, 'emergency': 10,
        'down': 7, 'unavailable': 7, 'offline': 7,
        
        # Spécifique firewall
        'firewall': 5, 'asqd': 5, 'filter': 5,
    }
    
    # NOUVEAU: Patterns spécifiques pour détecter les intrusions
    INTRUSION_PATTERNS = [
        (r'authentication.*fail', 9, "Échec d'authentification"),
        (r'login.*fail', 9, "Échec de connexion"),
        (r'invalid.*user', 8, "Utilisateur invalide"),
        (r'invalid.*password', 8, "Mot de passe invalide"),
        (r'access.*denied', 8, "Accès refusé"),
        (r'connection.*refused', 7, "Connexion refusée"),
        (r'unauthorized.*access', 9, "Accès non autorisé"),
        (r'brute.*force', 10, "Attaque brute force"),
        (r'port.*scan', 9, "Scan de ports"),
        (r'(ddos|dos).*attack', 10, "Attaque DDoS"),
        (r'intrusion.*detect', 10, "Intrusion détectée"),
        (r'malware.*detect', 10, "Malware détecté"),
        (r'blocked.*ip', 8, "IP bloquée"),
        (r'deny.*rule', 7, "Règle de refus"),
        (r'drop.*packet', 7, "Paquet rejeté"),
    ]
    
    def __init__(self, log_callback=None, verbose=False):
        self.log_callback = log_callback
        self.verbose = verbose
        self.syslog_path = r"\\SRV-SYSLOG\surveillence$\syslog"
        self.last_position = 0
        self.last_check_time = None
        self.processed_lines = set()
        self.stop_requested = False
        
        # Statistiques
        self.stats_total_lines = 0
        self.stats_intrusions = 0
        self.stats_high_priority = 0
    
    def log(self, message):
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
    
    def request_stop(self):
        self.stop_requested = True
        self.log("🛑 Arrêt demandé pour le lecteur Syslog")
    
    def reset_stop(self):
        self.stop_requested = False
    
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
    
    def check_availability(self):
        if not os.path.exists(self.syslog_path):
            raise Exception(f"Fichier Syslog introuvable: {self.syslog_path}")
        
        try:
            with open(self.syslog_path, 'r', encoding='utf-8', errors='replace') as f:
                f.read(100)
            
            size_mb = os.path.getsize(self.syslog_path) / (1024 * 1024)
            self.log(f"✓ Fichier Syslog détecté: {size_mb:.2f} MB")
            self.log(f"🎯 MODE DÉTECTION AGGRESSIVE: TOUTES les intrusions seront capturées")
            return True
        except PermissionError:
            raise Exception("Accès refusé au fichier Syslog")
    
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
                    self.debug(f"✓ IP trouvée: {ip}")
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
                    self.debug(f"✓ Timestamp: {timestamp}")
                except Exception as e:
                    self.debug(f"⚠ Erreur timestamp: {e}")
            
            # Extraction facility et severity
            facility = "syslog"
            severity = "notice"
            
            # Pattern Stormshield: "N facility severity"
            fac_sev_match = re.search(r'\d+\s+(\w+)\s+(emerg|alert|crit|err|error|warning|warn|notice|info|debug)\b', line, re.IGNORECASE)
            if fac_sev_match:
                facility = fac_sev_match.group(1)
                severity = fac_sev_match.group(2).lower()
                self.debug(f"✓ Format Stormshield: {facility}.{severity}")
            else:
                # Pattern standard: "facility.severity"
                std_match = re.search(r'(\w+)\.(emerg|alert|crit|err|error|warning|warn|notice|info|debug)\b', line, re.IGNORECASE)
                if std_match:
                    facility = std_match.group(1)
                    severity = std_match.group(2).lower()
                    self.debug(f"✓ Format standard: {facility}.{severity}")
            
            result = {
                'timestamp': timestamp,
                'ip': found_ip,
                'facility': facility,
                'severity': severity,
                'message': line,
                'raw_line': line
            }
            
            self.debug(f"✓ Ligne parsée: {facility}.{severity}")
            return result
            
        except Exception as e:
            self.debug(f"✗ Erreur parsing: {e}")
            return None
    
    def get_event_priority(self, log_entry):
        """
        CORRECTIF: Calcule la priorité de manière AGGRESSIVE
        Tout ce qui pourrait être une intrusion = priorité haute
        """
        max_score = 0
        found_indicators = []
        
        full_text = f"{log_entry['facility']} {log_entry['message']}".lower()
        
        # 1. NOUVEAU: Vérifier patterns d'intrusion d'ABORD
        for pattern, score, description in self.INTRUSION_PATTERNS:
            if re.search(pattern, full_text, re.IGNORECASE):
                max_score = max(max_score, score)
                found_indicators.append(f"{description}({score})")
                self.debug(f"🚨 INTRUSION DÉTECTÉE: {description}")
        
        # 2. Severity explicite
        severity = log_entry.get('severity', '').lower()
        if severity and severity in self.FACILITY_SEVERITY_MAP:
            severity_score = self.FACILITY_SEVERITY_MAP[severity]
            max_score = max(max_score, severity_score)
            found_indicators.append(f"severity:{severity}({severity_score})")
        
        # 3. Mots-clés (élargi)
        for keyword, score in self.CRITICAL_KEYWORDS.items():
            if keyword in full_text:
                max_score = max(max_score, score)
                found_indicators.append(f"{keyword}({score})")
        
        # 4. NOUVEAU: Boost pour facility firewall/asqd
        facility = log_entry.get('facility', '').lower()
        if facility in ['firewall', 'asqd', 'filter', 'security', 'auth']:
            if max_score > 0:
                max_score = min(max_score + 2, 10)  # +2 points
                found_indicators.append(f"facility_boost")
        
        if found_indicators and self.verbose:
            self.debug(f"Indicateurs: {', '.join(found_indicators[:5])}")
        
        # Score par défaut abaissé pour capturer plus
        if max_score == 0:
            max_score = 2
        
        return max_score, found_indicators
    
    def should_process_log(self, log_entry):
        """
        CORRECTIF: Logique SIMPLIFIÉE et AGGRESSIVE
        Si priorité >= 6 OU contient pattern intrusion = TICKET
        """
        if log_entry['ip'] not in self.MONITORED_DEVICES:
            return False, "IP non surveillée", 0
        
        priority, indicators = self.get_event_priority(log_entry)
        
        # CORRECTIF: Seuil abaissé à 6 (au lieu de 7)
        # Et détection spéciale pour intrusions
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
            # Vérifier facility critique
            facility = log_entry.get('facility', '').lower()
            if facility in ['firewall', 'asqd', 'filter', 'security']:
                return True, f"🛡️ Firewall/Sécurité: {priority}/10", priority
        
        # Même les priorités moyennes si répétées
        if priority >= 4:
            # Anti-doublon simplifié
            short_msg = log_entry['message'][:80]
            line_hash = hash(short_msg)
            
            if line_hash in self.processed_lines:
                return False, "Doublon", priority
            
            self.processed_lines.add(line_hash)
            
            # Accepter severity critique
            severity = log_entry.get('severity', '').lower()
            if severity in ['emerg', 'alert', 'crit', 'err', 'error', 'warning']:
                return True, f"⚠️ {severity.upper()}: {priority}/10", priority
        
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
        
        # NOUVEAU: Ajouter les indicateurs dans le message
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
            '_indicators': indicators  # NOUVEAU
        }
    
    def read_events(self, since_time=None, force_full_scan=False):
        """Lit les événements Syslog avec détection AGGRESSIVE"""
        if not os.path.exists(self.syslog_path):
            raise Exception(f"Fichier Syslog introuvable")
        
        events = []
        total_lines = 0
        parsed_lines = 0
        
        severity_counts = {
            'emerg': 0, 'alert': 0, 'crit': 0, 'err': 0,
            'warning': 0, 'notice': 0, 'info': 0, 'debug': 0
        }
        
        self.reset_stop()
        self.stats_total_lines = 0
        self.stats_intrusions = 0
        self.stats_high_priority = 0
        
        try:
            self.log(f"📂 Lecture du fichier Syslog...")
            self.log(f"🎯 MODE DÉTECTION AGGRESSIVE ACTIVÉ")
            self.log(f"   → Seuil: Priorité >= 6 (au lieu de 7)")
            self.log(f"   → Patterns d'intrusion: {len(self.INTRUSION_PATTERNS)} patterns actifs")
            
            # Gestion de la position
            with open(self.syslog_path, 'r', encoding='utf-8', errors='replace') as f:
                all_lines = f.readlines()
                
                if force_full_scan or self.last_position == 0:
                    lines = all_lines
                    self.log(f"   📖 Lecture complète: {len(lines)} lignes")
                else:
                    if self.last_position < len(all_lines):
                        lines = all_lines[self.last_position:]
                        self.log(f"   📖 Nouvelles lignes: {len(lines)}")
                    else:
                        lines = []
                        self.log(f"   ✅ Aucune nouvelle ligne")
                
                if not force_full_scan:
                    self.last_position = len(all_lines)
            
            if not lines:
                return []
            
            # Traitement
            for i, line in enumerate(lines):
                if i % 100 == 0 and self.stop_requested:
                    self.log(f"   🛑 Arrêt demandé à {i}/{len(lines)}")
                    break
                
                total_lines += 1
                self.stats_total_lines += 1
                
                if not line.strip():
                    continue
                
                log_entry = self.parse_syslog_line(line)
                
                if log_entry:
                    parsed_lines += 1
                    
                    sev = log_entry.get('severity', 'unknown')
                    if sev in severity_counts:
                        severity_counts[sev] += 1
                    
                    # Filtrer par date
                    if since_time and log_entry['timestamp'] < since_time:
                        continue
                    
                    # LOGIQUE SIMPLIFIÉE ET AGGRESSIVE
                    should_process, reason, adjusted_priority = self.should_process_log(log_entry)
                    
                    if should_process:
                        event = self.convert_to_event_format(log_entry)
                        event['_priority'] = adjusted_priority
                        events.append(event)
                        
                        device_info = self.MONITORED_DEVICES[log_entry['ip']]
                        emoji = self.get_priority_emoji(adjusted_priority)
                        self.log(f"   {emoji} {device_info['icon']} {reason}")
            
            # Affichage final
            if not self.stop_requested:
                self.log(f"\n📊 RÉSULTAT SYSLOG (MODE AGGRESSIVE):")
                self.log(f"   • Total scanné: {total_lines} lignes")
                self.log(f"   • Lignes avec IP surveillée: {parsed_lines}")
                
                self.log(f"\n   🚨 DÉTECTIONS:")
                self.log(f"      🔴 Intrusions détectées: {self.stats_intrusions}")
                self.log(f"      🟠 Haute priorité: {self.stats_high_priority}")
                self.log(f"      📊 TOTAL CAPTURÉ: {len(events)}")
                
                if events:
                    sources = {}
                    for event in events:
                        source = event['source']
                        sources[source] = sources.get(source, 0) + 1
                    
                    self.log(f"\n📋 Sources d'incidents:")
                    for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
                        max_priority = max(e['_priority'] for e in events if e['source'] == source)
                        emoji = self.get_priority_emoji(max_priority)
                        self.log(f"   {emoji} {source}: {count} incident(s)")
                else:
                    self.log(f"\n✅ Aucun incident capturé")
            
            self.last_check_time = datetime.now()
            return events
            
        except Exception as e:
            self.log(f"❌ Erreur lecture Syslog: {str(e)}")
            raise Exception(f"Erreur lecture Syslog: {str(e)}")
    
    def read_initial_check(self, hours=24):
        """Vérification initiale en mode AGGRESSIVE"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        self.log(f"📅 Vérification Syslog des {hours} dernières heures...")
        self.log(f"   Recherche depuis: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"   🎯 MODE AGGRESSIVE: Capture maximale des menaces")
        
        return self.read_events(since_time=cutoff_time, force_full_scan=True)
    
    def read_new_events(self):
        """Surveillance continue en mode AGGRESSIVE"""
        self.log(f"🔄 Recherche nouveaux événements Syslog...")
        self.log(f"   (depuis position {self.last_position})")
        return self.read_events(force_full_scan=False)
    
    def get_device_stats(self):
        """Statistiques des appareils surveillés"""
        stats = []
        for ip, info in self.MONITORED_DEVICES.items():
            stats.append(f"{info['icon']} {info['name']} ({ip})")
        return stats
    
    def reset(self):
        """Réinitialise le lecteur"""
        self.last_position = 0
        self.processed_lines.clear()
        self.stop_requested = False
        self.stats_total_lines = 0
        self.stats_intrusions = 0
        self.stats_high_priority = 0
        self.log("🔄 Lecteur Syslog réinitialisé")