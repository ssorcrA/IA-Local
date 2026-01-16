"""
Lecteur unifié - SYSLOG 100% SILENCIEUX
✅ Masque TOUTES les opérations Syslog
✅ Seulement rapports périodiques
"""
import os
from datetime import datetime, timedelta
from event_reader import EventReader
from syslog_reader import SyslogReader


class UnifiedLogReader:
    """Lecteur unifié avec Syslog silencieux"""
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        
        # Lecteurs spécialisés
        self.event_reader = EventReader(log_callback=log_callback)
        self.syslog_reader = SyslogReader(log_callback=log_callback, verbose=False)
        
        # Chemins de surveillance
        self.log_sources = {
            'forwarded_events': r"C:\IA\JournalTransfert\ForwardedEvents.evtx",
            'syslog': r"\\SRV-SYSLOG\surveillence$\syslog",
        }
        
        self.available_sources = []
        self.first_run = True
        
        # Stats Syslog (pour rapports)
        self.syslog_events_count = 0
        self.syslog_last_size = 0
    
    def log(self, message, silent=False):
        """Log avec option silent"""
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
        """Vérifie Syslog SILENCIEUSEMENT"""
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
        
        # 2. Syslog principal (vérification silencieuse)
        try:
            self.log("\n🔗 SOURCE : Syslog Principal")
            self.log("-" * 80)
            
            if self.check_syslog_status(silent=False):
                self.syslog_reader.check_availability()
                self.available_sources.append('syslog')
                self.log("✅ Syslog principal : Disponible")
                
                # Afficher les 4 équipements réseau
                self.log("\n📡 ÉQUIPEMENTS RÉSEAU SURVEILLÉS (depuis Syslog):")
                self.log("   🔥 192.168.10.254 → Stormshield UTM")
                self.log("   📡 192.168.10.11  → Borne WiFi")
                self.log("   🔌 192.168.10.15  → Switch Principal")
                self.log("   🔌 192.168.10.16  → Switch Secondaire")
                
                self.log("\n💡 NOTA: Les serveurs sont surveillés via ForwardedEvents:")
                self.log("   🖥️ 192.168.10.10  → Serveur AD (Windows Events)")
                self.log("   🤖 192.168.10.110 → Serveur IA (Windows Events)")
            else:
                self.log("❌ Syslog : État fichier problématique")
            
        except Exception as e:
            self.log(f"⚠️ Syslog principal : Indisponible ({e})")
        
        self.log("=" * 80)
        self.log(f"📊 TOTAL : {len(self.available_sources)} source(s) disponible(s)\n")
        
        if not self.available_sources:
            raise Exception("Aucune source de logs disponible !")
        
        return True
    
    def read_initial_check(self, hours=24):
        """
        🔥 ANALYSE INITIALE - Syslog silencieux
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
        
        # 🔥 2. SYSLOG - 100% SILENCIEUX
        if 'syslog' in self.available_sources:
            try:
                # Juste un message de début
                self.log("\n🔗 SOURCE : Syslog (équipements réseau)")
                self.log("-" * 80)
                self.log("📖 Lecture silencieuse en cours...")
                
                # 🔥 LECTURE SILENCIEUSE
                events = self.syslog_reader.read_initial_check(hours=hours)
                
                self.syslog_events_count = len(events)
                
                # Résultat simple
                self.log(f"\n✅ {len(events)} événement(s) Syslog détectés")
                
                if len(events) == 0:
                    self.log("💡 Aucun événement Syslog critique dans la période")
                
                all_events.extend(events)
            
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
        🔥 SURVEILLANCE CONTINUE - 100% SILENCIEUSE
        """
        all_events = []
        
        # 1. ForwardedEvents (silencieux)
        if 'forwarded_events' in self.available_sources:
            try:
                last_record = self.event_reader.get_last_record_number()
                
                if last_record > 0:
                    events = self.event_reader.read_events(since_record=last_record, silent=True)
                else:
                    cutoff = datetime.now() - timedelta(hours=2)
                    events = self.event_reader.read_events(since_time=cutoff, silent=True)
                
                all_events.extend(events)
            
            except:
                pass
        
        # 🔥 2. SYSLOG - 100% SILENCIEUX (pas de logs du tout)
        if 'syslog' in self.available_sources:
            try:
                if self.first_run:
                    # Première fois : 5 minutes (silencieux)
                    events = self.syslog_reader.read_startup_check()
                    self.first_run = False
                else:
                    # Surveillance normale (silencieux)
                    events = self.syslog_reader.read_new_events()
                
                self.syslog_events_count = len(events)
                all_events.extend(events)
            
            except:
                pass
        
        # Tri par priorité (silencieux)
        all_events.sort(key=lambda x: x.get('_priority', 0), reverse=True)
        
        return all_events
    
    def get_sources_summary(self):
        """Résumé des sources"""
        summary = []
        for source in self.available_sources:
            if source == 'forwarded_events':
                summary.append("✅ ForwardedEvents (EVTX)")
            elif source == 'syslog':
                summary.append("✅ Syslog Principal (4 équipements réseau)")
        return summary
    
    def get_syslog_stats(self):
        """Stats Syslog pour rapports"""
        return {
            'events_count': self.syslog_events_count,
            'last_size': self.syslog_last_size
        }