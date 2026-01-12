"""
Threads de surveillance AVEC ARRÊT IMMÉDIAT IA
Fichier : monitoring_thread.py - VERSION FINALE CORRIGÉE
CORRECTIFS:
- Arrêt immédiat de l'IA lors du stop
- Fermeture des sessions HTTP
- Pas de logs Syslog en surveillance continue
"""
import threading
from datetime import datetime
import time


class MonitoringThread:
    """Thread de surveillance continue"""
    
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
    
    def set_ai_analyzer(self, ai_analyzer):
        """Définit la référence à l'analyseur IA"""
        self.ai_analyzer = ai_analyzer
    
    def start(self, log_callback, status_callback, ai_analyzer=None):
        """Démarre la surveillance"""
        if ai_analyzer:
            self.ai_analyzer = ai_analyzer
        
        # Réinitialiser le flag d'arrêt de l'IA
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
        """Arrête la surveillance ET l'IA immédiatement"""
        log_callback = self.thread._args[0] if self.thread and self.thread._args else print
        
        log_callback("🛑 ARRÊT EN COURS...", "warning")
        log_callback("   → Arrêt de la surveillance", "warning")
        
        # 1. Arrêter le monitoring
        self.monitoring = False
        
        # 2. CRITIQUE: Arrêter l'IA immédiatement
        if self.ai_analyzer:
            log_callback("   → Interruption de l'IA...", "warning")
            self.ai_analyzer.request_stop()
            
            # Attendre max 2 secondes que l'IA s'arrête
            wait_time = 0
            while self.ai_analyzer.current_session and wait_time < 2:
                time.sleep(0.1)
                wait_time += 0.1
            
            if self.ai_analyzer.current_session:
                log_callback("   ⚠️ IA forcée à s'arrêter", "warning")
        
        # 3. Arrêter les lecteurs de logs
        if hasattr(self.log_reader, 'event_reader'):
            log_callback("   → Arrêt EventReader", "warning")
            self.log_reader.event_reader.stop_requested = True
        
        if hasattr(self.log_reader, 'syslog_reader'):
            log_callback("   → Arrêt SyslogReader", "warning")
            self.log_reader.syslog_reader.request_stop()
        
        log_callback("✅ Surveillance arrêtée", "success")
    
    def _monitor_loop(self, log_callback, status_callback):
        """Boucle de surveillance"""
        while self.monitoring:
            try:
                # Vérifier arrêt demandé
                if not self.monitoring:
                    break
                
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                status_callback(now)
                
                # Lecture des événements (SILENCIEUX pour Syslog)
                log_callback("🔍 Vérification en cours sur toutes les sources...", "info")
                events = self.log_reader.read_new_events()
                
                # Vérifier arrêt
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
                        log_callback(f"\n⚠️ {len(filtered_events)} nouvelle(s) menace(s)!", "warning")
                        
                        # Traiter chaque événement
                        for i, event in enumerate(filtered_events, 1):
                            # Vérifier arrêt AVANT chaque analyse
                            if not self.monitoring:
                                log_callback(f"\n🛑 Analyse interrompue à {i}/{len(filtered_events)}", "warning")
                                break
                            
                            # Vérifier si l'IA a été arrêtée
                            if self.ai_analyzer and self.ai_analyzer.stop_requested:
                                log_callback(f"\n🛑 IA arrêtée - Abandon des analyses", "warning")
                                break
                            
                            log_callback(f"[{i}/{len(filtered_events)}] {event['source']} - Event {event['event_id']}", "warning")
                            
                            # L'analyse vérifiera elle-même si arrêt demandé
                            success = self.analyzer_callback(event)
                            
                            if not success or not self.monitoring:
                                break
                        
                        # Rafraîchir si surveillance toujours active
                        if self.monitoring:
                            self.refresh_callback()
                            log_callback(f"✅ {len(filtered_events)} incident(s) traités\n", "success")
                    else:
                        log_callback(f"✅ {len(events)} événement(s) détectés mais aucun critique\n", "info")
                else:
                    log_callback("✅ Aucune nouvelle menace\n", "info")
                
                # Attente avec vérification d'arrêt toutes les secondes
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
    """Thread de vérification initiale 24h"""
    
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
    
    def set_ai_analyzer(self, ai_analyzer):
        """Définit la référence à l'analyseur IA"""
        self.ai_analyzer = ai_analyzer
    
    def start(self, log_callback, ai_analyzer=None):
        """Démarre la vérification"""
        if ai_analyzer:
            self.ai_analyzer = ai_analyzer
        
        # Réinitialiser le flag d'arrêt de l'IA
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
        """Arrête la vérification ET l'IA immédiatement"""
        log_callback = self.thread._args[0] if self.thread and self.thread._args else print
        
        log_callback("🛑 ARRÊT DE LA VÉRIFICATION...", "warning")
        log_callback("   → Arrêt du scan", "warning")
        
        # 1. Arrêter la vérification
        self.running = False
        
        # 2. CRITIQUE: Arrêter l'IA immédiatement
        if self.ai_analyzer:
            log_callback("   → Interruption de l'IA...", "warning")
            self.ai_analyzer.request_stop()
            
            # Attendre max 2 secondes
            wait_time = 0
            while self.ai_analyzer.current_session and wait_time < 2:
                time.sleep(0.1)
                wait_time += 0.1
            
            if self.ai_analyzer.current_session:
                log_callback("   ⚠️ IA forcée à s'arrêter", "warning")
        
        # 3. Arrêter les lecteurs de logs
        if hasattr(self.log_reader, 'event_reader'):
            log_callback("   → Arrêt EventReader", "warning")
            self.log_reader.event_reader.stop_requested = True
        
        if hasattr(self.log_reader, 'syslog_reader'):
            log_callback("   → Arrêt SyslogReader", "warning")
            self.log_reader.syslog_reader.request_stop()
        
        log_callback("✅ Vérification arrêtée", "success")
    
    def _check_loop(self, log_callback):
        """Boucle de vérification"""
        try:
            # Lecture des événements
            log_callback("📖 Lecture des logs...", "info")
            events = self.log_reader.read_initial_check(hours=self.check_hours)
            
            # Vérifier arrêt
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
                    
                    # Traiter chaque événement
                    for i, event in enumerate(filtered_events, 1):
                        # Vérifier arrêt AVANT chaque analyse
                        if not self.running:
                            log_callback(f"\n🛑 Analyse interrompue à {i}/{len(filtered_events)}", "warning")
                            break
                        
                        # Vérifier si l'IA a été arrêtée
                        if self.ai_analyzer and self.ai_analyzer.stop_requested:
                            log_callback(f"\n🛑 IA arrêtée - Abandon des analyses", "warning")
                            break
                        
                        log_callback(f"[{i}/{len(filtered_events)}] Analyse: {event['source']} - Event {event['event_id']}", "warning")
                        
                        # L'analyse vérifiera elle-même si arrêt demandé
                        success = self.analyzer_callback(event)
                        
                        if not success or not self.running:
                            break
                    
                    # Rafraîchir si vérification toujours active
                    if self.running:
                        self.refresh_callback()
                        log_callback(f"\n✅ Analyse terminée: {len(filtered_events)} incident(s)\n", "success")
                else:
                    log_callback(f"\n✅ Aucun événement critique après filtrage\n", "success")
            else:
                log_callback("\n✅ Aucune menace détectée\n", "success")
                
        except Exception as e:
            if self.running:
                log_callback(f"❌ Erreur lors de l'analyse: {e}", "error")
        finally:
            self.running = False