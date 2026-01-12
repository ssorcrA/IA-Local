"""
Lecteur unifié pour ForwardedEvents + Syslog + Dossiers multiples
Fichier : unified_log_reader.py
"""
import os
import glob
from datetime import datetime, timedelta
from event_reader import EventReader
from syslog_reader import SyslogReader


class UnifiedLogReader:
    """Lecteur unifié pour tous les types de logs"""
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        
        # Lecteurs spécialisés
        self.event_reader = EventReader(log_callback=log_callback)
        self.syslog_reader = SyslogReader(log_callback=log_callback)
        
        # Chemins de surveillance
        self.log_sources = {
            'forwarded_events': r"C:\IA\JournalTransfert\ForwardedEvents.evtx",
            'syslog': r"\\SRV-SYSLOG\surveillence$\syslog",
            'syslog_archive': r"\\SRV-SYSLOG\surveillence$\archive",
            'local_logs': r"C:\IA\Logs"
        }
        
        self.available_sources = []
    
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
            self.log(f"⚠️  ForwardedEvents : Indisponible ({e})")
        
        # 2. Syslog principal
        try:
            self.syslog_reader.check_availability()
            self.available_sources.append('syslog')
            self.log("✅ Syslog principal : Disponible")
        except Exception as e:
            self.log(f"⚠️  Syslog principal : Indisponible ({e})")
        
        # 3. Archive Syslog
        if os.path.exists(self.log_sources['syslog_archive']):
            archives = glob.glob(os.path.join(self.log_sources['syslog_archive'], 'syslog-*.log'))
            if archives:
                self.available_sources.append('syslog_archive')
                self.log(f"✅ Archives Syslog : {len(archives)} fichier(s) trouvé(s)")
        else:
            self.log("⚠️  Archives Syslog : Dossier introuvable")
        
        # 4. Logs locaux
        if os.path.exists(self.log_sources['local_logs']):
            local_files = glob.glob(os.path.join(self.log_sources['local_logs'], '*.log'))
            if local_files:
                self.available_sources.append('local_logs')
                self.log(f"✅ Logs locaux : {len(local_files)} fichier(s) trouvé(s)")
        else:
            self.log("⚠️  Logs locaux : Dossier introuvable")
        
        self.log("=" * 80)
        self.log(f"📊 TOTAL : {len(self.available_sources)} source(s) disponible(s)\n")
        
        if not self.available_sources:
            raise Exception("Aucune source de logs disponible !")
        
        return True
    
    def read_syslog_archives(self, since_time=None):
        """Lit les archives Syslog"""
        events = []
        archive_path = self.log_sources['syslog_archive']
        
        if not os.path.exists(archive_path):
            return events
        
        # Trouver tous les fichiers d'archive
        archive_files = sorted(glob.glob(os.path.join(archive_path, 'syslog-*.log')))
        
        self.log(f"📂 Analyse de {len(archive_files)} archive(s) Syslog...")
        
        for archive_file in archive_files:
            try:
                # Extraire la date du nom de fichier (ex: syslog-2024-01-06.log)
                filename = os.path.basename(archive_file)
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
                
                if date_match and since_time:
                    file_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
                    if file_date.date() < since_time.date():
                        continue
                
                self.log(f"   📄 {filename}...")
                
                # Lire le fichier avec le même parser que syslog principal
                with open(archive_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                for line in lines:
                    log_entry = self.syslog_reader.parse_syslog_line(line)
                    
                    if log_entry:
                        if since_time and log_entry['timestamp'] < since_time:
                            continue
                        
                        should_process, _ = self.syslog_reader.should_process_log(log_entry)
                        if should_process:
                            event = self.syslog_reader.convert_to_event_format(log_entry)
                            events.append(event)
            
            except Exception as e:
                self.log(f"   ⚠️  Erreur lecture {filename}: {e}")
        
        return events
    
    def read_local_logs(self, since_time=None):
        """Lit les logs locaux (format générique)"""
        events = []
        local_path = self.log_sources['local_logs']
        
        if not os.path.exists(local_path):
            return events
        
        log_files = glob.glob(os.path.join(local_path, '*.log'))
        
        self.log(f"📂 Analyse de {len(log_files)} fichier(s) log local...")
        
        for log_file in log_files:
            try:
                filename = os.path.basename(log_file)
                self.log(f"   📄 {filename}...")
                
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                for line in lines:
                    # Parser générique pour logs locaux
                    if not line.strip() or len(line) < 20:
                        continue
                    
                    # Détection de mots-clés critiques
                    priority = 5
                    line_lower = line.lower()
                    
                    if any(kw in line_lower for kw in ['error', 'fail', 'critical', 'alert']):
                        priority = 8
                    elif any(kw in line_lower for kw in ['warning', 'warn']):
                        priority = 6
                    
                    if priority >= 6:  # Seuil de filtrage
                        event = {
                            'record_number': hash(line) % 1000000,
                            'time_generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'source': f"📁 {filename}",
                            'event_id': priority * 1000,
                            'event_type': 'ERROR' if priority >= 8 else 'WARNING',
                            'computer': 'LocalLogs',
                            'message': line.strip()[:500],
                            '_priority': priority,
                            '_is_local_log': True
                        }
                        events.append(event)
            
            except Exception as e:
                self.log(f"   ⚠️  Erreur lecture {filename}: {e}")
        
        return events
    
    def read_all_sources(self, since_time=None, since_record=None):
        """Lit TOUTES les sources disponibles"""
        all_events = []
        
        self.log("\n🔄 LECTURE DE TOUTES LES SOURCES")
        self.log("=" * 80)
        
        # 1. ForwardedEvents
        if 'forwarded_events' in self.available_sources:
            try:
                self.log("\n📘 SOURCE : ForwardedEvents (EVTX)")
                self.log("-" * 80)
                
                if since_record:
                    events = self.event_reader.read_events(since_record=since_record)
                elif since_time:
                    events = self.event_reader.read_events(since_time=since_time)
                else:
                    events = self.event_reader.read_initial_check(hours=24)
                
                all_events.extend(events)
                self.log(f"✅ {len(events)} événement(s) ForwardedEvents\n")
            
            except Exception as e:
                self.log(f"❌ Erreur ForwardedEvents: {e}\n")
        
        # 2. Syslog principal
        if 'syslog' in self.available_sources:
            try:
                self.log("\n📗 SOURCE : Syslog Principal")
                self.log("-" * 80)
                
                if since_time:
                    events = self.syslog_reader.read_events(since_time=since_time)
                else:
                    events = self.syslog_reader.read_initial_check(hours=24)
                
                all_events.extend(events)
                self.log(f"✅ {len(events)} événement(s) Syslog\n")
            
            except Exception as e:
                self.log(f"❌ Erreur Syslog: {e}\n")
        
        # 3. Archives Syslog
        if 'syslog_archive' in self.available_sources:
            try:
                self.log("\n📙 SOURCE : Archives Syslog")
                self.log("-" * 80)
                
                events = self.read_syslog_archives(since_time=since_time)
                all_events.extend(events)
                self.log(f"✅ {len(events)} événement(s) Archives\n")
            
            except Exception as e:
                self.log(f"❌ Erreur Archives: {e}\n")
        
        # 4. Logs locaux
        if 'local_logs' in self.available_sources:
            try:
                self.log("\n📕 SOURCE : Logs Locaux")
                self.log("-" * 80)
                
                events = self.read_local_logs(since_time=since_time)
                all_events.extend(events)
                self.log(f"✅ {len(events)} événement(s) Logs Locaux\n")
            
            except Exception as e:
                self.log(f"❌ Erreur Logs Locaux: {e}\n")
        
        # Tri par priorité (plus critique d'abord)
        all_events.sort(key=lambda x: x.get('_priority', 0), reverse=True)
        
        self.log("=" * 80)
        self.log(f"📊 TOTAL GLOBAL : {len(all_events)} événement(s) collecté(s)\n")
        
        return all_events
    
    def read_initial_check(self, hours=24):
        """Vérification initiale sur toutes les sources"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        self.log(f"🔍 Vérification des {hours} dernières heures sur TOUTES les sources...")
        return self.read_all_sources(since_time=cutoff_time)
    
    def read_new_events(self):
        """Surveillance continue sur toutes les sources"""
        self.log("🔄 Recherche nouveaux événements sur TOUTES les sources...")
        
        # Pour ForwardedEvents, on utilise le record number
        last_record = self.event_reader.get_last_record_number()
        
        return self.read_all_sources(since_record=last_record if last_record > 0 else None)
    
    def get_sources_summary(self):
        """Résumé des sources"""
        summary = []
        for source in self.available_sources:
            if source == 'forwarded_events':
                summary.append("✅ ForwardedEvents (EVTX)")
            elif source == 'syslog':
                summary.append("✅ Syslog Principal")
            elif source == 'syslog_archive':
                summary.append("✅ Archives Syslog")
            elif source == 'local_logs':
                summary.append("✅ Logs Locaux")
        return summary