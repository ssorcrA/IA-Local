"""
Filtre intelligent d'événements avec PRIORISATION RENFORCÉE
Fichier : event_filter.py - VERSION OPTIMISÉE
"""
import re
from web_searcher import WebSearcher


class EventFilter:
    """Filtre les événements avec intelligence et priorisation renforcée"""
    
    # Event IDs CRITIQUES avec scores de 1 à 10
    CRITICAL_EVENT_IDS = {
        # NIVEAU 10 - CRITIQUE ABSOLU (Sécurité maximale)
        1102: 10,  # Journal d'audit effacé
        4719: 10,  # Modification politique d'audit
        4794: 10,  # Mode restauration services d'annuaire
        
        # NIVEAU 9 - TRÈS HAUTE PRIORITÉ (Intrusions probables)
        4765: 9,   # Historique SID ajouté - Suspect
        7045: 9,   # Nouveau service installé - Suspect
        4697: 9,   # Service installé dans le système
        
        # NIVEAU 8 - HAUTE PRIORITÉ (Sécurité importante)
        4625: 8,   # Échec d'authentification
        1001: 8,   # Crash système (BSOD)
        4724: 8,   # Tentative de réinitialisation mot de passe
        4728: 8,   # Membre ajouté à un groupe de sécurité global
        4732: 8,   # Membre ajouté à un groupe local
        4756: 8,   # Membre ajouté à un groupe universel
        
        # NIVEAU 7 - PRIORITÉ MOYENNE-HAUTE (Surveillance importante)
        41: 7,     # Redémarrage sans arrêt propre
        6008: 7,   # Arrêt inattendu
        4720: 7,   # Compte utilisateur créé
        4648: 7,   # Tentative de connexion explicite
        
        # NIVEAU 6 - PRIORITÉ MOYENNE (À surveiller)
        4688: 6,   # Nouveau processus créé
        4722: 6,   # Compte utilisateur activé
        1311: 6,   # Erreur réplication KCC
        2087: 6,   # Échec résolution DNS pour DC
        2088: 6,   # Échec recherche DC
        
        # NIVEAU 5 - PRIORITÉ BASSE-MOYENNE
        1000: 5,   # Crash d'application
        1002: 5,   # Application bloquée
        
        # NIVEAU 4 - PRIORITÉ BASSE
        # Ajoutez ici les event IDs moins critiques
        
        # NIVEAU 3 - TRÈS BASSE PRIORITÉ
        # Ajoutez ici les event IDs informatifs
        
        # NIVEAU 2 - INFORMATIONNEL
        # Event IDs pour information uniquement
        
        # NIVEAU 1 - MINIMAL
        # Event IDs de faible importance
    }
    
    # Mots-clés critiques avec scores précis de 1 à 10
    CRITICAL_KEYWORDS = {
        # NIVEAU 10 - MOTS-CLÉS CRITIQUES ABSOLUS
        'ransomware': 10,
        'intrusion': 10,
        'breach': 10,
        'compromis': 10,
        'hack': 10,
        'rootkit': 10,
        
        # NIVEAU 9 - TRÈS HAUTE PRIORITÉ
        'exploit': 9,
        'privilege escalation': 9,
        'élévation de privilèges': 9,
        'backdoor': 9,
        
        # NIVEAU 8 - HAUTE PRIORITÉ
        'attack': 8,
        'attaque': 8,
        'unauthorized': 8,
        'non autorisé': 8,
        'malware': 8,
        
        # NIVEAU 7 - PRIORITÉ MOYENNE-HAUTE
        'trojan': 7,
        'worm': 7,
        'botnet': 7,
        
        # NIVEAU 6 - PRIORITÉ MOYENNE
        'virus': 6,
        'vulnerability': 6,
        'vulnérabilité': 6,
        'brute force': 6,
        'injection': 6,
        'critical': 6,
        'critique': 6,
        
        # NIVEAU 5 - PRIORITÉ BASSE-MOYENNE
        'suspicious': 5,
        'suspect': 5,
        
        # NIVEAU 4 - PRIORITÉ BASSE
        'corruption': 4,
        'corruption de données': 4,
        'fatal': 4,
        'emergency': 4,
        'urgence': 4,
        
        # NIVEAU 3 - TRÈS BASSE PRIORITÉ
        'warning': 3,
        'avertissement': 3,
        
        # NIVEAU 2 - INFORMATIONNEL
        'notice': 2,
        
        # NIVEAU 1 - MINIMAL
        'info': 1,
    }
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.seen_events = {}
        self.web_searcher = WebSearcher(log_callback=log_callback)
    
    def log(self, message):
        """Log un message"""
        if self.log_callback:
            try:
                self.log_callback(message)
            except:
                print(message)
        else:
            print(message)
    
    def get_event_signature(self, event):
        """Génère une signature unique basée sur source + event_id + computer"""
        return f"{event['source']}_{event['event_id']}_{event['computer']}"
    
    def get_base_signature(self, event):
        """Génère une signature de base (sans computer) pour regroupement"""
        return f"{event['source']}_{event['event_id']}"
    
    def get_event_priority(self, event):
        """
        Calcule le score de priorité d'un événement (1-10)
        Plus le score est élevé, plus c'est prioritaire
        """
        score = 0
        event_id = event['event_id']
        
        # Score basé sur l'Event ID
        if event_id in self.CRITICAL_EVENT_IDS:
            score = self.CRITICAL_EVENT_IDS[event_id]
        
        # Score basé sur les mots-clés du message (prendre le max)
        message_lower = event['message'].lower()
        for keyword, keyword_score in self.CRITICAL_KEYWORDS.items():
            if keyword in message_lower:
                score = max(score, keyword_score)
        
        # Score par défaut si aucun match
        if score == 0:
            score = 3  # Priorité basse par défaut
        
        return score
    
    def get_priority_label(self, priority):
        """Retourne le label et l'icône pour un niveau de priorité"""
        if priority == 10:
            return "🔴 CRITIQUE 10/10", "🔴"
        elif priority == 9:
            return "🔴 CRITIQUE 9/10", "🔴"
        elif priority == 8:
            return "🟠 HAUTE 8/10", "🟠"
        elif priority == 7:
            return "🟠 HAUTE 7/10", "🟠"
        elif priority == 6:
            return "🟡 MOYENNE 6/10", "🟡"
        elif priority == 5:
            return "🟡 MOYENNE 5/10", "🟡"
        elif priority == 4:
            return "🟢 BASSE 4/10", "🟢"
        elif priority == 3:
            return "🟢 BASSE 3/10", "🟢"
        elif priority == 2:
            return "🔵 INFO 2/10", "🔵"
        else:
            return "⚪ MINIMAL 1/10", "⚪"
    
    def is_same_day(self, event):
        """Vérifie si l'événement est du même jour que le dernier vu"""
        from datetime import datetime
        
        signature = self.get_event_signature(event)
        
        if signature not in self.seen_events:
            return False
        
        try:
            current_date = event['time_generated'].split()[0]
            last_event = self.seen_events[signature]
            last_date = last_event['time_generated'].split()[0]
            return current_date == last_date
        except:
            return False
    
    def should_analyze_event(self, event, force_check=False):
        """
        Détermine si un événement doit être analysé
        Retourne: (should_analyze: bool, reason: str, priority: int)
        """
        signature = self.get_event_signature(event)
        base_signature = self.get_base_signature(event)
        event_id = event['event_id']
        
        # Calculer la priorité
        priority = self.get_event_priority(event)
        priority_label, _ = self.get_priority_label(priority)
        
        # RÈGLE 1: Événement déjà vu le même jour sur le même PC = SKIP
        if signature in self.seen_events and self.is_same_day(event):
            return False, f"Doublon détecté (même PC/jour)", priority
        
        # RÈGLE 2: Premier événement de ce type = ANALYSER
        if signature not in self.seen_events:
            self.seen_events[signature] = event
            return True, f"{priority_label} - Premier événement", priority
        
        # RÈGLE 3: Jour différent = ANALYSER
        if not self.is_same_day(event):
            self.seen_events[signature] = event
            return True, f"{priority_label} - Nouvelle occurrence", priority
        
        # RÈGLE 4: Vérification en ligne si priorité haute et force_check
        if force_check and priority >= 7:
            if self.check_severity_online(event):
                return True, f"{priority_label} - Confirmé critique en ligne", 10
        
        # Par défaut: skip
        return False, "Événement déjà traité", priority
    
    def check_severity_online(self, event):
        """Vérifie en ligne si l'erreur est critique"""
        try:
            query = f"Event ID {event['event_id']} {event['source']} severity critical security risk"
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num=3"
            
            response = self.web_searcher.session.get(search_url, timeout=5)
            
            if response.status_code == 200:
                content_lower = response.text.lower()
                
                severity_indicators = {
                    'critical': 3,
                    'high severity': 3,
                    'security risk': 2,
                    'vulnerability': 2,
                    'exploit': 2,
                    'intrusion': 3,
                    'attack': 2,
                    'breach': 3,
                    'ransomware': 3,
                    'malware': 2,
                }
                
                score = sum(points for indicator, points in severity_indicators.items() 
                          if indicator in content_lower)
                
                return score >= 4
        except:
            pass
        return False
    
    def group_similar_events(self, events):
        """
        Regroupe les événements similaires (même source + event_id)
        pour ne créer qu'un seul ticket par groupe
        """
        grouped = {}
        
        for event in events:
            base_sig = self.get_base_signature(event)
            
            if base_sig not in grouped:
                grouped[base_sig] = {
                    'representative': event,  # Événement représentatif
                    'count': 1,
                    'computers': [event['computer']],
                    'max_priority': event.get('_priority', 0)
                }
            else:
                grouped[base_sig]['count'] += 1
                if event['computer'] not in grouped[base_sig]['computers']:
                    grouped[base_sig]['computers'].append(event['computer'])
                # Garder la priorité maximale
                grouped[base_sig]['max_priority'] = max(
                    grouped[base_sig]['max_priority'],
                    event.get('_priority', 0)
                )
        
        # Créer une liste d'événements représentatifs avec métadonnées
        result = []
        for base_sig, data in grouped.items():
            event = data['representative']
            event['_grouped_count'] = data['count']
            event['_affected_computers'] = data['computers']
            event['_priority'] = data['max_priority']
            result.append(event)
        
        return result
    
    def filter_events(self, events, enable_online_check=True):
        """
        Filtre et groupe les événements avec PRIORISATION
        Retourne: Liste d'événements GROUPÉS et TRIÉS par priorité
        """
        filtered = []
        skipped = 0
        
        self.log(f"\n🔍 FILTRAGE INTELLIGENT: {len(events)} événements bruts")
        
        # Phase 1: Filtrer les doublons
        for event in events:
            should_analyze, reason, priority = self.should_analyze_event(
                event, 
                force_check=enable_online_check
            )
            
            if should_analyze:
                event['_priority'] = priority
                filtered.append(event)
            else:
                skipped += 1
        
        # Phase 2: Grouper les événements similaires
        if filtered:
            self.log(f"   • Après filtrage doublons: {len(filtered)} événements")
            grouped = self.group_similar_events(filtered)
            self.log(f"   • Après regroupement: {len(grouped)} tickets uniques")
            
            # Phase 3: Trier par priorité (critiques en premier)
            grouped.sort(key=lambda x: x.get('_priority', 0), reverse=True)
            
            # Statistiques par priorité
            priority_stats = {}
            for event in grouped:
                priority = event.get('_priority', 0)
                priority_label, icon = self.get_priority_label(priority)
                priority_stats[priority_label] = priority_stats.get(priority_label, 0) + 1
            
            self.log(f"\n📊 RÉPARTITION PAR PRIORITÉ:")
            for label in sorted(priority_stats.keys(), reverse=True):
                self.log(f"   {label}: {priority_stats[label]} incident(s)")
            
            self.log(f"\n✅ RÉSULTAT: {len(grouped)} tickets à créer (réduction de {len(events) - len(grouped)} doublons)")
            
            return grouped
        
        self.log(f"\n✅ Aucun événement à traiter après filtrage")
        return []
    
    def reset(self):
        """Réinitialise le filtre"""
        self.seen_events.clear()
        self.log("🔄 Filtre réinitialisé")