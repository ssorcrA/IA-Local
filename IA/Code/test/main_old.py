"""
Application principale avec toutes les corrections
Fichier : main.py - VERSION FINALE
CORRECTIFS:
- Arrêt immédiat de l'IA
- Pas de doublons Syslog
- Logs cachés en surveillance
- Sauvegarde état
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
import json
from datetime import datetime

from config import (
    OUTPUT_DIR, HISTORY_FILE, POLLING_INTERVAL, INITIAL_CHECK_HOURS,
    ensure_directories, validate_config, APP_VERSION, APP_NAME
)
from unified_log_reader import UnifiedLogReader
from enhanced_ai_analyzer import EnhancedAIAnalyzer
from web_searcher import WebSearcher
from ticket_manager import TicketManager
from event_filter import EventFilter
from theme_manager import ThemeManager

from gui_components import StatusBar, ControlPanel, Footer
from console_manager import ConsoleManager, AIConsoleManager
from ticket_tree_view import TicketTreeView
from monitoring_thread import MonitoringThread, InitialCheckThread
from tab_creators import TabCreators
from ticket_operations import TicketOperations


class UnifiedMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("1400x900")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.monitoring = False
        self.initial_check_running = False
        self.dark_mode = ThemeManager.load_preference()
        self.current_theme = ThemeManager.DARK_THEME if self.dark_mode else ThemeManager.LIGHT_THEME
        self.current_ticket_path = None
        
        ensure_directories()
        self.apply_theme()
        self.create_widgets()
        self.init_components()
    
    def init_components(self):
        try:
            self.log_reader = UnifiedLogReader(log_callback=self.log_message)
            self.ai_analyzer = EnhancedAIAnalyzer(log_callback=self.log_ai_message)
            self.web_searcher = WebSearcher(log_callback=self.log_message)
            self.ticket_manager = TicketManager(OUTPUT_DIR)
            self.event_filter = EventFilter(log_callback=self.log_message)
            
            self.monitor_thread = MonitoringThread(
                self.log_reader, self.event_filter,
                self.analyze_and_create_ticket, self.refresh_tickets,
                POLLING_INTERVAL
            )
            # IMPORTANT: Passer la référence à l'analyseur IA
            self.monitor_thread.set_ai_analyzer(self.ai_analyzer)
            
            self.initial_check_thread = InitialCheckThread(
                self.log_reader, self.event_filter,
                self.analyze_and_create_ticket, self.refresh_tickets,
                INITIAL_CHECK_HOURS
            )
            # IMPORTANT: Passer la référence à l'analyseur IA
            self.initial_check_thread.set_ai_analyzer(self.ai_analyzer)
            
            self.ticket_ops = TicketOperations(
                self.ticket_tree_view, OUTPUT_DIR, self.detail_text,
                self.log_message, self.notebook, self.root
            )
            
            self.load_history()
            self.check_requirements()
            
            # Démarrer le thread de vérification périodique des tickets
            self.start_ticket_refresh_thread()
            
        except Exception as e:
            self.log_message(f"Erreur d'initialisation: {e}", "error")
    
    def start_ticket_refresh_thread(self):
        """Thread qui rafraîchit les tickets toutes les 5 minutes"""
        import threading
        import time
        
        def refresh_loop():
            while True:
                time.sleep(300)  # 5 minutes
                
                try:
                    # Rafraîchir la vue (dans le thread principal)
                    self.root.after(0, self.silent_refresh_tickets)
                except:
                    pass
        
        refresh_thread = threading.Thread(target=refresh_loop, daemon=True)
        refresh_thread.start()
    
    def silent_refresh_tickets(self):
        """Rafraîchit les tickets sans message dans la console"""
        try:
            total, today = self.ticket_tree_view.load_tickets()
            self.footer.update_stats(total, today)
        except:
            pass
    
    def apply_theme(self):
        style = ttk.Style()
        style.theme_use('clam')
        theme = self.current_theme
        
        self.root.configure(bg=theme['bg_main'])
        
        style.configure('Main.TFrame', background=theme['bg_main'])
        style.configure('Card.TFrame', background=theme['bg_card'], relief='flat')
        style.configure('Header.TFrame', background=theme['bg_header'])
        
        style.configure('Header.TLabel', 
                       background=theme['bg_header'], 
                       foreground=theme['fg_header'], 
                       font=('Segoe UI', 16, 'bold'))
        style.configure('Title.TLabel', 
                       background=theme['bg_card'], 
                       foreground=theme['fg_main'], 
                       font=('Segoe UI', 11, 'bold'))
        style.configure('Normal.TLabel', 
                       background=theme['bg_card'], 
                       foreground=theme['fg_main'], 
                       font=('Segoe UI', 10))
        
        style.configure('Treeview', 
                       background=theme['tree_bg'], 
                       foreground=theme['tree_fg'], 
                       fieldbackground=theme['tree_bg'],
                       font=('Segoe UI', 9))
        style.configure('Treeview.Heading', 
                       background=theme['tree_heading_bg'], 
                       foreground=theme['tree_heading_fg'], 
                       font=('Segoe UI', 10, 'bold'))
    
    def create_widgets(self):
        self.create_header()
        
        self.status_bar = StatusBar(self.root, self.current_theme)
        
        self.control_panel = ControlPanel(self.root, {
            'start': self.start_monitoring,
            'stop': self.stop_monitoring,
            'refresh': self.refresh_tickets,
            'initial_check': self.initial_check,
            'stop_check': self.stop_initial_check,
            'cleanup': self.cleanup_old_tickets
        })
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=30, pady=(0, 20))
        
        tab_creators = TabCreators(self.notebook, self.current_theme)
        self.console = tab_creators.create_monitor_tab()
        self.ai_console = tab_creators.create_ai_log_tab()
        self.ticket_tree_view, self.path_display, self.search_entry = tab_creators.create_history_tab(
            OUTPUT_DIR, self.log_message, self.on_ticket_select,
            self.open_ticket, self.show_tree_menu
        )
        self.detail_text = tab_creators.create_detail_tab(
            self.export_current_ticket, self.copy_ticket_content
        )
        
        self.console_manager = ConsoleManager(self.console, self.current_theme)
        self.ai_console_manager = AIConsoleManager(self.ai_console, self.current_theme)
        
        self.footer = Footer(self.root, self.current_theme, APP_VERSION)
        
        self.root.after(100, self.load_tickets)
    
    def create_header(self):
        header = ttk.Frame(self.root, style='Header.TFrame', height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        header_content = ttk.Frame(header, style='Header.TFrame')
        header_content.pack(fill='both', expand=True, padx=30, pady=20)
        
        title = ttk.Label(header_content, text=APP_NAME, style='Header.TLabel')
        title.pack(side='left')
        
        subtitle = ttk.Label(
            header_content, 
            text=f"v{APP_VERSION} - Multi-Sources", 
            font=('Segoe UI', 9), 
            foreground='#95a5a6',
            background=self.current_theme['bg_header']
        )
        subtitle.pack(side='left', padx=(10, 0))
        
        theme_icon = "🌙" if not self.dark_mode else "☀️"
        self.theme_btn = tk.Button(
            header_content,
            text=f"{theme_icon} Thème",
            command=self.toggle_theme,
            bg='#34495e', fg='white',
            font=('Segoe UI', 9),
            relief='flat', bd=0,
            padx=15, pady=8,
            cursor='hand2'
        )
        self.theme_btn.pack(side='right')
    
    def log_message(self, message, tag="info"):
        self.console_manager.log(message, tag)
    
    def log_ai_message(self, message, tag="ai_info"):
        self.ai_console_manager.log(message, tag)
    
    def load_history(self):
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    last_record = data.get('last_record', 0)
                    if hasattr(self.log_reader, 'event_reader'):
                        self.log_reader.event_reader.set_last_record_number(last_record)
        except Exception as e:
            self.log_message(f"Avertissement: Impossible de charger l'historique: {e}", "warning")
    
    def save_history(self):
        try:
            last_record = 0
            if hasattr(self.log_reader, 'event_reader'):
                last_record = self.log_reader.event_reader.get_last_record_number()
            
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'last_record': last_record,
                    'last_save': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            self.log_message(f"Avertissement: Impossible de sauvegarder l'historique: {e}", "warning")
    
    def check_requirements(self):
        self.log_message("=" * 80, "info")
        self.log_message(f"  {APP_NAME} v{APP_VERSION}", "success")
        self.log_message("  Système de détection des menaces multi-sources avec IA", "info")
        self.log_message("=" * 80, "info")
        
        issues = validate_config()
        if issues:
            self.log_message("\n⚠️ Avertissements configuration:", "warning")
            for issue in issues:
                self.log_message(f"  • {issue}", "warning")
        
        try:
            self.log_reader.check_availability()
            sources = self.log_reader.get_sources_summary()
            self.log_message("\n📊 SOURCES ACTIVES:", "success")
            for source in sources:
                self.log_message(f"  {source}", "success")
        except Exception as e:
            self.log_message(f"\n❌ Erreur vérification sources: {e}", "error")
        
        self.ai_analyzer.check_ollama_endpoints()
        self.log_message("\n✅ Système opérationnel - Prêt à surveiller\n", "success")
    
    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.current_theme = ThemeManager.DARK_THEME if self.dark_mode else ThemeManager.LIGHT_THEME
        ThemeManager.save_preference(self.dark_mode)
        self.apply_theme()
        theme_icon = "🌙" if not self.dark_mode else "☀️"
        self.theme_btn.config(text=f"{theme_icon} Thème")
    
    def start_monitoring(self):
        if self.initial_check_running:
            messagebox.showwarning("Analyse en cours", "Attendez la fin de l'analyse 24h")
            return
        
        self.monitoring = True
        self.control_panel.set_monitoring_state(True)
        self.status_bar.update_status("🟢 Surveillance active", '#27ae60')
        
        self.log_message(f"\n🚀 Surveillance multi-sources démarrée (intervalle: {POLLING_INTERVAL}s)", "success")
        
        # Passer l'analyseur IA au thread
        self.monitor_thread.start(
            self.log_message,
            lambda t: self.status_bar.update_last_check(t),
            self.ai_analyzer
        )
    
    def stop_monitoring(self):
        self.log_message("\n🛑 ARRÊT DE LA SURVEILLANCE...", "warning")
        self.log_message("   → Arrêt des threads en cours", "warning")
        self.log_message("   → Interruption des analyses IA", "warning")
        
        self.monitoring = False
        self.monitor_thread.stop()  # Ceci va aussi arrêter l'IA
        
        self.control_panel.set_monitoring_state(False)
        self.status_bar.update_status("⚫ Inactif", '#95a5a6')
        
        self.save_history()
        self.log_message("✅ Surveillance arrêtée proprement\n", "success")
    
    def initial_check(self):
        if self.initial_check_running:
            messagebox.showwarning("En cours", "Une vérification est déjà en cours")
            return
        
        if self.monitoring:
            messagebox.showwarning("Surveillance active", "Arrêtez d'abord la surveillance continue")
            return
        
        self.log_message("\n" + "=" * 80, "warning")
        self.log_message("📅 ANALYSE MULTI-SOURCES - Fenêtre de 24 heures", "warning")
        self.log_message("=" * 80, "warning")
        
        self.initial_check_running = True
        self.control_panel.set_check_state(True)
        self.control_panel.start_btn.config(state='disabled')
        
        # Passer l'analyseur IA au thread
        self.initial_check_thread.start(self.log_message, self.ai_analyzer)
    
    def stop_initial_check(self):
        self.log_message("\n🛑 ARRÊT DE LA VÉRIFICATION...", "warning")
        self.log_message("   → Arrêt des threads en cours", "warning")
        self.log_message("   → Interruption des analyses IA", "warning")
        
        self.initial_check_running = False
        self.initial_check_thread.stop()  # Ceci va aussi arrêter l'IA
        
        self.control_panel.set_check_state(False)
        self.control_panel.start_btn.config(state='normal')
        
        self.log_message("✅ Vérification arrêtée proprement\n", "success")
    
    def analyze_and_create_ticket(self, event):
     """
     Analyse un événement et crée un ticket
     CORRECTION: Ne pas interrompre pendant l'analyse IA
     """
     try:
        # ✅ NE VÉRIFIER L'ARRÊT QU'AU DÉBUT
        if not self.monitoring and not self.initial_check_running:
            self.log_message("  🛑 Analyse annulée (arrêt demandé)", "warning")
            return False
        
        # 1. Recherche web (rapide, peut être interrompue)
        self.log_message(f"  🌐 Recherche d'informations en ligne...", "info")
        web_results = self.web_searcher.search(event)
        
        # 2. Analyse IA (CRITIQUE: ne pas interrompre)
        self.log_message(f"  🤖 Analyse IA en cours...", "info")
        
        # ⚠️ IMPORTANT: Ne plus vérifier stop_requested pendant l'analyse
        # L'analyseur IA va maintenant terminer son analyse même si arrêt demandé
        analysis = self.ai_analyzer.analyze(event, web_results)
        
        # 3. Vérifier si on a obtenu une analyse
        if not analysis:
            self.log_message("  ⚠️ Aucune analyse IA obtenue", "warning")
            analysis = f"""🔍 ANALYSE AUTOMATIQUE:
            Erreur détectée mais aucune analyse IA disponible.

            Event ID: {event['event_id']}
            Source: {event['source']}
            Type: {event['event_type']}

        Recommandation: Vérifier les logs manuellement."""
        
        # 4. Extraire les liens web
        web_links = []
        if web_results:
            import re
            for match in re.finditer(r'🔗 (https?://[^\s]+)', web_results):
                web_links.append(match.group(1))
        
        # 5. Créer le ticket (TOUJOURS)
        self.log_message(f"  📝 Création du ticket...", "info")
        ticket_path = self.ticket_manager.create_or_update_ticket(
            event, analysis, web_links, 
            lambda msg: self.log_message(msg, "success")
        )
        
        if ticket_path:
            self.log_message(f"  ✅ Ticket créé: {os.path.basename(ticket_path)}", "success")
            return True
        else:
            self.log_message(f"  ⚠️ Échec création ticket", "warning")
            return False
        
     except Exception as e:
        self.log_message(f"  ❌ Erreur lors de l'analyse: {e}", "error")
        import traceback
        self.log_message(f"  Détails: {traceback.format_exc()}", "error")
        return False
    
    def load_tickets(self):
        total, today = self.ticket_tree_view.load_tickets()
        self.footer.update_stats(total, today)
        self.log_message(f"✅ {total} ticket(s) chargé(s)", "success")
    
    def refresh_tickets(self):
        self.log_message("🔄 Actualisation de la base de données...", "info")
        self.load_tickets()
        self.log_message("✅ Base de données actualisée\n", "success")
    
    def on_ticket_select(self, event=None):
        ticket_path = self.ticket_tree_view.get_selected_ticket_path()
        if ticket_path:
            self.current_ticket_path = ticket_path
            self.ticket_ops.update_path_display(ticket_path, self.path_display)
    
    def open_ticket(self, event=None):
        self.ticket_ops.open_ticket(self.current_ticket_path)
    
    def show_tree_menu(self, event):
        pass
    
    def export_current_ticket(self):
        self.ticket_ops.export_ticket(self.detail_text)
    
    def copy_ticket_content(self):
        self.ticket_ops.copy_content(self.detail_text)
    
    def cleanup_old_tickets(self):
        if messagebox.askyesno("Nettoyage", "Supprimer les incidents de plus de 30 jours ?"):
            cleaned = self.ticket_manager.cleanup_old_tickets()
            if cleaned:
                self.log_message(f"🗑 {cleaned} incident(s) supprimés", "success")
                self.refresh_tickets()
            else:
                self.log_message("✅ Aucun incident à supprimer", "info")
    
    def on_closing(self):
        if self.monitoring or self.initial_check_running:
            if messagebox.askokcancel("Fermeture", "Des opérations sont en cours. Voulez-vous vraiment quitter ?"):
                # Arrêter proprement
                if self.monitoring:
                    self.monitor_thread.stop()
                if self.initial_check_running:
                    self.initial_check_thread.stop()
                
                self.save_history()
                self.root.destroy()
        else:
            self.save_history()
            self.root.destroy()


def main():
    root = tk.Tk()
    
    try:
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except:
        pass
    
    app = UnifiedMonitorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()