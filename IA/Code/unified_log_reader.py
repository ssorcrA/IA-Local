"""
Lecteur unifié - AVEC DÉMARRAGE 5 MINUTES
Fichier : unified_log_reader.py
CORRECTIF:
- ✅ Au démarrage: Syslog sur 5 minutes (pas 24h)
- ✅ Surveillance: nouvelles lignes
- ✅ Analyse 24h: scan complet
"""
import os
import glob
from datetime import datetime, timedelta
from event_reader import EventReader
from syslog_reader import SyslogReader


class UnifiedLogReader:
    """Lecteur unifié avec démarrage intelligent"""
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        
        # Lecteurs spécialisés
        self.event_reader = EventReader(log_callback=log_callback)
        self.syslog_reader = SyslogReader(log_callback=log_callback)
        
        # Chemins de surveillance
        self.log_sources = {
            'forwarded_events': r"C:\IA\JournalTransfert\ForwardedEvents.evtx",
            'syslog': r"\\SRV-SYSLOG\surveillence$\syslog",
        }
        
        self.available_sources = []
        self.first_run = True  # 🔥 Flag pour démarrage
    
    def log(self, message):
        if self.log_callback:
            try:
                self.log_callback(message)
            except:
                print(message)
        else:
            print(message)
    
    def check_availability(self):
        """Vérifie toutes les sources disponibles"""
        self.log("\n🔍 VÉRIFICATION DES SOURCES DE LOGS")
        self.log("=" * 80)
        
        # 1. ForwardedEvents
        try:
            self.event_reader.check_availability()
            self.available_sources.append('forwarded_events')
            self.log("✅ ForwardedEvents : Disponible")
        except Exception as e:
            self.log(f"⚠️ ForwardedEvents : Indisponible ({e})")
        
        # 2. Syslog principal
        try:
            self.syslog_reader.check_availability()
            self.available_sources.append('syslog')
            self.log("✅ Syslog principal : Disponible")
        except Exception as e:
            self.log(f"⚠️ Syslog principal : Indisponible ({e})")
        
        self.log("=" * 80)
        self.log(f"📊 TOTAL : {len(self.available_sources)} source(s) disponible(s)\n")
        
        if not self.available_sources:
            raise Exception("Aucune source de logs disponible !")
        
        return True
    
    def read_initial_check(self, hours=24):
        """
        🔥 ANALYSE INITIALE (scan complet)
        - ForwardedEvents : read_events(since_time)
        - Syslog : read_initial_check() → SCAN COMPLET
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        self.log(f"\n📅 ANALYSE {hours}H - SCAN COMPLET")
        self.log("=" * 80)
        
        all_events = []
        
        # 1. ForwardedEvents
        if 'forwarded_events' in self.available_sources:
            try:
                self.log("\n📘 SOURCE : ForwardedEvents (EVTX)")
                self.log("-" * 80)
                
                events = self.event_reader.read_events(since_time=cutoff_time)
                
                all_events.extend(events)
                self.log(f"✅ {len(events)} événement(s) ForwardedEvents\n")
            
            except Exception as e:
                self.log(f"❌ Erreur ForwardedEvents: {e}\n")
        
        # 2. Syslog - SCAN COMPLET
        if 'syslog' in self.available_sources:
            try:
                self.log("\n📗 SOURCE : Syslog (SCAN COMPLET)")
                self.log("-" * 80)
                
                events = self.syslog_reader.read_initial_check(hours=hours)
                
                all_events.extend(events)
                self.log(f"✅ {len(events)} événement(s) Syslog\n")
            
            except Exception as e:
                self.log(f"❌ Erreur Syslog: {e}\n")
        
        # Marquer comme non-première exécution
        self.first_run = False
        
        # Tri par priorité
        all_events.sort(key=lambda x: x.get('_priority', 0), reverse=True)
        
        self.log("=" * 80)
        self.log(f"📊 TOTAL GLOBAL : {len(all_events)} événement(s) collecté(s)\n")
        
        return all_events
    
    def read_new_events(self):
        """
        🔥 SURVEILLANCE CONTINUE
        - Si première exécution: Syslog sur 5 minutes
        - Sinon: nouvelles lignes uniquement
        """
        self.log(f"\n🔄 SURVEILLANCE - NOUVEAUX ÉVÉNEMENTS")
        self.log("=" * 80)
        
        all_events = []
        
        # 1. ForwardedEvents
        if 'forwarded_events' in self.available_sources:
            try:
                self.log("\n📘 SOURCE : ForwardedEvents")
                self.log("-" * 80)
                
                last_record = self.event_reader.get_last_record_number()
                
                if last_record > 0:
                    events = self.event_reader.read_events(since_record=last_record)
                else:
                    # Première lecture : 2h
                    cutoff = datetime.now() - timedelta(hours=2)
                    events = self.event_reader.read_events(since_time=cutoff)
                
                all_events.extend(events)
                self.log(f"✅ {len(events)} événement(s) ForwardedEvents\n")
            
            except Exception as e:
                self.log(f"❌ Erreur ForwardedEvents: {e}\n")
        
        # 2. Syslog
        if 'syslog' in self.available_sources:
            try:
                self.log("\n📗 SOURCE : Syslog")
                self.log("-" * 80)
                
                # 🔥 SI PREMIÈRE EXÉCUTION: 5 MINUTES
                if self.first_run:
                    self.log("⏰ Premier démarrage - Scan 5 dernières minutes")
                    events = self.syslog_reader.read_startup_check()
                    self.first_run = False
                else:
                    # Surveillance normale
                    events = self.syslog_reader.read_new_events()
                
                all_events.extend(events)
                self.log(f"✅ {len(events)} événement(s) Syslog\n")
            
            except Exception as e:
                self.log(f"❌ Erreur Syslog: {e}\n")
        
        # Tri par priorité
        all_events.sort(key=lambda x: x.get('_priority', 0), reverse=True)
        
        self.log("=" * 80)
        self.log(f"📊 TOTAL GLOBAL : {len(all_events)} événement(s) collecté(s)\n")
        
        return all_events
    
    def get_sources_summary(self):
        """Résumé des sources"""
        summary = []
        for source in self.available_sources:
            if source == 'forwarded_events':
                summary.append("✅ ForwardedEvents (EVTX)")
            elif source == 'syslog':
                summary.append("✅ Syslog Principal")
        return summary