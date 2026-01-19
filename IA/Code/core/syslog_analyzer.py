"""
Analyseur intelligent de logs Syslog avec filtrage avancé
Fichier : syslog_analyzer.py
Objectif : Ne créer des tickets QUE pour les événements vraiment importants
"""
import re
from datetime import datetime, timedelta


class SyslogAnalyzer:
    """
    Analyse intelligente des logs Syslog
    Détermine quels événements méritent vraiment un ticket
    """
    
    # Patterns CRITIQUES qui nécessitent TOUJOURS un ticket (priorité 9-10)
    CRITICAL_PATTERNS = {
        # Sécurité - Attaques
        r'attack\s+detected': 10,
        r'intrusion\s+attempt': 10,
        r'unauthorized\s+access': 10,
        r'(hack|breach|exploit)\s+attempt': 10,
        r'malware\s+detected': 10,
        r'virus\s+found': 10,
        
        # Sécurité - Authentification
        r'authentication\s+failed.*\((\d+)\s+attempts?\)': 9,  # Avec compteur
        r'brute\s*force\s+attack': 10,
        r'password\s+attack': 9,
        r'account\s+locked': 8,
        
        # Réseau - Connexions suspectes
        r'connection\s+from\s+blocked\s+(ip|host)': 9,
        r'(blacklist|blocklist)\s+hit': 9,
        r'suspicious\s+(connection|traffic)': 8,
        
        # Firewall - Attaques réseau
        r'(ddos|dos)\s+attack': 10,
        r'port\s+scan\s+detected': 8,
        r'flood\s+detected': 9,
        r'syn\s+flood': 9,
        
        # Système critique
        r'system\s+(failure|crash)': 10,
        r'kernel\s+panic': 10,
        r'out\s+of\s+memory': 9,
        r'disk\s+(full|failure)': 9,
        r'raid\s+(failure|degraded)': 10,
        
        # Services critiques
        r'(dhcp|dns|ldap|active\s+directory)\s+(fail|down|unavailable)': 9,
        r'backup\s+failed': 8,
        r'database\s+(corruption|failure)': 10,
    }
    
    # Patterns HAUTE priorité (7-8) - Tickets si répétés ou combinés
    HIGH_PRIORITY_PATTERNS = {
        r'connection\s+(refused|timeout|failed)': 7,
        r'service\s+(stopped|failed|unavailable)': 7,
        r'certificate\s+(expired|invalid)': 8,
        r'license\s+expired': 7,
        r'configuration\s+error': 7,
        r'access\s+denied': 6,
        r'permission\s+denied': 6,
        r'file\s+not\s+found': 5,
    }
    
    # Patterns à IGNORER (bruit, événements normaux)
    IGNORE_PATTERNS = {
        r'informational',
        r'session\s+established',
        r'connection\s+closed\s+normally',
        r'user\s+logged\s+in\s+successfully',
        r'service\s+started\s+successfully',
        r'backup\s+completed\s+successfully',
        r'scheduled\s+task\s+completed',
        r'heartbeat\s+received',
        r'keepalive',
        r'link\s+up',
        r'interface\s+up',
    }
    
    # Seuils de répétition pour créer un ticket
    REPETITION_THRESHOLDS = {
        'error': 3,      # 3 erreurs identiques = ticket
        'warning': 5,    # 5 warnings identiques = ticket
        'notice': 10,    # 10 notices identiques = ticket
    }
    
    # Fenêtre temporelle pour compter les répétitions (en minutes)
    TIME_WINDOW = 10
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.event_history = {}  # Stocke les événements récents pour détecter répétitions
        self.ticket_created = {}  # Évite de créer plusieurs tickets pour même problème
    
    def log(self, message):
        if self.log_callback:
            try:
                self.log_callback(message)
            except:
                print(message)
        else:
            print(message)
    
    def should_create_ticket(self, log_entry, priority):
        """
        Détermine si un ticket doit être créé pour ce log
        
        Retourne: (should_create: bool, reason: str, adjusted_priority: int)
        """
        message = log_entry.get('message', '').lower()
        severity = log_entry.get('severity', 'notice').lower()
        facility = log_entry.get('facility', '').lower()
        
        # 1. VÉRIFIER SI ON DOIT IGNORER
        for pattern in self.IGNORE_PATTERNS:
            if re.search(pattern, message, re.IGNORECASE):
                return False, "Événement normal (ignoré)", priority
        
        # 2. VÉRIFIER PATTERNS CRITIQUES
        for pattern, crit_priority in self.CRITICAL_PATTERNS.items():
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                # Cas spécial : authentification échouée avec compteur
                if 'authentication' in pattern and 'attempts' in pattern:
                    try:
                        attempts = int(match.group(1))
                        if attempts >= 5:
                            return True, f"⚠️ CRITIQUE: {attempts} tentatives d'authentification échouées", 10
                        elif attempts >= 3:
                            return True, f"⚠️ Multiple tentatives d'authentification ({attempts})", 9
                    except:
                        pass
                
                return True, f"🚨 CRITIQUE: {pattern[:50]}", crit_priority
        
        # 3. VÉRIFIER PATTERNS HAUTE PRIORITÉ
        for pattern, high_priority in self.HIGH_PRIORITY_PATTERNS.items():
            if re.search(pattern, message, re.IGNORECASE):
                # Vérifier si répété
                event_key = self._get_event_key(log_entry, pattern)
                repetitions = self._count_repetitions(event_key, log_entry['timestamp'])
                
                threshold = self.REPETITION_THRESHOLDS.get(severity, 3)
                
                if repetitions >= threshold:
                    return True, f"🔁 RÉPÉTÉ {repetitions}x: {pattern[:50]}", high_priority + 1
        
        # 4. VÉRIFIER SEVERITY CRITIQUE (emerg, alert, crit, err)
        if severity in ['emerg', 'alert', 'crit']:
            return True, f"🔴 Severity critique: {severity.upper()}", priority
        
        if severity == 'err' or severity == 'error':
            # Pour les erreurs, vérifier si répétées
            event_key = self._get_event_key(log_entry, 'error')
            repetitions = self._count_repetitions(event_key, log_entry['timestamp'])
            
            if repetitions >= self.REPETITION_THRESHOLDS['error']:
                return True, f"🔁 Erreur répétée {repetitions}x", priority + 1
        
        # 5. VÉRIFIER FACILITY CRITIQUE
        critical_facilities = ['firewall', 'asqd', 'security', 'auth']
        if any(cf in facility for cf in critical_facilities):
            if priority >= 7:
                return True, f"🛡️ Facility critique: {facility}", priority
        
        # 6. VÉRIFIER SI DÉJÀ TRAITÉ RÉCEMMENT
        ticket_key = self._get_ticket_key(log_entry)
        if ticket_key in self.ticket_created:
            last_ticket_time = self.ticket_created[ticket_key]
            time_diff = (log_entry['timestamp'] - last_ticket_time).total_seconds() / 60
            
            if time_diff < 60:  # Moins d'1h
                return False, f"Ticket déjà créé il y a {int(time_diff)}min", priority
        
        # 7. DÉCISION FINALE BASÉE SUR PRIORITÉ
        if priority >= 9:
            return True, f"🔴 Priorité critique: {priority}/10", priority
        elif priority >= 7:
            # Haute priorité mais vérifier répétitions
            event_key = self._get_event_key(log_entry, 'high_priority')
            repetitions = self._count_repetitions(event_key, log_entry['timestamp'])
            
            if repetitions >= 2:
                return True, f"🟠 Haute priorité répétée {repetitions}x", priority
        
        # Par défaut : pas de ticket
        return False, f"Priorité {priority}/10 - Pas de ticket", priority
    
    def _get_event_key(self, log_entry, pattern_type):
        """Génère une clé unique pour un type d'événement"""
        ip = log_entry.get('ip', 'unknown')
        facility = log_entry.get('facility', 'unknown')
        # Message normalisé (sans nombres/IPs pour grouper les similaires)
        message = re.sub(r'\d+\.\d+\.\d+\.\d+', 'IP', log_entry.get('message', ''))
        message = re.sub(r'\d+', 'N', message)
        message_short = message[:100]
        
        return f"{ip}_{facility}_{pattern_type}_{hash(message_short)}"
    
    def _get_ticket_key(self, log_entry):
        """Génère une clé pour éviter les tickets dupliqués"""
        ip = log_entry.get('ip', 'unknown')
        facility = log_entry.get('facility', 'unknown')
        message_hash = hash(log_entry.get('message', '')[:200])
        
        return f"{ip}_{facility}_{message_hash}"
    
    def _count_repetitions(self, event_key, current_time):
        """Compte les répétitions d'un événement dans la fenêtre temporelle"""
        # Nettoyer l'historique ancien
        cutoff_time = current_time - timedelta(minutes=self.TIME_WINDOW)
        
        if event_key not in self.event_history:
            self.event_history[event_key] = []
        
        # Retirer événements trop vieux
        self.event_history[event_key] = [
            t for t in self.event_history[event_key]
            if t > cutoff_time
        ]
        
        # Ajouter l'événement actuel
        self.event_history[event_key].append(current_time)
        
        return len(self.event_history[event_key])
    
    def mark_ticket_created(self, log_entry):
        """Marque qu'un ticket a été créé pour cet événement"""
        ticket_key = self._get_ticket_key(log_entry)
        self.ticket_created[ticket_key] = log_entry['timestamp']
    
    def get_statistics(self):
        """Retourne des statistiques sur les événements analysés"""
        total_events = sum(len(times) for times in self.event_history.values())
        total_tickets = len(self.ticket_created)
        
        return {
            'total_events_tracked': total_events,
            'total_tickets_created': total_tickets,
            'unique_event_types': len(self.event_history),
            'reduction_rate': f"{100 - (total_tickets / max(total_events, 1) * 100):.1f}%"
        }
    
    def reset(self):
        """Réinitialise l'analyseur"""
        self.event_history.clear()
        self.ticket_created.clear()
        self.log("🔄 Analyseur Syslog réinitialisé")
    
    def clean_old_data(self, hours=24):
        """Nettoie les données de plus de X heures"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        # Nettoyer historique
        for key in list(self.event_history.keys()):
            self.event_history[key] = [
                t for t in self.event_history[key]
                if t > cutoff
            ]
            if not self.event_history[key]:
                del self.event_history[key]
        
        # Nettoyer tickets créés
        for key in list(self.ticket_created.keys()):
            if self.ticket_created[key] < cutoff:
                del self.ticket_created[key]
        
        self.log(f"🧹 Données de plus de {hours}h nettoyées")


# EXEMPLE D'UTILISATION
if __name__ == "__main__":
    analyzer = SyslogAnalyzer()
    
    # Test 1 : Événement critique
    log_critical = {
        'ip': '192.168.1.254',
        'facility': 'firewall',
        'severity': 'alert',
        'message': 'Attack detected from 10.0.0.5',
        'timestamp': datetime.now()
    }
    
    should_create, reason, priority = analyzer.should_create_ticket(log_critical, 9)
    print(f"Test 1 - Attaque détectée:")
    print(f"  Créer ticket: {should_create}")
    print(f"  Raison: {reason}")
    print(f"  Priorité: {priority}/10\n")
    
    # Test 2 : Warning simple (ne devrait PAS créer de ticket)
    log_warning = {
        'ip': '192.168.1.254',
        'facility': 'system',
        'severity': 'warning',
        'message': 'Connection timeout to 192.168.1.100',
        'timestamp': datetime.now()
    }
    
    should_create, reason, priority = analyzer.should_create_ticket(log_warning, 6)
    print(f"Test 2 - Warning simple:")
    print(f"  Créer ticket: {should_create}")
    print(f"  Raison: {reason}\n")
    
    # Test 3 : Warning répété (DEVRAIT créer un ticket)
    for i in range(5):
        should_create, reason, priority = analyzer.should_create_ticket(log_warning, 6)
    
    print(f"Test 3 - Warning répété 5x:")
    print(f"  Créer ticket: {should_create}")
    print(f"  Raison: {reason}\n")
    
    # Statistiques
    stats = analyzer.get_statistics()
    print(f"Statistiques:")
    for key, value in stats.items():
        print(f"  {key}: {value}")