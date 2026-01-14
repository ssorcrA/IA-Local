"""
Threads de surveillance - VERSION CORRIGÉE
Fichier : monitoring_thread.py
CORRECTIFS:
- Affiche les vraies statistiques
- Compte créations vs mises à jour
- Affiche répartition réelle
"""
import threading
from datetime import datetime
import time


class MonitoringThread:
    """Thread de surveillance continue avec vraies stats"""
    
    def __init__(self, log_reader, event_filter, analyzer_callback, 
                 refresh_callback, polling_interval):
        self.log_reader = log_reader
        self.event_filter = event_filter
        self.analyzer_callback = analyzer_callback
        self.refresh_callback = refresh_callback
        self.polling_interval = polling_interval
        
        self.monitoring = False
        self.thread = None
        self.ai_analyzer = None
        self.ticket_manager = None
    
    def set_ai_analyzer(self, ai_analyzer):
        self.ai_analyzer = ai_analyzer
    
    def set_ticket_manager(self, ticket_manager):
        """🔥 NOUVEAU: Passer le ticket_manager pour les stats"""
        self.ticket_manager = ticket_manager
    
    def start(self, log_callback, status_callback, ai_analyzer=None):
        if ai_analyzer:
            self.ai_analyzer = ai_analyzer
        
        if self.ai_analyzer:
            self.ai_analyzer.reset_stop()
        
        self.monitoring = True
        self.thread = threading.Thread(
            target=self._monitor_loop,
            args=(log_callback, status_callback),
            daemon=True
        )
        self.thread.start()
    
    def stop(self):
        log_callback = self.thread._args[0] if self.thread and self.thread._args else print
        
        log_callback("🛑 ARRÊT EN COURS...", "warning")
        log_callback("   → Arrêt de la surveillance", "warning")
        
        self.monitoring = False
        
        if self.ai_analyzer:
            log_callback("   → Interruption de l'IA...", "warning")
            self.ai_analyzer.request_stop()
            
            wait_time = 0
            while self.ai_analyzer.current_session and wait_time < 2:
                time.sleep(0.1)
                wait_time += 0.1
            
            if self.ai_analyzer.current_session:
                log_callback("   ⚠️ IA forcée à s'arrêter", "warning")
        
        if hasattr(self.log_reader, 'event_reader'):
            log_callback("   → Arrêt EventReader", "warning")
            self.log_reader.event_reader.stop_requested = True
        
        if hasattr(self.log_reader, 'syslog_reader'):
            log_callback("   → Arrêt SyslogReader", "warning")
            self.log_reader.syslog_reader.request_stop()
        
        log_callback("✅ Surveillance arrêtée", "success")
    
    def _monitor_loop(self, log_callback, status_callback):
        """Boucle de surveillance avec vraies stats"""
        while self.monitoring:
            try:
                if not self.monitoring:
                    break
                
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                status_callback(now)
                
                # 🔥 Réinitialiser les stats du ticket_manager
                if self.ticket_manager:
                    self.ticket_manager.reset_stats()
                
                log_callback("\n🔍 Vérification en cours sur toutes les sources...", "info")
                events = self.log_reader.read_new_events()
                
                if not self.monitoring:
                    break
                
                if events:
                    # Filtrage
                    filtered_events = self.event_filter.filter_events(
                        events, enable_online_check=False
                    )
                    
                    if not self.monitoring:
                        break
                    
                    if filtered_events:
                        log_callback(f"\n⚠️ {len(filtered_events)} événement(s) à traiter!", "warning")
                        
                        for i, event in enumerate(filtered_events, 1):
                            if not self.monitoring:
                                log_callback(f"\n🛑 Analyse interrompue à {i}/{len(filtered_events)}", "warning")
                                break
                            
                            if self.ai_analyzer and self.ai_analyzer.stop_requested:
                                log_callback(f"\n🛑 IA arrêtée - Abandon des analyses", "warning")
                                break
                            
                            source_info = f"{event['source']}"
                            event_type = "🔴" if event.get('_priority', 0) >= 7 else "🟡"
                            log_callback(f"{event_type} [{i}/{len(filtered_events)}] {source_info} - Event {event['event_id']}", "warning")
                            
                            success = self.analyzer_callback(event)
                            
                            if not success or not self.monitoring:
                                break
                        
                        if self.monitoring:
                            # 🔥 AFFICHER LES VRAIES STATS
                            if self.ticket_manager:
                                stats = self.ticket_manager.get_stats()
                                log_callback(f"\n📊 STATISTIQUES DE TRAITEMENT:", "success")
                                log_callback(f"   • Événements détectés: {len(filtered_events)}", "success")
                                log_callback(f"   • Nouveaux tickets créés: {stats['created']}", "success")
                                log_callback(f"   • Tickets mis à jour: {stats['updated']}", "success")
                                log_callback(f"   • TOTAL: {stats['total']} tickets traités\n", "success")
                            else:
                                log_callback(f"✅ {len(filtered_events)} incident(s) traités\n", "success")
                            
                            self.refresh_callback()
                    else:
                        log_callback(f"✅ {len(events)} événement(s) détectés mais aucun critique\n", "info")
                else:
                    log_callback("✅ Aucune nouvelle menace\n", "info")
                
                # Attente avec vérification d'arrêt
                for _ in range(self.polling_interval):
                    if not self.monitoring:
                        break
                    time.sleep(1)
                
            except Exception as e:
                if self.monitoring:
                    log_callback(f"❌ Erreur de surveillance: {e}", "error")
                    time.sleep(self.polling_interval)
                else:
                    break


class InitialCheckThread:
    """Thread de vérification initiale 24h avec vraies stats"""
    
    def __init__(self, log_reader, event_filter, analyzer_callback, 
                 refresh_callback, check_hours):
        self.log_reader = log_reader
        self.event_filter = event_filter
        self.analyzer_callback = analyzer_callback
        self.refresh_callback = refresh_callback
        self.check_hours = check_hours
        
        self.running = False
        self.thread = None
        self.ai_analyzer = None
        self.ticket_manager = None
    
    def set_ai_analyzer(self, ai_analyzer):
        self.ai_analyzer = ai_analyzer
    
    def set_ticket_manager(self, ticket_manager):
        """🔥 NOUVEAU: Passer le ticket_manager pour les stats"""
        self.ticket_manager = ticket_manager
    
    def start(self, log_callback, ai_analyzer=None):
        if ai_analyzer:
            self.ai_analyzer = ai_analyzer
        
        if self.ai_analyzer:
            self.ai_analyzer.reset_stop()
        
        self.running = True
        self.thread = threading.Thread(
            target=self._check_loop,
            args=(log_callback,),
            daemon=True
        )
        self.thread.start()
    
    def stop(self):
        log_callback = self.thread._args[0] if self.thread and self.thread._args else print
        
        log_callback("🛑 ARRÊT DE LA VÉRIFICATION...", "warning")
        log_callback("   → Arrêt du scan", "warning")
        
        self.running = False
        
        if self.ai_analyzer:
            log_callback("   → Interruption de l'IA...", "warning")
            self.ai_analyzer.request_stop()
            
            wait_time = 0
            while self.ai_analyzer.current_session and wait_time < 2:
                time.sleep(0.1)
                wait_time += 0.1
            
            if self.ai_analyzer.current_session:
                log_callback("   ⚠️ IA forcée à s'arrêter", "warning")
        
        if hasattr(self.log_reader, 'event_reader'):
            log_callback("   → Arrêt EventReader", "warning")
            self.log_reader.event_reader.stop_requested = True
        
        if hasattr(self.log_reader, 'syslog_reader'):
            log_callback("   → Arrêt SyslogReader", "warning")
            self.log_reader.syslog_reader.request_stop()
        
        log_callback("✅ Vérification arrêtée", "success")
    
    def _check_loop(self, log_callback):
        """Boucle de vérification avec vraies stats"""
        try:
            # 🔥 Réinitialiser les stats
            if self.ticket_manager:
                self.ticket_manager.reset_stats()
            
            log_callback("📖 Lecture des logs...", "info")
            events = self.log_reader.read_initial_check(hours=self.check_hours)
            
            if not self.running:
                log_callback("🛑 Vérification annulée", "warning")
                return
            
            if events:
                log_callback(f"\n📋 {len(events)} événements bruts détectés", "info")
                
                # Filtrage
                log_callback("🔍 Filtrage des événements...", "info")
                filtered_events = self.event_filter.filter_events(
                    events, enable_online_check=True
                )
                
                if not self.running:
                    log_callback("🛑 Vérification annulée", "warning")
                    return
                
                if filtered_events:
                    log_callback(f"\n⚠️ {len(filtered_events)} menaces à analyser\n", "warning")
                    
                    for i, event in enumerate(filtered_events, 1):
                        if not self.running:
                            log_callback(f"\n🛑 Analyse interrompue à {i}/{len(filtered_events)}", "warning")
                            break
                        
                        if self.ai_analyzer and self.ai_analyzer.stop_requested:
                            log_callback(f"\n🛑 IA arrêtée - Abandon des analyses", "warning")
                            break
                        
                        source_info = f"{event['source']}"
                        event_type = "🔴" if event.get('_priority', 0) >= 7 else "🟡"
                        log_callback(f"{event_type} [{i}/{len(filtered_events)}] Analyse: {source_info} - Event {event['event_id']}", "warning")
                        
                        success = self.analyzer_callback(event)
                        
                        if not success or not self.running:
                            break
                    
                    if self.running:
                        # 🔥 AFFICHER LES VRAIES STATS
                        if self.ticket_manager:
                            stats = self.ticket_manager.get_stats()
                            log_callback(f"\n📊 STATISTIQUES FINALES:", "success")
                            log_callback(f"   • Événements bruts: {len(events)}", "info")
                            log_callback(f"   • Événements filtrés: {len(filtered_events)}", "info")
                            log_callback(f"   • Nouveaux tickets créés: {stats['created']}", "success")
                            log_callback(f"   • Tickets mis à jour: {stats['updated']}", "success")
                            log_callback(f"   • TOTAL: {stats['total']} tickets traités\n", "success")
                        else:
                            log_callback(f"\n✅ Analyse terminée: {len(filtered_events)} incident(s)\n", "success")
                        
                        self.refresh_callback()
                else:
                    log_callback(f"\n✅ Aucun événement critique après filtrage\n", "success")
            else:
                log_callback("\n✅ Aucune menace détectée\n", "success")
                
        except Exception as e:
            if self.running:
                log_callback(f"❌ Erreur lors de l'analyse: {e}", "error")
        finally:
            self.running = False