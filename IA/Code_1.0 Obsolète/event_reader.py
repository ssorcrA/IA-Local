"""
Lecteur d'événements Windows avec cercles colorés
Fichier : event_reader.py
"""
from datetime import datetime, timedelta
import os
import sys
import shutil
from config import LOG_FILE

try:
    import win32evtlog
    import win32evtlogutil
    import win32con
    WINDOWS_EVENTS_AVAILABLE = True
except ImportError:
    WINDOWS_EVENTS_AVAILABLE = False
    print("ATTENTION: pywin32 n'est pas installé")


class EventReader:
    """Lit les événements depuis le fichier EVTX"""
    
    # Priorités des Event IDs (1-10)
    EVENT_PRIORITIES = {
        # Niveau 10 - CRITIQUE
        1102: 10, 4719: 10, 4794: 10,
        # Niveau 9 - TRÈS HAUTE
        4765: 9, 7045: 9, 4697: 9,
        # Niveau 8 - HAUTE
        4625: 8, 1001: 8, 4724: 8, 4728: 8, 4732: 8, 4756: 8,
        # Niveau 7 - MOYENNE-HAUTE
        41: 7, 6008: 7, 4720: 7, 4648: 7,
        # Niveau 6 - MOYENNE
        4688: 6, 4722: 6, 1311: 6, 2087: 6, 2088: 6,
        # Niveau 5 - BASSE-MOYENNE
        1000: 5, 1002: 5,
    }
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.last_record_number = 0
        self.last_check_time = None
        self.log_file = LOG_FILE
        self.temp_log_file = None
    
    def log(self, message):
        if self.log_callback:
            try:
                self.log_callback(message)
            except:
                print(message)
        else:
            print(message)
    
    def get_priority_emoji(self, event_id, event_type):
        """Retourne le cercle coloré selon la priorité"""
        priority = self.EVENT_PRIORITIES.get(event_id, 5)
        
        # Ajuster selon le type
        if event_type == 'ERROR' and priority < 6:
            priority = 6
        
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
    
    def create_temp_copy(self):
        """Crée une copie temporaire du fichier EVTX"""
        try:
            temp_dir = os.path.join(os.path.dirname(self.log_file), "temp")
            os.makedirs(temp_dir, exist_ok=True)
            
            temp_file = os.path.join(temp_dir, f"temp_{os.getpid()}.evtx")
            
            self.log(f"📋 Création copie temporaire...")
            shutil.copy2(self.log_file, temp_file)
            self.log(f"✓ Copie créée: {temp_file}")
            
            return temp_file
        except Exception as e:
            self.log(f"⚠️ Impossible de créer la copie: {e}")
            return None
    
    def check_availability(self):
        """Vérifie que le fichier EVTX est accessible"""
        if not WINDOWS_EVENTS_AVAILABLE:
            raise Exception("pywin32 non installé: pip install pywin32")
        
        if not os.path.exists(self.log_file):
            raise Exception(f"Fichier EVTX introuvable: {self.log_file}")
        
        size_mb = os.path.getsize(self.log_file) / (1024 * 1024)
        self.log(f"✓ Fichier détecté: {self.log_file} ({size_mb:.2f} MB)")
        
        file_path = os.path.abspath(self.log_file)
        
        try:
            hand = win32evtlog.OpenBackupEventLog(None, file_path)
            win32evtlog.CloseEventLog(hand)
            self.log(f"✓ Accès direct au fichier OK")
            return True
        except Exception as e:
            self.log(f"⚠️ Accès direct impossible: {str(e)}")
            self.log(f"🔄 Tentative avec copie temporaire...")
            
            self.temp_log_file = self.create_temp_copy()
            
            if self.temp_log_file:
                try:
                    hand = win32evtlog.OpenBackupEventLog(None, self.temp_log_file)
                    win32evtlog.CloseEventLog(hand)
                    self.log(f"✓ Copie temporaire accessible")
                    return True
                except Exception as e2:
                    self.log(f"❌ Échec copie temporaire: {e2}")
                    raise Exception("Impossible d'accéder au fichier EVTX")
            else:
                raise Exception("Impossible d'accéder au fichier EVTX")
    
    def get_working_file(self):
        """Retourne le fichier à utiliser"""
        return self.temp_log_file if self.temp_log_file else os.path.abspath(self.log_file)
    
    def read_events(self, since_time=None, since_record=None):
        """Lit les événements ERROR et WARNING depuis le fichier EVTX"""
        if not WINDOWS_EVENTS_AVAILABLE:
            raise Exception("pywin32 requis")
        
        working_file = self.get_working_file()
        
        if not os.path.exists(working_file):
            raise Exception(f"Fichier EVTX introuvable: {working_file}")
        
        events = []
        hand = None
        
        try:
            self.log(f"📂 Lecture du fichier: {os.path.basename(working_file)}")
            
            try:
                hand = win32evtlog.OpenBackupEventLog(None, working_file)
            except Exception as open_error:
                if not self.temp_log_file:
                    self.log(f"⚠️ Erreur d'ouverture, création copie temporaire...")
                    self.temp_log_file = self.create_temp_copy()
                    if self.temp_log_file:
                        working_file = self.temp_log_file
                        hand = win32evtlog.OpenBackupEventLog(None, working_file)
                    else:
                        raise
                else:
                    raise
            
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
            
            if since_record:
                self.log(f"📖 Recherche événements après record #{since_record}...")
            elif since_time:
                self.log(f"📖 Recherche événements depuis {since_time.strftime('%Y-%m-%d %H:%M:%S')}...")
            else:
                self.log(f"📖 Lecture complète du fichier...")
            
            total_read = 0
            events_found = 0
            errors_found = 0
            warnings_found = 0
            max_events = 50000
            
            while total_read < max_events:
                try:
                    event_records = win32evtlog.ReadEventLog(hand, flags, 0)
                    
                    if not event_records:
                        break
                    
                    for event in event_records:
                        total_read += 1
                        
                        if since_record and event.RecordNumber <= since_record:
                            total_read = max_events
                            break
                        
                        if since_time:
                            try:
                                event_time = event.TimeGenerated
                                if event_time < since_time:
                                    continue
                            except:
                                pass
                        
                        event_type = None
                        if event.EventType == win32evtlog.EVENTLOG_ERROR_TYPE:
                            event_type = 'ERROR'
                            errors_found += 1
                        elif event.EventType == win32evtlog.EVENTLOG_WARNING_TYPE:
                            event_type = 'WARNING'
                            warnings_found += 1
                        else:
                            continue
                        
                        event_data = {
                            'record_number': event.RecordNumber,
                            'time_generated': event.TimeGenerated.Format(),
                            'source': event.SourceName or "Unknown",
                            'event_id': event.EventID & 0xFFFF,
                            'event_type': event_type,
                            'computer': event.ComputerName or "Unknown",
                            'message': ''
                        }
                        
                        try:
                            msg = win32evtlogutil.SafeFormatMessage(event, working_file)
                            if msg:
                                event_data['message'] = msg
                            else:
                                event_data['message'] = f"Event ID {event_data['event_id']} from {event_data['source']}"
                        except:
                            event_data['message'] = f"Event ID {event_data['event_id']} from {event_data['source']}"
                        
                        # Ajouter la priorité
                        event_data['_priority'] = self.EVENT_PRIORITIES.get(event_data['event_id'], 5)
                        
                        events.append(event_data)
                        events_found += 1
                        
                        if event.RecordNumber > self.last_record_number:
                            self.last_record_number = event.RecordNumber
                        
                        if total_read % 1000 == 0:
                            self.log(f"   ... {total_read} événements scannés, {events_found} erreurs/warnings trouvées")
                
                except Exception as read_error:
                    error_str = str(read_error)
                    if "No more data" in error_str or "handle is invalid" in error_str:
                        break
                    else:
                        self.log(f"⚠️ Erreur lecture: {read_error}")
                        break
            
            events.sort(key=lambda x: x['record_number'])
            
            self.log(f"📊 RÉSULTAT:")
            self.log(f"   • Total scanné: {total_read} événements")
            self.log(f"   • Erreurs trouvées: {errors_found}")
            self.log(f"   • Warnings trouvés: {warnings_found}")
            self.log(f"   • TOTAL INCIDENTS: {events_found}")
            
            # Afficher les sources AVEC CERCLES COLORÉS
            if events:
                sources = {}
                for event in events:
                    source = event['source']
                    sources[source] = sources.get(source, 0) + 1
                
                self.log(f"\n📋 Sources d'erreurs trouvées:")
                for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True)[:10]:
                    # Trouver la priorité max pour cette source
                    max_priority = max(e['_priority'] for e in events if e['source'] == source)
                    emoji = self.get_priority_emoji(max_priority, 'ERROR')
                    self.log(f"   {emoji} {source}: {count} incident(s)")
            
            self.last_check_time = datetime.now()
            
            return events
            
        except Exception as e:
            error_detail = f"Erreur lecture fichier EVTX: {str(e)}"
            self.log(f"❌ {error_detail}")
            raise Exception(error_detail)
        
        finally:
            if hand:
                try:
                    win32evtlog.CloseEventLog(hand)
                except:
                    pass
    
    def read_initial_check(self, hours=24):
        """Vérification initiale: lit les X dernières heures"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        self.log(f"🔍 Vérification des {hours} dernières heures...")
        self.log(f"   Recherche depuis: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return self.read_events(since_time=cutoff_time)
    
    def read_new_events(self):
        """Surveillance continue: lit uniquement les nouveaux événements"""
        self.log(f"🔄 Recherche événements après record #{self.last_record_number}")
        return self.read_events(since_record=self.last_record_number)
    
    def get_last_record_number(self):
        return self.last_record_number
    
    def set_last_record_number(self, record_number):
        self.last_record_number = record_number
        self.log(f"📌 Dernier record défini: #{record_number}")
    
    def cleanup_temp_files(self):
        """Nettoie les fichiers temporaires"""
        if self.temp_log_file and os.path.exists(self.temp_log_file):
            try:
                os.remove(self.temp_log_file)
                self.log("🧹 Fichier temporaire nettoyé")
            except:
                pass
    
    def __del__(self):
        self.cleanup_temp_files()