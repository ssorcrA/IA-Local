"""
Lecteur de logs Syslog - DÉTECTION GARANTIE ULTRA-SENSIBLE
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
    
    # MOTS-CLÉS CRITIQUES - ULTRA-SENSIBLE (mots simples)
    CRITICAL_KEYWORDS = {
        # Niveau 10 - CRITIQUE
        'attack': 10, 'intrusion': 10, 'breach': 10, 'hack': 10, 
        'exploit': 10, 'malware': 10, 'unauthorized': 10, 'denied': 10,
        'critical': 10, 'emergency': 10, 'panic': 10,
        
        # Niveau 9 - TRÈS HAUTE
        'blocked': 9, 'block': 9, 'deny': 9, 'drop': 9, 
        'dropped': 9, 'reject': 9, 'rejected': 9,
        
        # Niveau 8 - HAUTE
        'fail': 8, 'failed': 8, 'failure': 8, 'error': 8, 'err': 8,
        
        # Niveau 7 - MOYENNE-HAUTE  
        'alert': 7, 'timeout': 7, 'unreachable': 7, 'down': 7,
        
        # Niveau 6 - MOYENNE
        'warning': 6, 'warn': 6,
        
        # Niveau 5 - BASSE
        'notice': 5,
    }
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.syslog_path = r"\\SRV-SYSLOG\surveillence$\syslog"
        self.last_position = 0
        self.last_check_time = None
        self.processed_lines = set()
    
    def log(self, message):
        if self.log_callback:
            try:
                self.log_callback(message)
            except:
                print(message)
        else:
            print(message)
    
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
            with open(self.syslog_path, 'r', encoding='utf-8', errors='ignore') as f:
                f.read(100)
            
            size_mb = os.path.getsize(self.syslog_path) / (1024 * 1024)
            self.log(f"✓ Fichier Syslog détecté: {size_mb:.2f} MB")
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
        """Calcule la priorité - DÉTECTION SIMPLE ET EFFICACE"""
        max_score = 0
        
        # Recherche avec mots-clés simples (case insensitive)
        full_text = f"{log_entry['facility']} {log_entry['message']}".lower()
        
        # Chercher chaque mot-clé
        for keyword, score in self.CRITICAL_KEYWORDS.items():
            if keyword in full_text:
                if score > max_score:
                    max_score = score
                    self.log(f"      🔍 Mot-clé trouvé: '{keyword}' (score {score})")
        
        # Score par défaut si rien trouvé
        if max_score == 0:
            # Vérifier si c'est vraiment vide ou juste info
            if any(word in full_text for word in ['info', 'debug', 'notice']):
                max_score = 4
            else:
                max_score = 5  # Par défaut = moyenne
        
        return max_score
    
    def should_process_log(self, log_entry):
        """Détermine si on traite ce log"""
        # Vérifier IP surveillée
        if log_entry['ip'] not in self.MONITORED_DEVICES:
            return False, "IP non surveillée"
        
        # Calculer priorité
        priority = self.get_event_priority(log_entry)
        
        # SEUIL DE FILTRAGE ABAISSÉ: >= 4 (au lieu de 5)
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
        
        try:
            self.log(f"📂 Lecture du fichier Syslog...")
            
            with open(self.syslog_path, 'r', encoding='utf-8', errors='ignore') as f:
                if self.last_position > 0:
                    f.seek(self.last_position)
                
                lines = f.readlines()
                self.last_position = f.tell()
            
            self.log(f"   📋 {len(lines)} lignes à analyser...")
            
            # TRAITEMENT AVEC DEBUG
            for i, line in enumerate(lines):
                total_lines += 1
                
                if not line.strip():
                    continue
                
                log_entry = self.parse_syslog_line(line)
                
                if log_entry:
                    parsed_lines += 1
                    
                    # Afficher le parsing toutes les 100 lignes
                    if parsed_lines % 100 == 0:
                        self.log(f"   ... {parsed_lines} lignes parsées")
                    
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
            
            # AFFICHAGE PROPRE FINAL
            self.log(f"\n📊 RÉSULTAT:")
            self.log(f"   • Total scanné: {total_lines} lignes")
            self.log(f"   • Lignes parsées: {parsed_lines}")
            self.log(f"   • Erreurs trouvées: {errors_found}")
            self.log(f"   • Warnings trouvés: {warnings_found}")
            self.log(f"   • TOTAL INCIDENTS: {len(events)}")
            
            # Afficher sources avec cercles
            if events:
                sources = {}
                for event in events:
                    source = event['source']
                    sources[source] = sources.get(source, 0) + 1
                
                self.log(f"\n📋 Sources d'erreurs trouvées:")
                for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
                    max_priority = max(e['_priority'] for e in events if e['source'] == source)
                    emoji = self.get_priority_emoji(max_priority)
                    self.log(f"   {emoji} {source}: {count} incident(s)")
            else:
                self.log(f"\n⚠️ AUCUN ÉVÉNEMENT DÉTECTÉ !")
                self.log(f"   • Lignes totales: {total_lines}")
                self.log(f"   • Lignes avec IP surveillée: {parsed_lines}")
                if parsed_lines > 0:
                    self.log(f"   • Toutes les lignes ont été filtrées (priorité < 4)")
            
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
        self.log("🔄 Lecteur Syslog réinitialisé")