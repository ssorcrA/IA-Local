"""
Lecteur unifié - MARQUAGE SOURCE AUTOMATIQUE
Fichier : unified_log_reader.py - VERSION FINALE

✅ CORRECTIF :
- Tous les events de ForwardedEvents.evtx → _source_type = 'forwarded_events'
- Permet attribution automatique au Serveur AD
"""
import os
from datetime import datetime, timedelta
from event_reader import EventReader
from syslog_reader import SyslogReader


class UnifiedLogReader:
    """Lecteur unifié avec marquage automatique de la source"""
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        
        self.event_reader = EventReader(log_callback=log_callback)
        self.syslog_reader = SyslogReader(log_callback=log_callback, verbose=False)
        
        self.log_sources = {
            'forwarded_events': r"C:\IA\JournalTransfert\ForwardedEvents.evtx",
            'syslog': r"\\SRV-SYSLOG\surveillence$\syslog",
        }
        
        self.available_sources = []
        self.syslog_first_run = True
        
        self.syslog_events_count = 0
        self.syslog_last_size = 0
    
    def log(self, message, silent=False):
        if silent:
            return
        
        if self.log_callback:
            try:
                self.log_callback(message)
            except:
                print(message)
        else:
            print(message)
    
    def check_syslog_status(self, silent=True):
        syslog_path = self.log_sources['syslog']
        
        if not os.path.exists(syslog_path):
            if not silent:
                self.log(f"   ❌ Fichier introuvable: {syslog_path}")
            return False
        
        try:
            size = os.path.getsize(syslog_path)
            
            if not silent:
                size_mb = size / (1024 * 1024)
                self.log(f"   📊 Taille: {size_mb:.2f} MB")
            
            self.syslog_last_size = size
            return True
            
        except Exception as e:
            if not silent:
                self.log(f"   ❌ Erreur lecture: {e}")
            return False
    
    def check_availability(self):
        self.log("\n🔍 VÉRIFICATION DES SOURCES DE LOGS")
        self.log("=" * 80)
        
        # 1. ForwardedEvents
        try:
            self.event_reader.check_availability()
            self.available_sources.append('forwarded_events')
            self.log("✅ ForwardedEvents : Disponible (→ Serveur AD)")
        except Exception as e:
            self.log(f"⚠️ ForwardedEvents : Indisponible ({e})")
        
        # 2. Syslog
        try:
            self.log("\n🔗 SOURCE : Syslog Principal")
            self.log("-" * 80)
            
            if self.check_syslog_status(silent=False):
                self.syslog_reader.check_availability()
                self.available_sources.append('syslog')
                self.log("✅ Syslog principal : Disponible")
            else:
                self.log("❌ Syslog : État fichier problématique")
            
        except Exception as e:
            self.log(f"⚠️ Syslog principal : Indisponible ({e})")
        
        self.log("=" * 80)
        self.log(f"📊 TOTAL : {len(self.available_sources)} source(s) disponible(s)\n")
        
        if not self.available_sources:
            raise Exception("Aucune source de logs disponible !")
        
        return True
    
    def _mark_events_as_forwarded(self, events):
        """
        🔥 MARQUE AUTOMATIQUEMENT TOUS LES EVENTS DE FORWARDEDEVENTS
        
        Permet à DeviceDetector de les attribuer au Serveur AD
        """
        for event in events:
            event['_source_type'] = 'forwarded_events'
            event['_source_file'] = 'ForwardedEvents.evtx'
            event['_is_from_forwarded'] = True
        
        return events
    
    def read_initial_check(self, hours=24):
        """Analyse complète sur X heures"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        self.log(f"\n📅 ANALYSE {hours}H - SCAN COMPLET")
        self.log("=" * 80)
        
        all_events = []
        
        # 1. ForwardedEvents (Serveur AD)
        if 'forwarded_events' in self.available_sources:
            try:
                self.log("\n📘 SOURCE : ForwardedEvents.evtx → Serveur AD")
                self.log("-" * 80)
                
                events = self.event_reader.read_events(since_time=cutoff_time)
                
                # 🔥 MARQUAGE AUTOMATIQUE POUR SERVEUR AD
                events = self._mark_events_as_forwarded(events)
                
                all_events.extend(events)
                self.log(f"✅ {len(events)} événement(s) ForwardedEvents")
                self.log(f"   → Seront attribués au Serveur AD (192.168.10.10)\n")
            
            except Exception as e:
                self.log(f"❌ Erreur ForwardedEvents: {e}\n")
        
        # 2. Syslog (Équipements réseau)
        if 'syslog' in self.available_sources:
            try:
                self.log("\n🔗 SOURCE : Syslog → Équipements réseau")
                self.log("-" * 80)
                self.log("📖 Lecture silencieuse en cours...")
                
                events = self.syslog_reader.read_initial_check(hours=hours)
                
                self.syslog_events_count = len(events)
                
                self.log(f"\n✅ {len(events)} événement(s) Syslog détectés")
                
                if len(events) == 0:
                    self.log("💡 Aucun événement Syslog critique dans la période")
                
                all_events.extend(events)
            
            except Exception as e:
                self.log(f"❌ Erreur Syslog: {e}\n")
        
        all_events.sort(key=lambda x: x.get('_priority', 0), reverse=True)
        
        self.log("=" * 80)
        self.log(f"📊 TOTAL GLOBAL : {len(all_events)} événement(s) collecté(s)\n")
        
        return all_events
    
    def read_new_events(self):
        """Surveillance continue - Lecture nouveaux événements"""
        all_events = []
        
        # 1. ForwardedEvents (Serveur AD)
        if 'forwarded_events' in self.available_sources:
            try:
                last_record = self.event_reader.get_last_record_number()
                
                if last_record > 0:
                    events = self.event_reader.read_events(since_record=last_record, silent=True)
                else:
                    cutoff = datetime.now() - timedelta(hours=2)
                    events = self.event_reader.read_events(since_time=cutoff, silent=True)
                
                # 🔥 MARQUAGE AUTOMATIQUE POUR SERVEUR AD
                events = self._mark_events_as_forwarded(events)
                
                all_events.extend(events)
            
            except:
                pass
        
        # 2. Syslog (Équipements réseau)
        if 'syslog' in self.available_sources:
            try:
                if self.syslog_first_run:
                    events = self.syslog_reader.read_startup_check()
                    self.syslog_first_run = False
                else:
                    events = self.syslog_reader.read_new_events()
                
                self.syslog_events_count = len(events)
                all_events.extend(events)
            
            except:
                pass
        
        all_events.sort(key=lambda x: x.get('_priority', 0), reverse=True)
        
        return all_events
    
    def get_sources_summary(self):
        """Résumé des sources disponibles"""
        summary = []
        for source in self.available_sources:
            if source == 'forwarded_events':
                summary.append("✅ ForwardedEvents (EVTX) → Serveur AD")
            elif source == 'syslog':
                summary.append("✅ Syslog Principal (4 équipements réseau)")
        return summary
    
    def get_syslog_stats(self):
        """Statistiques Syslog"""
        return {
            'events_count': self.syslog_events_count,
            'last_size': self.syslog_last_size
        }