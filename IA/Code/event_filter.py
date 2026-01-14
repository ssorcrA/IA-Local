"""
Filtre d'événements - VERSION CORRIGÉE
Fichier : event_filter.py
CORRECTIFS:
- Évite uniquement les VRAIS doublons (même record_number)
- Calcule la priorité
- Laisse ticket_manager gérer le regroupement
- Ne filtre PLUS excessivement
"""
import re
from web_searcher import WebSearcher


class EventFilter:
    """Filtre minimal - évite seulement les doublons stricts"""
    
    CRITICAL_EVENT_IDS = {
        1102: 10, 4719: 10, 4794: 10,
        4765: 9, 7045: 9, 4697: 9,
        4625: 8, 1001: 8, 4724: 8, 4728: 8, 4732: 8, 4756: 8,
        41: 7, 6008: 7, 4720: 7, 4648: 7,
        4688: 6, 4722: 6, 1311: 6, 2087: 6, 2088: 6,
        1000: 5, 1002: 5,
    }
    
    CRITICAL_KEYWORDS = {
        'ransomware': 10, 'intrusion': 10, 'breach': 10, 'compromis': 10,
        'hack': 10, 'rootkit': 10, 'exploit': 9, 'privilege escalation': 9,
        'backdoor': 9, 'attack': 8, 'unauthorized': 8, 'malware': 8,
        'trojan': 7, 'worm': 7, 'botnet': 7, 'virus': 6, 'vulnerability': 6,
        'brute force': 6, 'injection': 6, 'critical': 6, 'suspicious': 5,
        'corruption': 4, 'fatal': 4, 'emergency': 4, 'warning': 3,
    }
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        # 🔥 ON GARDE SEULEMENT LES RECORD_NUMBERS POUR ÉVITER LES VRAIS DOUBLONS
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
    
    def get_event_priority(self, event):
        """Calcule la priorité d'un événement"""
        score = 0
        event_id = event.get('event_id', 0)
        
        # Priorité basée sur Event ID
        if event_id in self.CRITICAL_EVENT_IDS:
            score = self.CRITICAL_EVENT_IDS[event_id]
        
        # Priorité basée sur mots-clés
        message_lower = event.get('message', '').lower()
        for keyword, keyword_score in self.CRITICAL_KEYWORDS.items():
            if keyword in message_lower:
                score = max(score, keyword_score)
        
        # Priorité par défaut
        if score == 0:
            score = 3
        
        return score
    
    def get_priority_label(self, priority):
        """Retourne le label et emoji de priorité"""
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
        """
        🔥 FILTRAGE MINIMAL - Évite SEULEMENT les doublons stricts
        Laisse ticket_manager gérer le regroupement intelligent
        """
        if not events:
            return []
        
        self.log(f"\n🔍 FILTRAGE MINIMAL:")
        self.log(f"   • Événements reçus: {len(events)}")
        
        # Séparer Syslog et Windows pour stats
        syslog_events = []
        windows_events = []
        
        for event in events:
            if event.get('_is_syslog', False):
                syslog_events.append(event)
            else:
                windows_events.append(event)
        
        self.log(f"   • Événements Syslog: {len(syslog_events)}")
        self.log(f"   • Événements Windows: {len(windows_events)}")
        
        # 🔥 FILTRAGE: Éviter UNIQUEMENT les doublons stricts (même record_number)
        result = []
        duplicates = 0
        
        for event in events:
            # Calculer priorité
            priority = self.get_event_priority(event)
            event['_priority'] = priority
            
            # Vérifier doublon strict
            record_num = event.get('record_number', 0)
            
            if record_num in self.seen_record_numbers:
                duplicates += 1
                continue
            
            # Ajouter à la liste
            self.seen_record_numbers.add(record_num)
            result.append(event)
        
        # Statistiques
        self.log(f"\n📊 RÉSULTAT FILTRAGE:")
        self.log(f"   • Doublons stricts ignorés: {duplicates}")
        self.log(f"   • Événements uniques: {len(result)}")
        
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
        
        self.log(f"\n✅ {len(result)} événements passent au ticket_manager")
        self.log("   (Le regroupement se fera dans ticket_manager)\n")
        
        return result
    
    def reset(self):
        """Réinitialise le filtre"""
        self.seen_record_numbers.clear()
        self.log("🔄 Filtre réinitialisé")