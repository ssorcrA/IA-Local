"""
MONITORING THREADS - ERREURS INSTANTANÉES + RAPPORT 1 MINUTE
Fichier : monitoring_thread.py - VERSION FINALE

✅ CORRECTIFS :
1. Erreurs affichées IMMÉDIATEMENT (pas d'attente)
2. Compte-rendu TOUJOURS à 60 secondes
3. Stats doublons détaillées dans le rapport
"""
import threading
from datetime import datetime, timedelta
import time


class MonitoringThread:
    """SURVEILLANCE CONTINUE - Erreurs instantanées + Rapport 1 min"""
    
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
        
        # 🔥 RAPPORT FIXE : 60 SECONDES
        self.REPORT_INTERVAL_SECONDS = 60
        
        # Stats minute
        self.minute_events_scanned = 0
        self.minute_threats_detected = 0
        self.minute_tickets_created = 0
        self.minute_tickets_updated = 0
        self.minute_duplicates = 0
        self.minute_device_stats = {}
        
        # Stats globales
        self.total_events_scanned = 0
        self.total_threats_detected = 0
        self.total_tickets_created = 0
        self.total_duplicates = 0
        
        self.last_report_time = None
    
    def set_ai_analyzer(self, ai_analyzer):
        self.ai_analyzer = ai_analyzer
    
    def set_ticket_manager(self, ticket_manager):
        self.ticket_manager = ticket_manager
    
    def start(self, log_callback, status_callback, ai_analyzer=None):
        if ai_analyzer:
            self.ai_analyzer = ai_analyzer
        
        if self.ai_analyzer:
            self.ai_analyzer.reset_stop()
        
        self.monitoring = True
        self.last_report_time = datetime.now()
        
        self._reset_minute_stats()
        
        self.thread = threading.Thread(
            target=self._monitor_loop,
            args=(log_callback, status_callback),
            daemon=True
        )
        self.thread.start()
    
    def stop(self):
        self.monitoring = False
        if self.ai_analyzer:
            self.ai_analyzer.request_stop()
    
    def _reset_minute_stats(self):
        """Reset stats de la minute"""
        self.minute_events_scanned = 0
        self.minute_threats_detected = 0
        self.minute_tickets_created = 0
        self.minute_tickets_updated = 0
        self.minute_duplicates = 0
        self.minute_device_stats.clear()
    
    def _show_periodic_report(self, log_callback):
        """
        🔥 RAPPORT PÉRIODIQUE - TOUJOURS À 60 SECONDES
        """
        elapsed = (datetime.now() - self.last_report_time).total_seconds()
        
        log_callback(f"\n{'='*80}", "info")
        log_callback(f"📊 COMPTE-RENDU MINUTE - {int(elapsed)}s écoulées", "success")
        log_callback(f"{'='*80}", "info")
        
        log_callback(f"\n📈 DERNIÈRE MINUTE :", "info")
        log_callback(f"   • Événements scannés : {self.minute_events_scanned}", "info")
        log_callback(f"   • Menaces détectées : {self.minute_threats_detected}", 
                    "warning" if self.minute_threats_detected > 0 else "info")
        
        # 🔥 DOUBLONS
        if self.minute_duplicates > 0:
            log_callback(f"   🔄 Doublons ignorés (<10 min) : {self.minute_duplicates}", "info")
        
        log_callback(f"   • Tickets créés : {self.minute_tickets_created}", 
                    "success" if self.minute_tickets_created > 0 else "info")
        log_callback(f"   • Tickets mis à jour : {self.minute_tickets_updated}", 
                    "success" if self.minute_tickets_updated > 0 else "info")
        
        # Détail par appareil
        if self.minute_device_stats:
            log_callback(f"\n🖥 DÉTAIL PAR APPAREIL :", "info")
            for device, stats in sorted(self.minute_device_stats.items(), 
                                       key=lambda x: x[1]['threats'], 
                                       reverse=True):
                if stats['scanned'] > 0 or stats['threats'] > 0:
                    icon = stats.get('icon', '📟')
                    log_callback(
                        f"   {icon} {device}: "
                        f"{stats['scanned']} scannés, "
                        f"{stats['threats']} menaces, "
                        f"{stats['duplicates']} doublons, "
                        f"{stats['tickets_created']} créés, "
                        f"{stats['tickets_updated']} m-à-j",
                        "info"
                    )
        
        # Stats globales
        log_callback(f"\n📊 DEPUIS DÉMARRAGE :", "info")
        log_callback(f"   • Total événements : {self.total_events_scanned}", "info")
        log_callback(f"   • Total menaces : {self.total_threats_detected}", 
                    "warning" if self.total_threats_detected > 0 else "info")
        
        if self.total_duplicates > 0:
            total_processed = self.total_threats_detected + self.total_duplicates
            reduction = (self.total_duplicates / total_processed * 100) if total_processed > 0 else 0
            log_callback(
                f"   🔄 Total doublons évités : {self.total_duplicates} ({reduction:.1f}% réduction)", 
                "info"
            )
        
        log_callback(f"   • Total tickets : {self.total_tickets_created}", 
                    "success" if self.total_tickets_created > 0 else "info")
        
        # Message si calme
        if self.minute_threats_detected == 0:
            log_callback(f"\n✅ Aucune menace durant cette période", "success")
        
        # Prochain rapport
        next_report = datetime.now() + timedelta(seconds=self.REPORT_INTERVAL_SECONDS)
        log_callback(
            f"\n⏰ Prochain compte-rendu : {next_report.strftime('%H:%M:%S')}",
            "info"
        )
        log_callback(f"{'='*80}\n", "info")
        
        # Reset
        self.last_report_time = datetime.now()
        self._reset_minute_stats()
    
    def _update_device_stats(self, events, filtered_events):
        """MAJ stats par device"""
        for event in events:
            device = self._get_device_name(event)
            if device not in self.minute_device_stats:
                self.minute_device_stats[device] = {
                    'scanned': 0, 'threats': 0, 'duplicates': 0,
                    'tickets_created': 0, 'tickets_updated': 0,
                    'icon': self._get_device_icon(event)
                }
            self.minute_device_stats[device]['scanned'] += 1
        
        for event in filtered_events:
            device = self._get_device_name(event)
            if device in self.minute_device_stats:
                self.minute_device_stats[device]['threats'] += 1
    
    def _update_ticket_stats(self, device, created=False, updated=False, duplicate=False):
        """MAJ stats tickets par device"""
        if device in self.minute_device_stats:
            if created:
                self.minute_device_stats[device]['tickets_created'] += 1
            if updated:
                self.minute_device_stats[device]['tickets_updated'] += 1
            if duplicate:
                self.minute_device_stats[device]['duplicates'] += 1
    
    def _get_device_name(self, event):
        """Nom du device"""
        if event.get('_device_name'):
            return event['_device_name']
        
        device_ip = event.get('_device_ip', '')
        
        device_map = {
            '192.168.10.254': 'Stormshield',
            '192.168.10.11': 'Borne WiFi',
            '192.168.10.15': 'Switch Principal',
            '192.168.10.16': 'Switch Secondaire',
            '192.168.10.10': 'Serveur AD',
            '192.168.10.110': 'Serveur IA',
        }
        
        return device_map.get(device_ip, 'Autres')
    
    def _get_device_icon(self, event):
        """Icône du device"""
        device_name = self._get_device_name(event)
        
        icons = {
            'Stormshield': '🔥',
            'Borne WiFi': '📡',
            'Switch Principal': '🔌',
            'Switch Secondaire': '🔌',
            'Serveur AD': '🖥️',
            'Serveur IA': '🤖',
            'Autres': '❓'
        }
        
        return icons.get(device_name, '📟')
    
    def _monitor_loop(self, log_callback, status_callback):
        """
        🔥 BOUCLE SURVEILLANCE - ERREURS INSTANTANÉES
        
        - Affiche IMMÉDIATEMENT chaque erreur détectée
        - Rapport périodique TOUJOURS à 60 secondes
        """
        log_callback("\n🔄 SURVEILLANCE CONTINUE ACTIVÉE", "success")
        log_callback(f"📊 Compte-rendu toutes les {self.REPORT_INTERVAL_SECONDS} secondes\n", "info")
        
        while self.monitoring:
            try:
                if not self.monitoring:
                    break
                
                cycle_start = datetime.now()
                now_str = cycle_start.strftime("%Y-%m-%d %H:%M:%S")
                status_callback(now_str)
                
                # Reset stats ticket_manager
                if self.ticket_manager:
                    self.ticket_manager.reset_stats()
                
                # Lecture événements
                events = self.log_reader.read_new_events()
                
                if not self.monitoring:
                    break
                
                self.total_events_scanned += len(events)
                self.minute_events_scanned += len(events)
                
                if events:
                    # Filtrage
                    filtered_events = self.event_filter.filter_events(
                        events, 
                        enable_online_check=False
                    )
                    
                    if not self.monitoring:
                        break
                    
                    # MAJ stats
                    self._update_device_stats(events, filtered_events)
                    
                    if filtered_events:
                        self.total_threats_detected += len(filtered_events)
                        self.minute_threats_detected += len(filtered_events)
                        
                        # 🔥 AFFICHAGE IMMÉDIAT DES MENACES
                        log_callback(
                            f"\n⚠️ {len(filtered_events)} MENACE(S) DÉTECTÉE(S) ! ({now_str})",
                            "warning"
                        )
                        log_callback(f"{'='*80}", "warning")
                        
                        for i, event in enumerate(filtered_events, 1):
                            if not self.monitoring:
                                break
                            
                            device = self._get_device_name(event)
                            icon = self._get_device_icon(event)
                            priority = event.get('_priority', 0)
                            severity = event.get('_severity', 'unknown').upper()
                            
                            emoji = "🔴" if priority >= 7 else "🟡"
                            
                            # 🔥 AFFICHAGE IMMÉDIAT
                            log_callback(
                                f"\n{emoji} TRAITEMENT [{i}/{len(filtered_events)}]",
                                "warning"
                            )
                            log_callback(f"   Appareil : {icon} {device}", "info")
                            log_callback(f"   Event ID : {event['event_id']}", "info")
                            log_callback(f"   Severity : {severity}", "info")
                            log_callback(f"   Priorité : {priority}/10", "info")
                            
                            msg_short = event.get('message', '')[:100]
                            log_callback(f"   Message  : {msg_short}...", "info")
                            
                            analysis_start = time.time()
                            
                            # Traitement
                            try:
                                result = self.analyzer_callback(event)
                                
                                if isinstance(result, tuple) and len(result) == 2:
                                    success, is_new = result
                                else:
                                    success = bool(result)
                                    is_new = True
                                
                            except Exception as e:
                                # 🔥 ERREUR AFFICHÉE IMMÉDIATEMENT
                                log_callback(f"   ❌ Erreur analyse: {e}", "error")
                                success = False
                                is_new = False
                            
                            analysis_duration = time.time() - analysis_start
                            
                            # Résultat
                            if success:
                                if is_new:
                                    self.total_tickets_created += 1
                                    self.minute_tickets_created += 1
                                    self._update_ticket_stats(device, created=True)
                                    log_callback(
                                        f"   ✅ Ticket créé ({analysis_duration:.1f}s)",
                                        "success"
                                    )
                                else:
                                    self.minute_tickets_updated += 1
                                    self._update_ticket_stats(device, updated=True)
                                    log_callback(
                                        f"   📝 Ticket mis à jour ({analysis_duration:.1f}s)",
                                        "success"
                                    )
                            else:
                                # 🔥 DOUBLON DÉTECTÉ
                                self.minute_duplicates += 1
                                self.total_duplicates += 1
                                self._update_ticket_stats(device, duplicate=True)
                                # Pas de log pour doublons (compte-rendu uniquement)
                            
                            log_callback(f"   {'-'*80}", "info")
                        
                        # Refresh GUI
                        if self.monitoring:
                            self.refresh_callback()
                
                # 🔥 VÉRIFIER SI 60 SECONDES ÉCOULÉES
                elapsed = (datetime.now() - self.last_report_time).total_seconds()
                
                if elapsed >= self.REPORT_INTERVAL_SECONDS:
                    self._show_periodic_report(log_callback)
                
                # Attente polling
                for _ in range(self.polling_interval):
                    if not self.monitoring:
                        break
                    time.sleep(1)
                
            except Exception as e:
                if self.monitoring:
                    # 🔥 ERREUR AFFICHÉE IMMÉDIATEMENT
                    log_callback(f"❌ Erreur surveillance : {e}", "error")
                    time.sleep(self.polling_interval)
                else:
                    break
        
        log_callback("\n🛑 Surveillance arrêtée proprement", "info")


class InitialCheckThread:
    """ANALYSE INITIALE - X heures"""
    
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
        self.running = False
        if self.ai_analyzer:
            self.ai_analyzer.request_stop()
    
    def _check_loop(self, log_callback):
        """
        🔥 ANALYSE INITIALE - ERREURS INSTANTANÉES
        """
        try:
            if self.ticket_manager:
                self.ticket_manager.reset_stats()
            
            log_callback(f"📖 Lecture des {self.check_hours}h...", "info")
            
            events = self.log_reader.read_initial_check(hours=self.check_hours)
            
            if not self.running:
                log_callback("🛑 Analyse annulée", "warning")
                return
            
            if events:
                log_callback(f"\n📋 {len(events)} événements détectés", "info")
                
                log_callback("🔍 Filtrage...", "info")
                filtered_events = self.event_filter.filter_events(
                    events, 
                    enable_online_check=True
                )
                
                if not self.running:
                    log_callback("🛑 Analyse annulée", "warning")
                    return
                
                if filtered_events:
                    log_callback(
                        f"\n⚠️ {len(filtered_events)} menaces à analyser",
                        "warning"
                    )
                    log_callback(f"{'='*80}\n", "warning")
                    
                    for i, event in enumerate(filtered_events, 1):
                        if not self.running:
                            log_callback(
                                f"\n🛑 Interrompu à {i}/{len(filtered_events)}",
                                "warning"
                            )
                            break
                        
                        device_name = event.get('_device_name', 'Unknown')
                        device_ip = event.get('_device_ip', '')
                        source_display = f"{device_name} ({device_ip})" if device_ip else device_name
                        
                        priority = event.get('_priority', 0)
                        severity = event.get('_severity', 'unknown').upper()
                        emoji = "🔴" if priority >= 7 else "🟡"
                        
                        # 🔥 AFFICHAGE IMMÉDIAT
                        log_callback(
                            f"\n{emoji} ANALYSE [{i}/{len(filtered_events)}]",
                            "warning"
                        )
                        log_callback(f"   Source   : {source_display}", "info")
                        log_callback(f"   Event ID : {event['event_id']}", "info")
                        log_callback(f"   Severity : {severity}", "info")
                        log_callback(f"   Priorité : {priority}/10", "info")
                        
                        analysis_start = time.time()
                        
                        try:
                            result = self.analyzer_callback(event)
                            
                            if isinstance(result, tuple) and len(result) == 2:
                                success, is_new = result
                            else:
                                success = bool(result)
                                is_new = True
                        except Exception as e:
                            # 🔥 ERREUR AFFICHÉE IMMÉDIATEMENT
                            log_callback(f"   ❌ Erreur: {e}", "error")
                            success = False
                            is_new = False
                        
                        analysis_duration = time.time() - analysis_start
                        
                        # Résultat
                        if success:
                            status = "créé" if is_new else "mis à jour"
                            log_callback(
                                f"   ✅ Ticket {status} ({analysis_duration:.1f}s)",
                                "success"
                            )
                        # Doublons : pas de log
                    
                    # Stats finales
                    if self.running and self.ticket_manager:
                        stats = self.ticket_manager.get_stats()
                        
                        log_callback(f"\n📊 STATS FINALES :", "success")
                        log_callback(
                            f"   • Événements bruts : {len(events)}",
                            "info"
                        )
                        log_callback(
                            f"   • Filtrés : {len(filtered_events)}",
                            "info"
                        )
                        
                        if stats['duplicates_ignored'] > 0:
                            log_callback(
                                f"   🔄 Doublons ignorés (<10 min) : {stats['duplicates_ignored']}",
                                "info"
                            )
                        
                        log_callback(
                            f"   • Nouveaux tickets : {stats['created']}",
                            "success"
                        )
                        log_callback(
                            f"   • MAJ : {stats['updated']}",
                            "success"
                        )
                        log_callback(
                            f"   • TOTAL : {stats['total']}\n",
                            "success"
                        )
                        
                        self.refresh_callback()
                else:
                    log_callback(
                        f"\n✅ Aucun critique après filtrage\n",
                        "success"
                    )
            else:
                log_callback("\n✅ Aucune menace\n", "success")
                
        except Exception as e:
            if self.running:
                # 🔥 ERREUR AFFICHÉE IMMÉDIATEMENT
                log_callback(f"❌ Erreur : {e}", "error")
        finally:
            self.running = False