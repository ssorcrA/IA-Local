"""
Lecteur d'événements Windows - MARQUE FORWARDEDEVENTS
Fichier : event_reader.py - VERSION CORRIGÉE

✅ Ajoute le flag _is_from_forwarded = True
"""
from datetime import datetime, timedelta
import os
import sys
import shutil
import time
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
    
    EVENT_PRIORITIES = {
        1102: 10, 4719: 10, 4794: 10,
        4765: 9, 7045: 9, 4697: 9,
        4625: 8, 1001: 8, 4724: 8, 4728: 8, 4732: 8, 4756: 8,
        41: 7, 6008: 7, 4720: 7, 4648: 7,
        4688: 6, 4722: 6, 1311: 6, 2087: 6, 2088: 6,
        1000: 5, 1002: 5,
    }
    
    def __init__(self, log_callback=None, verbose=False):
        self.log_callback = log_callback
        self.verbose = verbose
        self.last_record_number = 0
        self.last_check_time = None
        self.log_file = LOG_FILE
        self.temp_log_file = None
        self.temp_dir = os.path.join(os.path.dirname(self.log_file), "temp")
        self.current_pid = os.getpid()
        
        self.force_copy_mode = False
    
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
    
    def debug(self, message, silent=False):
        if silent:
            return
        if self.verbose:
            self.log(f"   [DEBUG] {message}")
    
    def get_priority_emoji(self, event_id, event_type):
        priority = self.EVENT_PRIORITIES.get(event_id, 5)
        
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
    
    def cleanup_old_temp_files(self):
        try:
            if not os.path.exists(self.temp_dir):
                return
            
            cleaned = 0
            for file in os.listdir(self.temp_dir):
                if not file.startswith('temp_') or not file.endswith('.evtx'):
                    continue
                
                try:
                    file_pid = int(file.replace('temp_', '').replace('.evtx', ''))
                    
                    if file_pid != self.current_pid:
                        file_path = os.path.join(self.temp_dir, file)
                        
                        try:
                            os.remove(file_path)
                            cleaned += 1
                        except:
                            pass
                except:
                    pass
            
            if cleaned > 0:
                self.debug(f"🧹 {cleaned} ancienne(s) copie(s) nettoyée(s)", silent=True)
        except:
            pass
    
    def create_temp_copy(self, silent=False):
        try:
            os.makedirs(self.temp_dir, exist_ok=True)
            
            temp_file = os.path.join(self.temp_dir, f"temp_{self.current_pid}.evtx")
            
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            
            self.log(f"📋 Création copie temporaire...", silent=silent)
            shutil.copy2(self.log_file, temp_file)
            self.log(f"✅ Copie créée: temp_{self.current_pid}.evtx", silent=silent)
            
            return temp_file
        except Exception as e:
            self.log(f"⚠️  Impossible de créer la copie: {e}", silent=silent)
            return None
    
    def check_availability(self):
        if not WINDOWS_EVENTS_AVAILABLE:
            raise Exception("pywin32 non installé: pip install pywin32")
        
        if not os.path.exists(self.log_file):
            raise Exception(f"Fichier EVTX introuvable: {self.log_file}")
        
        size_mb = os.path.getsize(self.log_file) / (1024 * 1024)
        self.log(f"✅ Fichier détecté: {self.log_file} ({size_mb:.2f} MB)")
        
        self.cleanup_old_temp_files()
        
        file_path = os.path.abspath(self.log_file)
        
        try:
            hand = win32evtlog.OpenBackupEventLog(None, file_path)
            win32evtlog.CloseEventLog(hand)
            self.log(f"✅ Accès direct au fichier OK")
            self.force_copy_mode = False
            return True
        except Exception as e:
            error_str = str(e)
            
            if "32" in error_str or "utilisé par un autre processus" in error_str:
                self.log(f"⚠️  Fichier verrouillé (erreur 32) - Mode copie forcé", "warning")
                self.force_copy_mode = True
            else:
                self.log(f"⚠️  Accès direct impossible: {str(e)}")
            
            self.log(f"📄 Utilisation de copie temporaire obligatoire...")
            
            self.temp_log_file = self.create_temp_copy()
            
            if self.temp_log_file:
                try:
                    hand = win32evtlog.OpenBackupEventLog(None, self.temp_log_file)
                    win32evtlog.CloseEventLog(hand)
                    self.log(f"✅ Copie temporaire accessible")
                    return True
                except Exception as e2:
                    self.log(f"❌ Échec copie temporaire: {e2}")
                    raise Exception("Impossible d'accéder au fichier EVTX")
            else:
                raise Exception("Impossible d'accéder au fichier EVTX")
    
    def get_working_file(self):
        if self.force_copy_mode:
            return self.temp_log_file if self.temp_log_file else None
        
        if self.temp_log_file and os.path.exists(self.temp_log_file):
            return self.temp_log_file
        return os.path.abspath(self.log_file)
    
    def read_events(self, since_time=None, since_record=None, silent=False):
        """
        🔥 MARQUE _is_from_forwarded = True
        """
        if not WINDOWS_EVENTS_AVAILABLE:
            raise Exception("pywin32 requis")
        
        if self.force_copy_mode or (since_record is not None and since_record > 0):
            self.debug(f"📄 Mise à jour copie...", silent=silent)
            
            if self.temp_log_file and os.path.exists(self.temp_log_file):
                try:
                    os.remove(self.temp_log_file)
                    self.temp_log_file = None
                except:
                    pass
            
            self.temp_log_file = self.create_temp_copy(silent=silent)
        
        working_file = self.get_working_file()
        
        if not working_file or not os.path.exists(working_file):
            self.log(f"⚠️  Fichier introuvable, recréation...", silent=silent)
            self.temp_log_file = self.create_temp_copy(silent=silent)
            working_file = self.get_working_file()
            
            if not working_file or not os.path.exists(working_file):
                raise Exception(f"Fichier EVTX introuvable: {working_file}")
        
        events = []
        hand = None
        
        try:
            self.log(f"📂 Lecture: {os.path.basename(working_file)}", silent=silent)
            
            try:
                hand = win32evtlog.OpenBackupEventLog(None, working_file)
            except Exception as open_error:
                self.log(f"⚠️  Erreur ouverture, recréation copie...", silent=silent)
                
                if self.temp_log_file:
                    try:
                        os.remove(self.temp_log_file)
                    except:
                        pass
                
                self.temp_log_file = self.create_temp_copy(silent=silent)
                
                if self.temp_log_file:
                    working_file = self.temp_log_file
                    hand = win32evtlog.OpenBackupEventLog(None, working_file)
                else:
                    raise
            
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
            
            if since_record:
                self.log(f"📖 Recherche après record #{since_record}...", silent=silent)
            elif since_time:
                self.log(f"📖 Depuis {since_time.strftime('%Y-%m-%d %H:%M:%S')}...", silent=silent)
            else:
                self.log(f"📖 Lecture complète...", silent=silent)
            
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
                            'message': '',
                            
                            # 🔥 FLAG FORWARDEDEVENTS
                            '_is_from_forwarded': True
                        }
                        
                        try:
                            msg = win32evtlogutil.SafeFormatMessage(event, working_file)
                            if msg:
                                event_data['message'] = msg
                            else:
                                event_data['message'] = f"Event ID {event_data['event_id']} from {event_data['source']}"
                        except:
                            event_data['message'] = f"Event ID {event_data['event_id']} from {event_data['source']}"
                        
                        event_data['_priority'] = self.EVENT_PRIORITIES.get(event_data['event_id'], 5)
                        
                        events.append(event_data)
                        events_found += 1
                        
                        if event.RecordNumber > self.last_record_number:
                            self.last_record_number = event.RecordNumber
                        
                        if total_read % 1000 == 0:
                            self.debug(f"{total_read} scannés, {events_found} trouvés", silent=silent)
                
                except Exception as read_error:
                    error_str = str(read_error)
                    if "No more data" in error_str or "handle is invalid" in error_str:
                        break
                    else:
                        self.log(f"⚠️  Erreur lecture: {read_error}", silent=silent)
                        break
            
            events.sort(key=lambda x: x['record_number'])
            
            if not silent:
                self.log(f"📊 RÉSULTAT:")
                self.log(f"   • Scannés: {total_read}")
                self.log(f"   • Erreurs: {errors_found}")
                self.log(f"   • Warnings: {warnings_found}")
                self.log(f"   • TOTAL: {events_found}")
            
            self.last_check_time = datetime.now()
            
            return events
            
        except Exception as e:
            error_detail = f"Erreur lecture EVTX: {str(e)}"
            self.log(f"❌ {error_detail}", silent=silent)
            raise Exception(error_detail)
        
        finally:
            if hand:
                try:
                    win32evtlog.CloseEventLog(hand)
                except:
                    pass
    
    def read_initial_check(self, hours=24):
        cutoff_time = datetime.now() - timedelta(hours=hours)
        self.log(f"🔍 Vérification {hours}h...")
        self.log(f"   Depuis: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return self.read_events(since_time=cutoff_time, silent=False)
    
    def read_new_events(self):
        if self.last_record_number == 0:
            cutoff = datetime.now() - timedelta(hours=2)
            return self.read_events(since_time=cutoff, silent=True)
        
        return self.read_events(since_record=self.last_record_number, silent=True)
    
    def get_last_record_number(self):
        return self.last_record_number
    
    def set_last_record_number(self, record_number):
        self.last_record_number = record_number
        self.log(f"📌 Record: #{record_number}")
    
    def cleanup(self):
        if self.temp_log_file and os.path.exists(self.temp_log_file):
            try:
                os.remove(self.temp_log_file)
                self.temp_log_file = None
            except:
                pass
    
    def __del__(self):
        self.cleanup()