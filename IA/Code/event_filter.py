"""
Filtre d'événements - CLASSIFICATION SYSLOG AUTOMATIQUE
✅ Stormshield, Borne WiFi, Switches → Marqués comme Syslog
✅ Détection intelligente
"""
import re
from web_searcher import WebSearcher


class EventFilter:
    """Filtre avec classification Syslog automatique"""
    
    # Seuils ultra-bas
    DEVICE_THRESHOLDS = {
        'Stormshield': 3,
        'Borne WiFi': 9,
        'Switch Principal': 3,
        'Switch Secondaire': 3,
        'Serveur AD': 5,
        'Serveur IA': 6,
        'Autres': 6,
    }
    
    # 🔥 APPAREILS SYSLOG (équipements réseau)
    SYSLOG_DEVICES = {
        'Stormshield',
        'Borne WiFi', 
        'Switch Principal',
        'Switch Secondaire'
    }
    
    # 🔥 IPs SYSLOG
    SYSLOG_IPS = {
        '192.168.10.254',  # Stormshield
        '192.168.10.11',   # Borne WiFi
        '192.168.10.15',   # Switch Principal
        '192.168.10.16'    # Switch Secondaire
    }
    
    CRITICAL_EVENT_IDS = {
        1102: 10, 4719: 10, 4794: 10,
        4765: 9, 7045: 9, 4697: 9,
        4625: 8, 1001: 8, 4724: 8, 4728: 8, 4732: 8, 4756: 8,
        41: 7, 6008: 7, 4720: 7, 4648: 7,
        4688: 6, 4722: 6, 1311: 6, 2087: 6, 2088: 6,
        1000: 5, 1002: 5,
    }
    
    CRITICAL_KEYWORDS = {
        'intrusion': 10, 'attack': 10, 'breach': 10, 'hack': 10,
        'exploit': 9, 'malware': 9, 'virus': 9, 'trojan': 9,
        'deny': 8, 'denied': 8, 'drop': 8, 'dropped': 8,
        'block': 8, 'blocked': 8, 'reject': 8, 'rejected': 8,
        'refused': 8, 'forbidden': 8,
        'unauthorized': 9, 'invalid': 7, 'suspicious': 8,
        'scan': 7, 'probe': 7, 'attempt': 6,
        'anomaly': 8, 'anomalous': 8,
        'authentication failed': 9, 'login failed': 8,
        'auth fail': 8, 'brute': 10, 'brute force': 10,
        'fail': 6, 'failed': 6, 'failure': 6, 'error': 5,
        'timeout': 5, 'corruption': 6, 'fatal': 7,
        'ddos': 10, 'dos': 9, 'flood': 9,
        'syn flood': 10, 'port scan': 9,
    }
    
    INTRUSION_PATTERNS = [
        (r'(\d+)\s+failed\s+(?:login|authentication)\s+attempts?', 9),
        (r'multiple\s+failed\s+attempts', 9),
        (r'access\s+denied\s+from\s+(\d+\.\d+\.\d+\.\d+)', 8),
        (r'connection\s+refused\s+from', 7),
        (r'invalid\s+user', 8),
        (r'root\s+login\s+attempt', 9),
        (r'admin\s+(?:login|access)\s+attempt', 9),
        (r'port\s+scan\s+detected', 9),
        (r'(?:syn|icmp|udp)\s+flood', 10),
        (r'blacklist\s+hit', 9),
        (r'malicious\s+(?:traffic|activity|content)', 9),
    ]
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.seen_record_numbers = set()
        self.web_searcher = WebSearcher(log_callback=log_callback)
    
    def log(self, message):
        if self.log_callback:
            try:
                self.log_callback(message)
            except:
                print(message)
        else:
            print(message)
    
    def classify_event_as_syslog(self, event):
        """
        🔥 CLASSIFICATION AUTOMATIQUE SYSLOG
        Marque un événement comme Syslog si c'est un équipement réseau
        """
        # Déjà marqué
        if event.get('_is_syslog') is not None:
            return event.get('_is_syslog')
        
        # Vérifier par device_name
        device_name = event.get('_device_name', '')
        if device_name in self.SYSLOG_DEVICES:
            event['_is_syslog'] = True
            return True
        
        # Vérifier par device_ip
        device_ip = event.get('_device_ip', '')
        if device_ip in self.SYSLOG_IPS:
            event['_is_syslog'] = True
            return True
        
        # Vérifier par computer
        computer = event.get('computer', '')
        if computer in self.SYSLOG_IPS:
            event['_is_syslog'] = True
            return True
        
        # Vérifier dans source
        source = event.get('source', '').lower()
        
        syslog_keywords = ['stormshield', 'firewall', 'asqd', 'wifi', 'switch', 'borne']
        
        if any(kw in source for kw in syslog_keywords):
            event['_is_syslog'] = True
            return True
        
        # Par défaut : Windows Event
        event['_is_syslog'] = False
        return False
    
    def get_device_from_event(self, event):
        """Détermine l'appareil"""
        if event.get('_device_name'):
            return event['_device_name']
        
        device_ip = event.get('_device_ip', '').strip()
        
        if device_ip:
            ip_map = {
                '192.168.10.254': 'Stormshield',
                '192.168.10.11': 'Borne WiFi',
                '192.168.10.15': 'Switch Principal',
                '192.168.10.16': 'Switch Secondaire',
                '192.168.10.10': 'Serveur AD',
                '192.168.10.110': 'Serveur IA'
            }
            
            if device_ip in ip_map:
                return ip_map[device_ip]
        
        computer = event.get('computer', '').strip()
        
        if computer:
            ip_map = {
                '192.168.10.254': 'Stormshield',
                '192.168.10.11': 'Borne WiFi',
                '192.168.10.15': 'Switch Principal',
                '192.168.10.16': 'Switch Secondaire',
                '192.168.10.10': 'Serveur AD',
                '192.168.10.110': 'Serveur IA'
            }
            
            if computer in ip_map:
                return ip_map[computer]
        
        source = event.get('source', '').lower()
        
        if 'stormshield' in source or '192.168.10.254' in source:
            return 'Stormshield'
        elif 'wifi' in source or 'borne' in source or '192.168.10.11' in source:
            return 'Borne WiFi'
        elif 'switch' in source:
            if '15' in source or 'principal' in source:
                return 'Switch Principal'
            elif '16' in source or 'secondaire' in source:
                return 'Switch Secondaire'
        elif 'ad' in source or 'active directory' in source or '192.168.10.10' in source:
            return 'Serveur AD'
        elif 'ia' in source or 'serveur-ia' in source or '192.168.10.110' in source:
            return 'Serveur IA'
        
        return 'Autres'
    
    def analyze_intrusion_patterns(self, message):
        """Analyse patterns d'intrusion"""
        message_lower = message.lower()
        
        for pattern, priority in self.INTRUSION_PATTERNS:
            match = re.search(pattern, message_lower)
            if match:
                reason = f"Pattern intrusion: {pattern[:50]}"
                
                if r'(\d+)' in pattern:
                    try:
                        attempts = int(match.group(1))
                        if attempts >= 10:
                            priority = min(10, priority + 2)
                            reason = f"Intrusion: {attempts} tentatives"
                        elif attempts >= 5:
                            priority = min(10, priority + 1)
                            reason = f"Intrusion: {attempts} tentatives"
                    except:
                        pass
                
                return True, priority, reason
        
        return False, 0, ""
    
    def get_event_priority(self, event):
        """Calcule la priorité"""
        score = 0
        event_id = event.get('event_id', 0)
        
        if event_id in self.CRITICAL_EVENT_IDS:
            score = self.CRITICAL_EVENT_IDS[event_id]
        
        message = event.get('message', '')
        message_lower = message.lower()
        
        intrusion_detected, intrusion_priority, intrusion_reason = \
            self.analyze_intrusion_patterns(message)
        
        if intrusion_detected:
            score = max(score, intrusion_priority)
            event['_intrusion_detected'] = True
            event['_intrusion_reason'] = intrusion_reason
        
        for keyword, keyword_score in self.CRITICAL_KEYWORDS.items():
            if keyword in message_lower:
                score = max(score, keyword_score)
                
                device = self.get_device_from_event(event)
                if device == 'Stormshield':
                    score = min(10, score + 1)
        
        if event.get('_is_syslog', False) and event.get('_priority'):
            score = max(score, event['_priority'])
        
        if score == 0:
            event_type = event.get('event_type', '').upper()
            if event_type == 'ERROR':
                score = 6
            elif event_type == 'WARNING':
                score = 5
            else:
                score = 3
        
        return score
    
    def get_priority_label(self, priority):
        """Label de priorité"""
        if priority >= 9:
            return "🔴 CRITIQUE", "🔴"
        elif priority >= 7:
            return "🟠 HAUTE", "🟠"
        elif priority >= 5:
            return "🟡 MOYENNE", "🟡"
        elif priority >= 3:
            return "🟢 BASSE", "🟢"
        else:
            return "⚪ INFO", "⚪"
    
    def filter_events(self, events, enable_online_check=True):
        """Filtrage des événements"""
        if not events:
            return []
        
        # 🔥 CLASSIFICATION SYSLOG AUTOMATIQUE
        for event in events:
            self.classify_event_as_syslog(event)
        
        # Comptage séparé
        syslog_count = sum(1 for e in events if e.get('_is_syslog', False))
        windows_count = sum(1 for e in events if not e.get('_is_syslog', False))
        
        self.log(f"\n🔍 FILTRAGE PAR APPAREIL:")
        self.log(f"   • Événements reçus: {len(events)}")
        self.log(f"   • Événements Syslog: {syslog_count}")
        self.log(f"   • Événements Windows: {windows_count}")
        
        result = []
        duplicates = 0
        filtered_by_threshold = 0
        intrusions_detected = 0
        
        device_stats = {}
        
        for event in events:
            priority = self.get_event_priority(event)
            event['_priority'] = priority
            
            if event.get('_intrusion_detected'):
                intrusions_detected += 1
            
            record_num = event.get('record_number', 0)
            
            if record_num in self.seen_record_numbers:
                duplicates += 1
                continue
            
            device = self.get_device_from_event(event)
            min_threshold = self.DEVICE_THRESHOLDS.get(device, 6)
            
            if priority < min_threshold:
                filtered_by_threshold += 1
                
                if device not in device_stats:
                    device_stats[device] = {
                        'total': 0, 'filtered': 0, 'kept': 0,
                        'syslog': 0, 'windows': 0
                    }
                device_stats[device]['total'] += 1
                device_stats[device]['filtered'] += 1
                
                if event.get('_is_syslog', False):
                    device_stats[device]['syslog'] += 1
                else:
                    device_stats[device]['windows'] += 1
                
                continue
            
            self.seen_record_numbers.add(record_num)
            result.append(event)
            
            if device not in device_stats:
                device_stats[device] = {
                    'total': 0, 'filtered': 0, 'kept': 0,
                    'syslog': 0, 'windows': 0
                }
            device_stats[device]['total'] += 1
            device_stats[device]['kept'] += 1
            
            if event.get('_is_syslog', False):
                device_stats[device]['syslog'] += 1
            else:
                device_stats[device]['windows'] += 1
        
        self.log(f"\n📊 RÉSULTAT FILTRAGE:")
        self.log(f"   • Doublons ignorés: {duplicates}")
        self.log(f"   • Filtrés par seuil: {filtered_by_threshold}")
        
        if intrusions_detected > 0:
            self.log(f"   🚨 INTRUSIONS DÉTECTÉES: {intrusions_detected}")
        
        self.log(f"   ✅ Événements gardés: {len(result)}")
        
        final_syslog = sum(1 for e in result if e.get('_is_syslog', False))
        final_windows = sum(1 for e in result if not e.get('_is_syslog', False))
        
        self.log(f"\n📈 RÉPARTITION FINALE:")
        self.log(f"   • Syslog gardés: {final_syslog}")
        self.log(f"   • Windows gardés: {final_windows}")
        
        if device_stats:
            self.log(f"\n📡 DÉTAIL PAR APPAREIL:")
            for device, stats in sorted(device_stats.items()):
                threshold = self.DEVICE_THRESHOLDS.get(device, 6)
                
                device_icons = {
                    'Stormshield': '🔥',
                    'Borne WiFi': '📡',
                    'Switch Principal': '🔌',
                    'Switch Secondaire': '🔌',
                    'Serveur AD': '🖥️',
                    'Serveur IA': '🤖',
                    'Autres': '❓'
                }
                
                icon = device_icons.get(device, '🔟')
                
                # 🔥 INDICATION SI SYSLOG
                if device in self.SYSLOG_DEVICES:
                    device_type = " [SYSLOG]"
                else:
                    device_type = " [WINDOWS]"
                
                if threshold == 9:
                    mode = "CRITIQUE SEULEMENT"
                elif threshold <= 3:
                    mode = "Ultra-sensible"
                elif threshold == 5:
                    mode = "Sensible"
                else:
                    mode = "Équilibré"
                
                self.log(f"   {icon} {device}{device_type} (seuil {threshold}/10 - {mode}):")
                self.log(f"      - Reçus: {stats['total']} (Syslog: {stats['syslog']}, Win: {stats['windows']})")
                self.log(f"      - Filtrés: {stats['filtered']}")
                self.log(f"      - ✅ Gardés: {stats['kept']}")
        
        priority_stats = {}
        for event in result:
            priority = event.get('_priority', 0)
            label, _ = self.get_priority_label(priority)
            priority_stats[label] = priority_stats.get(label, 0) + 1
        
        if priority_stats:
            self.log(f"\n🎯 RÉPARTITION PAR PRIORITÉ:")
            for label in sorted(priority_stats.keys(), reverse=True):
                self.log(f"   {label}: {priority_stats[label]} événement(s)")
        
        self.log(f"\n✅ {len(result)} événements passent au ticket_manager\n")
        
        return result
    
    def reset(self):
        """Réinitialise le filtre"""
        self.seen_record_numbers.clear()
        self.log("🔄 Filtre réinitialisé")