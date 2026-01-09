import threading
from datetime import datetime

class MonitoringThread:
    def __init__(self, log_reader, event_filter, analyzer_callback, 
                 refresh_callback, polling_interval):
        self.log_reader = log_reader
        self.event_filter = event_filter
        self.analyzer_callback = analyzer_callback
        self.refresh_callback = refresh_callback
        self.polling_interval = polling_interval
        
        self.monitoring = False
        self.thread = None
    
    def start(self, log_callback, status_callback):
        self.monitoring = True
        self.thread = threading.Thread(
            target=self._monitor_loop,
            args=(log_callback, status_callback),
            daemon=True
        )
        self.thread.start()
    
    def stop(self):
        self.monitoring = False
    
    def _monitor_loop(self, log_callback, status_callback):
        while self.monitoring:
            try:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                status_callback(now)
                
                log_callback("Vérification en cours sur toutes les sources...", "info")
                events = self.log_reader.read_new_events()
                
                if not self.monitoring:
                    break
                
                if events:
                    filtered_events = self.event_filter.filter_events(
                        events, enable_online_check=False
                    )
                    
                    if not self.monitoring:
                        break
                    
                    if filtered_events:
                        log_callback(f"\n⚠️ {len(filtered_events)} nouvelle(s) menace(s)!", "warning")
                        
                        for i, event in enumerate(filtered_events, 1):
                            if not self.monitoring:
                                log_callback(f"\n🛑 Analyse interrompue à {i}/{len(filtered_events)}", "warning")
                                break
                            
                            log_callback(f"[{i}/{len(filtered_events)}] {event['source']} - Event {event['event_id']}", "warning")
                            success = self.analyzer_callback(event)
                            
                            if not success:
                                break
                        
                        if self.monitoring:
                            self.refresh_callback()
                            log_callback(f"✅ {len(filtered_events)} incident(s) traités\n", "success")
                    else:
                        log_callback(f"✅ {len(events)} événement(s) détectés mais aucun critique\n", "info")
                else:
                    log_callback("✅ Aucune nouvelle menace\n", "info")
                
                for _ in range(self.polling_interval):
                    if not self.monitoring:
                        break
                    threading.Event().wait(1)
                
            except Exception as e:
                log_callback(f"Erreur de surveillance: {e}", "error")
                threading.Event().wait(self.polling_interval)


class InitialCheckThread:
    def __init__(self, log_reader, event_filter, analyzer_callback, 
                 refresh_callback, check_hours):
        self.log_reader = log_reader
        self.event_filter = event_filter
        self.analyzer_callback = analyzer_callback
        self.refresh_callback = refresh_callback
        self.check_hours = check_hours
        
        self.running = False
        self.thread = None
    
    def start(self, log_callback):
        self.running = True
        self.thread = threading.Thread(
            target=self._check_loop,
            args=(log_callback,),
            daemon=True
        )
        self.thread.start()
    
    def stop(self):
        self.running = False
    
    def _check_loop(self, log_callback):
        try:
            events = self.log_reader.read_initial_check(hours=self.check_hours)
            
            if not self.running:
                log_callback("Vérification annulée", "warning")
                return
            
            if events:
                log_callback(f"\n📋 {len(events)} événements bruts détectés", "info")
                
                filtered_events = self.event_filter.filter_events(
                    events, enable_online_check=True
                )
                
                if not self.running:
                    return
                
                if filtered_events:
                    log_callback(f"\n⚠️ {len(filtered_events)} menaces à analyser\n", "warning")
                    
                    for i, event in enumerate(filtered_events, 1):
                        if not self.running:
                            log_callback(f"\n🛑 Analyse interrompue à {i}/{len(filtered_events)}", "warning")
                            break
                        
                        log_callback(f"[{i}/{len(filtered_events)}] Analyse: {event['source']} - Event {event['event_id']}", "warning")
                        
                        success = self.analyzer_callback(event)
                        if not success:
                            break
                    
                    if self.running:
                        self.refresh_callback()
                        log_callback(f"\n✅ Analyse terminée: {len(filtered_events)} incident(s)\n", "success")
                else:
                    log_callback(f"\n✅ Aucun événement critique après filtrage\n", "success")
            else:
                log_callback("\n✅ Aucune menace détectée\n", "success")
                
        except Exception as e:
            log_callback(f"Erreur lors de l'analyse: {e}", "error")
        finally:
            self.running = False