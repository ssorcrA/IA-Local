"""
Filtre d'événements - BORNE WIFI TRÈS SÉLECTIVE (seuil 9/10)
Fichier : event_filter.py - VERSION FINALE
✅ CORRECTIF: Aligné avec syslog_reader.py
- Borne WiFi : seuil 9 (critiques uniquement)
- Stormshield : seuil 5 (surveillance normale)
- Switches : seuil 6 (surveillance normale)
"""
import re
from web_searcher import WebSearcher


class EventFilter:
    """Filtre avec Borne WiFi très sélective"""
    
    # ✅ SEUILS ALIGNÉS - BORNE WIFI CRITIQUE UNIQUEMENT
    DEVICE_THRESHOLDS = {
        'Stormshield': 5,          # ✅ Surveillance normale - warnings + errors
        'Borne WiFi': 9,           # 🔥 TRÈS SÉLECTIF - Critiques uniquement
        'Switch Principal': 6,     # ✅ Surveillance normale - erreurs moyennes+
        'Switch Secondaire': 6,    # ✅ Surveillance normale
        'Serveur AD': 6,           # ✅ Surveillance normale
        'Serveur IA': 7,           # Critiques uniquement
        'Autres': 7,
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
        # Intrusions réseau
        'intrusion': 10, 'attack': 10, 'breach': 10, 'hack': 10,
        'exploit': 9, 'malware': 9, 'virus': 9, 'trojan': 9,
        
        # Blocages firewall (CRITIQUES pour Stormshield)
        'deny': 8, 'denied': 8, 'drop': 8, 'dropped': 8,
        'block': 8, 'blocked': 8, 'reject': 8, 'rejected': 8,
        'refused': 8, 'forbidden': 8,
        
        # Tentatives suspectes
        'unauthorized': 9, 'invalid': 7, 'suspicious': 8,
        'scan': 7, 'probe': 7, 'attempt': 6,
        'anomaly': 8, 'anomalous': 8,
        
        # Authentification
        'authentication failed': 9, 'login failed': 8,
        'auth fail': 8, 'brute': 10, 'brute force': 10,
        
        # Erreurs système
        'fail': 6, 'failed': 6, 'failure': 6, 'error': 5,
        'timeout': 5, 'corruption': 6, 'fatal': 7,
        
        # Trafic malveillant
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
    
    def get_device_from_event(self, event):
        """Détermine l'appareil"""
        device_ip = event.get('_device_ip', '')
        
        if device_ip == '192.168.10.254':
            return 'Stormshield'
        elif device_ip == '192.168.10.11':
            return 'Borne WiFi'
        elif device_ip == '192.168.10.15':
            return 'Switch Principal'
        elif device_ip == '192.168.10.16':
            return 'Switch Secondaire'
        elif device_ip == '192.168.10.10':
            return 'Serveur AD'
        elif device_ip == '192.168.10.110':
            return 'Serveur IA'
        
        computer = event.get('computer', '').strip()
        
        if computer == '192.168.10.254':
            return 'Stormshield'
        elif computer == '192.168.10.11':
            return 'Borne WiFi'
        elif computer == '192.168.10.15':
            return 'Switch Principal'
        elif computer == '192.168.10.16':
            return 'Switch Secondaire'
        elif computer == '192.168.10.10':
            return 'Serveur AD'
        elif computer == '192.168.10.110':
            return 'Serveur IA'
        
        source = event.get('source', '').lower()
        
        if 'stormshield' in source or '192.168.10.254' in source:
            return 'Stormshield'
        elif 'wifi' in source or 'borne' in source:
            return 'Borne WiFi'
        elif 'switch' in source and ('15' in source or 'principal' in source):
            return 'Switch Principal'
        elif 'switch' in source and ('16' in source or 'secondaire' in source):
            return 'Switch Secondaire'
        elif 'ad' in source or 'active directory' in source:
            return 'Serveur AD'
        elif 'ia' in source or 'serveur-ia' in source:
            return 'Serveur IA'
        
        return 'Autres'
    
    def analyze_intrusion_patterns(self, message):
        """Analyse approfondie des patterns d'intrusion"""
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
                
                if event.get('_device_ip') == '192.168.10.254':
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
        """Retourne le label et emoji"""
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
        """Filtrage optimisé"""
        if not events:
            return []
        
        self.log(f"\n🔍 FILTRAGE PAR APPAREIL:")
        self.log(f"   • Événements reçus: {len(events)}")
        
        syslog_events = [e for e in events if e.get('_is_syslog', False)]
        windows_events = [e for e in events if not e.get('_is_syslog', False)]
        
        self.log(f"   • Événements Syslog: {len(syslog_events)}")
        self.log(f"   • Événements Windows: {len(windows_events)}")
        
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
            
            # ✅ APPLIQUER SEUIL ALIGNÉ
            min_threshold = self.DEVICE_THRESHOLDS.get(device, 7)
            
            if priority < min_threshold:
                filtered_by_threshold += 1
                
                if device not in device_stats:
                    device_stats[device] = {'total': 0, 'filtered': 0, 'kept': 0}
                device_stats[device]['total'] += 1
                device_stats[device]['filtered'] += 1
                
                continue
            
            self.seen_record_numbers.add(record_num)
            result.append(event)
            
            if device not in device_stats:
                device_stats[device] = {'total': 0, 'filtered': 0, 'kept': 0}
            device_stats[device]['total'] += 1
            device_stats[device]['kept'] += 1
        
        # Stats globales
        self.log(f"\n📊 RÉSULTAT FILTRAGE:")
        self.log(f"   • Doublons ignorés: {duplicates}")
        self.log(f"   • Filtrés par seuil: {filtered_by_threshold}")
        
        if intrusions_detected > 0:
            self.log(f"   🚨 INTRUSIONS DÉTECTÉES: {intrusions_detected}")
        
        self.log(f"   ✅ Événements gardés: {len(result)}")
        
        # Stats par appareil
        if device_stats:
            self.log(f"\n📡 DÉTAIL PAR APPAREIL:")
            for device, stats in sorted(device_stats.items()):
                threshold = self.DEVICE_THRESHOLDS.get(device, 7)
                
                # 🔥 Emoji spécial pour Borne WiFi
                if device == "Borne WiFi":
                    icon = "🔥" if threshold == 9 else "📡"
                    status = "TRÈS SÉLECTIF" if threshold == 9 else "Normal"
                    self.log(f"   {icon} {device} (seuil {threshold}/10 - {status}):")
                elif device == "Stormshield":
                    icon = "✅"
                    self.log(f"   {icon} {device} (seuil {threshold}/10 - Surveillance normale):")
                else:
                    icon = "✅"
                    self.log(f"   {icon} {device} (seuil {threshold}/10):")
                
                self.log(f"      - Reçus: {stats['total']}")
                self.log(f"      - Filtrés: {stats['filtered']}")
                self.log(f"      - ✅ Gardés: {stats['kept']}")
        
        # Stats par priorité
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