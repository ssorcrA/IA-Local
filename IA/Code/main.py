"""
Application principale - IMPORTS MIS À JOUR
Fichier : main.py - VERSION RESTRUCTURÉE

✅ IMPORTS ADAPTÉS À LA NOUVELLE STRUCTURE
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
import json
import threading
import time
from datetime import datetime

# === Configuration ===
from config import (
    OUTPUT_DIR, HISTORY_FILE, POLLING_INTERVAL, INITIAL_CHECK_HOURS,
    ensure_directories, validate_config, APP_VERSION, APP_NAME
)

# === Core ===
from core.unified_log_reader import UnifiedLogReader
from core.event_filter import EventFilter
from core.device_detector import DeviceDetector

# === AI ===
from ai.enhanced_ai_analyzer import EnhancedAIAnalyzer
from ai.web_searcher import WebSearcher

# === Tickets ===
from tickets.ticket_manager import TicketManager
from tickets.ticket_operations import TicketOperations

# === GUI ===
from gui.theme_manager import ThemeManager
from gui.gui_components import StatusBar, ControlPanel, Footer
from gui.console_manager import ConsoleManager, AIConsoleManager
from gui.ticket_tree_view import TicketTreeView
from gui.tab_creators import TabCreators

# === Utils ===
from utils.monitoring_thread import MonitoringThread, InitialCheckThread


class UnifiedMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("1400x900")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.monitoring = False
        self.quick_check_running = False
        self.full_check_running = False
        
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
            self.monitor_thread.set_ai_analyzer(self.ai_analyzer)
            self.monitor_thread.set_ticket_manager(self.ticket_manager)
            
            self.quick_check_thread = None
            
            self.full_check_thread = InitialCheckThread(
                self.log_reader, self.event_filter,
                self.analyze_and_create_ticket, self.load_tickets,
                INITIAL_CHECK_HOURS
            )
            self.full_check_thread.set_ai_analyzer(self.ai_analyzer)
            self.full_check_thread.set_ticket_manager(self.ticket_manager)
            
            self.ticket_ops = TicketOperations(
                self.ticket_tree_view, OUTPUT_DIR, self.detail_text,
                self.log_message, self.notebook, self.root
            )
            
            self.load_history()
            self.check_requirements()
            self.start_ticket_refresh_thread()
            
        except Exception as e:
            self.log_message(f"❌ Erreur d'initialisation: {e}", "error")
    
    def start_ticket_refresh_thread(self):
        def refresh_loop():
            while True:
                time.sleep(300)
                try:
                    self.root.after(0, self.silent_refresh_tickets)
                except:
                    pass
        
        refresh_thread = threading.Thread(target=refresh_loop, daemon=True)
        refresh_thread.start()
    
    def silent_refresh_tickets(self):
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
            'quick_check': self.quick_check,
            'initial_check': self.initial_check,
            'stop_check': self.stop_any_check,
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
        except:
            pass
    
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
        except:
            pass
    
    def check_requirements(self):
        self.log_message("="*80, "info")
        self.log_message(f"✅ {APP_NAME} v{APP_VERSION} - Système prêt", "success")
        self.log_message("="*80 + "\n", "info")
        
        try:
            self.log_reader.check_availability()
            self.ai_analyzer.check_ollama_endpoints()
        except:
            pass
    
    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.current_theme = ThemeManager.DARK_THEME if self.dark_mode else ThemeManager.LIGHT_THEME
        ThemeManager.save_preference(self.dark_mode)
        self.apply_theme()
        theme_icon = "🌙" if not self.dark_mode else "☀️"
        self.theme_btn.config(text=f"{theme_icon} Thème")
    
    def start_monitoring(self):
        if self.quick_check_running or self.full_check_running:
            messagebox.showwarning("Analyse en cours", 
                "Attendez la fin de l'analyse en cours avant de démarrer la surveillance")
            return
        
        self.monitoring = True
        self.control_panel.set_monitoring_state(True)
        self.status_bar.update_status("🟢 Surveillance active", '#27ae60')
        
        self.log_message(f"\n🚀 SURVEILLANCE DÉMARRÉE\n", "success")
        
        self.monitor_thread.start(
            self.log_message,
            lambda t: self.status_bar.update_last_check(t),
            self.ai_analyzer
        )
    
    def stop_monitoring(self):
        self.log_message("\n🛑 ARRÊT DE LA SURVEILLANCE...", "warning")
        
        self.monitoring = False
        self.monitor_thread.stop()
        
        self.control_panel.set_monitoring_state(False)
        self.status_bar.update_status("⚫ Inactif", '#95a5a6')
        
        self.save_history()
        self.log_message("✅ Surveillance arrêtée proprement\n", "success")
    
    def quick_check(self):
        if self.monitoring:
            messagebox.showwarning("Surveillance active", 
                "Arrêtez d'abord la surveillance continue")
            return
        
        if self.quick_check_running or self.full_check_running:
            messagebox.showwarning("En cours", "Une vérification est déjà en cours")
            return
        
        hours = 2
        
        self.log_message("\n" + "=" * 80, "warning")
        self.log_message(f"🔍 TEST RAPIDE - Fenêtre de {hours} heures", "warning")
        self.log_message("=" * 80, "warning")
        
        self.quick_check_running = True
        self.control_panel.set_check_state(True)
        self.control_panel.start_btn.config(state='disabled')
        
        self.quick_check_thread = InitialCheckThread(
            self.log_reader, self.event_filter,
            self.analyze_and_create_ticket, self.load_tickets,
            hours
        )
        self.quick_check_thread.set_ai_analyzer(self.ai_analyzer)
        self.quick_check_thread.set_ticket_manager(self.ticket_manager)
        
        self.quick_check_thread.start(self.log_message, self.ai_analyzer)
        
        def wait_for_completion():
            while self.quick_check_thread.running:
                time.sleep(1)
            self.root.after(0, self._on_quick_check_complete)
        
        wait_thread = threading.Thread(target=wait_for_completion, daemon=True)
        wait_thread.start()
    
    def _on_quick_check_complete(self):
        self.quick_check_running = False
        self.control_panel.set_check_state(False)
        self.control_panel.start_btn.config(state='normal')
        self.log_message("\n✅ Test rapide terminé\n", "success")
    
    def initial_check(self):
        if self.monitoring:
            messagebox.showwarning("Surveillance active", 
                "Arrêtez d'abord la surveillance continue")
            return
        
        if self.quick_check_running or self.full_check_running:
            messagebox.showwarning("En cours", "Une vérification est déjà en cours")
            return
        
        response = messagebox.askyesno(
            "Analyse 24h", 
            "⚠️ ATTENTION ⚠️\n\n"
            "Cette analyse va scanner les 24 dernières heures.\n"
            "Cela peut générer BEAUCOUP d'événements à traiter.\n\n"
            "Recommandation : Utilisez d'abord '🔍 Test 2h'\n\n"
            "Voulez-vous continuer ?",
            icon='warning'
        )
        
        if not response:
            return
        
        self.log_message("\n" + "=" * 80, "warning")
        self.log_message(f"📅 ANALYSE COMPLÈTE - Fenêtre de 24 heures", "warning")
        self.log_message("=" * 80, "warning")
        
        self.full_check_running = True
        self.control_panel.set_check_state(True)
        self.control_panel.start_btn.config(state='disabled')
        
        self.full_check_thread.start(self.log_message, self.ai_analyzer)
        
        def wait_for_completion():
            while self.full_check_thread.running:
                time.sleep(1)
            self.root.after(0, self._on_full_check_complete)
        
        wait_thread = threading.Thread(target=wait_for_completion, daemon=True)
        wait_thread.start()
    
    def _on_full_check_complete(self):
        self.full_check_running = False
        self.control_panel.set_check_state(False)
        self.control_panel.start_btn.config(state='normal')
        self.log_message("\n✅ Analyse complète terminée\n", "success")
    
    def stop_any_check(self):
        self.log_message("\n🛑 ARRÊT DE LA VÉRIFICATION...", "warning")
        
        if self.quick_check_running and self.quick_check_thread:
            self.quick_check_thread.stop()
            self.quick_check_running = False
        
        if self.full_check_running:
            self.full_check_thread.stop()
            self.full_check_running = False
        
        self.control_panel.set_check_state(False)
        self.control_panel.start_btn.config(state='normal')
        
        self.log_message("✅ Vérification arrêtée proprement\n", "success")
    
    def analyze_and_create_ticket(self, event):
        """
        🔥 TRAITEMENT AVEC VÉRIFICATION DOUBLON 10 MIN
        
        ✅ ORDRE D'EXÉCUTION :
        1. ⚠️ VÉRIFIER DOUBLON (<10 min) → RETOUR IMMÉDIAT
        2. Recherche web
        3. Analyse IA
        4. Création/MAJ ticket
        
        Returns:
            (success: bool, is_new: bool)
        """
        try:
            if not self.monitoring and not self.quick_check_running and not self.full_check_running:
                return False, False
        
            if self.ai_analyzer.stop_requested:
                return False, False
        
            # ✅ VÉRIFIER DOUBLON
            if self.ticket_manager.is_duplicate_within_timewindow(event):
                return False, False
        
            # Recherche web
            web_results = self.web_searcher.search(event)
        
            if not self.monitoring and not self.quick_check_running and not self.full_check_running:
                return False, False
        
            # Analyse IA
            analysis = self.ai_analyzer.analyze(event, web_results)
        
            if not self.monitoring and not self.quick_check_running and not self.full_check_running:
                return False, False
        
            if self.ai_analyzer.stop_requested:
                return False, False
        
            # Extraction liens
            web_links = []
            if web_results:
                import re
                for match in re.finditer(r'🔗 (https?://[^\s]+)', web_results):
                    web_links.append(match.group(1))
        
            # Création/MAJ ticket
            success, is_new = self.ticket_manager.create_or_update_ticket(
                event, analysis, web_links, 
                lambda msg: self.log_message(msg, "success")
            )
        
            return success, is_new
        
        except Exception as e:
            self.log_message(f"  ❌ Erreur analyse: {e}", "error")
            return False, False
    
    def load_tickets(self):
        total, today = self.ticket_tree_view.load_tickets()
        self.footer.update_stats(total, today)
        self.log_message(f"✅ {total} ticket(s) chargés", "success")
    
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
                self.log_message(f"🗑️ {cleaned} incident(s) supprimés", "success")
                self.refresh_tickets()
            else:
                self.log_message("✅ Aucun incident à supprimer", "info")
    
    def on_closing(self):
        if self.monitoring or self.quick_check_running or self.full_check_running:
            if messagebox.askokcancel("Fermeture", "Des opérations sont en cours. Voulez-vous vraiment quitter ?"):
                if self.monitoring:
                    self.monitor_thread.stop()
                if self.quick_check_running and self.quick_check_thread:
                    self.quick_check_thread.stop()
                if self.full_check_running:
                    self.full_check_thread.stop()
                
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