"""
Lecteur de logs Syslog - DÉTECTION ULTRA-SENSIBLE
Fichier : syslog_reader.py - VERSION CORRIGÉE
"""
import os
import re
from datetime import datetime, timedelta


class SyslogReader:
    """Lit et analyse les logs Syslog avec détection garantie"""
    
    MONITORED_DEVICES = {
        '192.168.1.254': {'name': 'Stormshield', 'type': 'firewall', 'icon': '🔥'},
        '192.168.1.15': {'name': 'Switch', 'type': 'switch', 'icon': '🔌'},
        '192.168.1.11': {'name': 'Borne WiFi', 'type': 'wifi', 'icon': '📡'}
    }
    
    # MOTS-CLÉS CRITIQUES - DÉTECTION MAXIMALE
    CRITICAL_KEYWORDS = {
        # Niveau 10 - CRITIQUE
        'attack': 10, 'intrusion': 10, 'breach': 10, 'hack': 10, 
        'exploit': 10, 'malware': 10, 'unauthorized': 10, 'denied': 10,
        'critical': 10, 'emergency': 10, 'panic': 10, 'crit': 10,
        
        # Niveau 9 - TRÈS HAUTE
        'blocked': 9, 'block': 9, 'deny': 9, 'drop': 9, 
        'dropped': 9, 'reject': 9, 'rejected': 9, 'alert': 9,
        
        # Niveau 8 - HAUTE
        'fail': 8, 'failed': 8, 'failure': 8, 'error': 8, 'err': 8,
        'fatal': 8, 'severe': 8,
        
        # Niveau 7 - MOYENNE-HAUTE  
        'timeout': 7, 'unreachable': 7, 'down': 7, 'offline': 7,
        
        # Niveau 6 - MOYENNE
        'warning': 6, 'warn': 6, 'problem': 6, 'issue': 6,
        
        # Niveau 5 - BASSE
        'notice': 5, 'info': 5,
        
        # Niveau 4 - TRÈS BASSE
        'debug': 4,
    }
    
    # Niveaux de sévérité syslog standard
    SYSLOG_SEVERITY = {
        'emerg': 10, 'emergency': 10,
        'alert': 9,
        'crit': 10, 'critical': 10,
        'err': 8, 'error': 8,
        'warn': 6, 'warning': 6,
        'notice': 5,
        'info': 4, 'informational': 4,
        'debug': 3
    }
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.syslog_path = r"\\SRV-SYSLOG\surveillence$\syslog"
        self.last_position = 0
        self.last_check_time = None
        self.processed_lines = set()
        self.stop_requested = False
    
    def log(self, message):
        if self.log_callback:
            try:
                self.log_callback(message)
            except:
                print(message)
        else:
            print(message)
    
    def request_stop(self):
        """Demande l'arrêt de la lecture"""
        self.stop_requested = True
        self.log("🛑 Arrêt demandé pour le lecteur Syslog")
    
    def reset_stop(self):
        """Réinitialise le flag d'arrêt"""
        self.stop_requested = False
    
    def get_priority_emoji(self, priority):
        """Cercles colorés"""
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
        """Vérifie l'accès au fichier"""
        if not os.path.exists(self.syslog_path):
            raise Exception(f"Fichier Syslog introuvable: {self.syslog_path}")
        
        try:
            # Tester la lecture avec différents encodages
            encodings = ['utf-8', 'latin-1', 'cp1252']
            working_encoding = None
            
            for encoding in encodings:
                try:
                    with open(self.syslog_path, 'r', encoding=encoding, errors='replace') as f:
                        f.read(100)
                    working_encoding = encoding
                    break
                except:
                    continue
            
            if not working_encoding:
                raise Exception("Impossible de lire le fichier avec les encodages testés")
            
            size_mb = os.path.getsize(self.syslog_path) / (1024 * 1024)
            self.log(f"✓ Fichier Syslog détecté: {size_mb:.2f} MB (encodage: {working_encoding})")
            return True
        except PermissionError:
            raise Exception("Accès refusé au fichier Syslog")
    
    def parse_syslog_line(self, line):
        """Parse une ligne Syslog - TOUS FORMATS"""
        try:
            line = line.strip()
            if not line or len(line) < 20:
                return None
            
            # Recherche d'IP surveillée PARTOUT dans la ligne
            found_ip = None
            for ip in self.MONITORED_DEVICES.keys():
                if ip in line:
                    found_ip = ip
                    break
            
            if not found_ip:
                return None
            
            # Extraction timestamp (multiples formats)
            timestamp = datetime.now()
            
            # Format 1: Jan 6 10:30:45
            time_match = re.search(r'(\w+\s+\d+\s+\d+:\d+:\d+)', line)
            if time_match:
                try:
                    current_year = datetime.now().year
                    timestamp = datetime.strptime(f"{current_year} {time_match.group(1)}", 
                                                 "%Y %b %d %H:%M:%S")
                except:
                    pass
            
            # Format 2: ISO 2024-01-06T10:30:45
            iso_match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', line)
            if iso_match:
                try:
                    timestamp = datetime.fromisoformat(iso_match.group(1))
                except:
                    pass
            
            # Extraction facility (entre IP et message)
            facility = "syslog"
            facility_match = re.search(rf'{re.escape(found_ip)}\s+(\w+):', line)
            if facility_match:
                facility = facility_match.group(1)
            
            return {
                'timestamp': timestamp,
                'ip': found_ip,
                'facility': facility,
                'message': line,
                'raw_line': line
            }
            
        except Exception:
            return None
    
    def get_event_priority(self, log_entry):
        """Calcule la priorité - DÉTECTION MAXIMALE"""
        max_score = 0
        found_keywords = []
        
        # Recherche avec mots-clés simples (case insensitive)
        full_text = f"{log_entry['facility']} {log_entry['message']}".lower()
        
        # 1. Chercher les niveaux de sévérité syslog
        for severity, score in self.SYSLOG_SEVERITY.items():
            # Chercher comme mot entier ou entre crochets [ALERT]
            if re.search(rf'\b{severity}\b|\[{severity}\]', full_text, re.IGNORECASE):
                if score > max_score:
                    max_score = score
                    found_keywords.append(f"{severity}({score})")
        
        # 2. Chercher chaque mot-clé critique
        for keyword, score in self.CRITICAL_KEYWORDS.items():
            if keyword in full_text:
                if score > max_score:
                    max_score = score
                found_keywords.append(f"{keyword}({score})")
        
        # 3. Patterns spéciaux pour équipements réseau
        patterns = [
            (r'connection\s+(failed|refused|timeout)', 7),
            (r'authentication\s+fail', 8),
            (r'link\s+down', 7),
            (r'port\s+(down|disabled)', 6),
            (r'memory\s+(full|exceeded)', 8),
            (r'cpu\s+(overload|high)', 7),
            (r'packet\s+(drop|loss)', 6),
            (r'unable\s+to', 6),
            (r'cannot\s+', 6),
            (r'unavailable', 6),
        ]
        
        for pattern, score in patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                if score > max_score:
                    max_score = score
                found_keywords.append(f"pattern:{pattern}({score})")
        
        # Debug: afficher ce qui a été trouvé
        if found_keywords and max_score >= 5:
            self.log(f"      🔍 Détecté: {', '.join(found_keywords[:3])}")
        
        # Score par défaut si rien trouvé
        if max_score == 0:
            max_score = 4  # Par défaut = basse priorité
        
        return max_score
    
    def should_process_log(self, log_entry):
        """Détermine si on traite ce log"""
        # Vérifier IP surveillée
        if log_entry['ip'] not in self.MONITORED_DEVICES:
            return False, "IP non surveillée"
        
        # Calculer priorité
        priority = self.get_event_priority(log_entry)
        
        # SEUIL DE FILTRAGE TRÈS BAS: >= 4
        if priority < 4:
            return False, f"Priorité trop basse ({priority})"
        
        # Anti-doublon
        line_hash = hash(log_entry['raw_line'])
        if line_hash in self.processed_lines:
            return False, "Doublon"
        
        self.processed_lines.add(line_hash)
        return True, f"Priorité {priority}/10"
    
    def convert_to_event_format(self, log_entry):
        """Convertit en format événement"""
        device_info = self.MONITORED_DEVICES.get(log_entry['ip'], 
                                                 {'name': 'Unknown', 'icon': '❓'})
        
        priority = self.get_event_priority(log_entry)
        
        return {
            'record_number': hash(log_entry['raw_line']) % 1000000,
            'time_generated': log_entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            'source': f"{device_info['icon']} {device_info['name']} ({log_entry['ip']})",
            'event_id': priority * 1000,
            'event_type': 'WARNING' if priority < 8 else 'ERROR',
            'computer': log_entry['ip'],
            'message': f"[{log_entry['facility']}] {log_entry['message'][:500]}",
            '_priority': priority,
            '_is_syslog': True,
            '_device_type': device_info.get('type', 'unknown'),
            '_device_name': device_info['name']
        }
    
    def read_events(self, since_time=None):
        """Lit les événements Syslog - LECTURE COMPLÈTE"""
        if not os.path.exists(self.syslog_path):
            raise Exception(f"Fichier Syslog introuvable")
        
        events = []
        total_lines = 0
        parsed_lines = 0
        errors_found = 0
        warnings_found = 0
        
        # Réinitialiser le flag d'arrêt
        self.reset_stop()
        
        try:
            self.log(f"📂 Lecture du fichier Syslog...")
            
            # Essayer différents encodages
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            lines = None
            used_encoding = None
            
            for encoding in encodings:
                try:
                    with open(self.syslog_path, 'r', encoding=encoding, errors='replace') as f:
                        # Lire TOUTES les lignes
                        all_lines = f.readlines()
                        
                        # Si on a un last_position, ne garder que les nouvelles lignes
                        if self.last_position > 0:
                            lines = all_lines[self.last_position:]
                        else:
                            lines = all_lines
                        
                        # Mettre à jour la position
                        self.last_position = len(all_lines)
                        
                    used_encoding = encoding
                    break
                except Exception as e:
                    continue
            
            if lines is None:
                raise Exception("Impossible de lire le fichier")
            
            self.log(f"   📋 {len(lines)} lignes à analyser (encodage: {used_encoding})...")
            
            # TRAITEMENT AVEC SUPPORT D'ARRÊT
            for i, line in enumerate(lines):
                # Vérifier si arrêt demandé toutes les 50 lignes
                if i % 50 == 0 and self.stop_requested:
                    self.log(f"   🛑 Arrêt demandé à la ligne {i+1}/{len(lines)}")
                    break
                
                total_lines += 1
                
                if not line.strip():
                    continue
                
                log_entry = self.parse_syslog_line(line)
                
                if log_entry:
                    parsed_lines += 1
                    
                    # Afficher parsing toutes les 200 lignes
                    if parsed_lines % 200 == 0:
                        self.log(f"   ... {parsed_lines}/{total_lines} lignes analysées")
                    
                    # Filtrer par date
                    if since_time and log_entry['timestamp'] < since_time:
                        continue
                    
                    # Vérifier traitement
                    should_process, reason = self.should_process_log(log_entry)
                    
                    if should_process:
                        event = self.convert_to_event_format(log_entry)
                        events.append(event)
                        
                        device_info = self.MONITORED_DEVICES[log_entry['ip']]
                        self.log(f"   ✓ {device_info['icon']} {device_info['name']}: {reason}")
                        
                        if event['event_type'] == 'ERROR':
                            errors_found += 1
                        else:
                            warnings_found += 1
            
            # AFFICHAGE FINAL
            if not self.stop_requested:
                self.log(f"\n📊 RÉSULTAT SYSLOG:")
                self.log(f"   • Total scanné: {total_lines} lignes")
                self.log(f"   • Lignes avec IP surveillée: {parsed_lines}")
                self.log(f"   • Erreurs détectées: {errors_found}")
                self.log(f"   • Warnings détectés: {warnings_found}")
                self.log(f"   • TOTAL INCIDENTS: {len(events)}")
                
                # Afficher sources avec cercles
                if events:
                    sources = {}
                    for event in events:
                        source = event['source']
                        sources[source] = sources.get(source, 0) + 1
                    
                    self.log(f"\n📋 Sources d'incidents trouvées:")
                    for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
                        max_priority = max(e['_priority'] for e in events if e['source'] == source)
                        emoji = self.get_priority_emoji(max_priority)
                        self.log(f"   {emoji} {source}: {count} incident(s)")
                else:
                    self.log(f"\n✅ Aucun incident détecté (seuil: priorité >= 4)")
            else:
                self.log(f"\n⚠️ Lecture interrompue: {len(events)} événements avant arrêt")
            
            self.last_check_time = datetime.now()
            return events
            
        except Exception as e:
            self.log(f"❌ Erreur lecture Syslog: {str(e)}")
            raise Exception(f"Erreur lecture Syslog: {str(e)}")
    
    def read_initial_check(self, hours=24):
        """Vérification initiale X heures"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        self.log(f"🔍 Vérification Syslog des {hours} dernières heures...")
        self.log(f"   Recherche depuis: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.last_position = 0
        self.processed_lines.clear()
        
        return self.read_events(since_time=cutoff_time)
    
    def read_new_events(self):
        """Surveillance continue"""
        self.log(f"🔄 Recherche nouveaux événements Syslog...")
        return self.read_events()
    
    def get_device_stats(self):
        """Stats équipements"""
        stats = []
        for ip, info in self.MONITORED_DEVICES.items():
            stats.append(f"{info['icon']} {info['name']} ({ip})")
        return stats
    
    def reset(self):
        """Reset"""
        self.last_position = 0
        self.processed_lines.clear()
        self.stop_requested = False
        self.log("🔄 Lecteur Syslog réinitialisé")