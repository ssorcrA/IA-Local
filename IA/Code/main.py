"""
AD Log Monitor - Version Unifiée Multi-Sources
Fichier : main.py - VERSION 3.0
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
import json
import re
import threading
from datetime import datetime

from config import (
    OUTPUT_DIR, HISTORY_FILE, 
    POLLING_INTERVAL, INITIAL_CHECK_HOURS,
    ensure_directories, validate_config,
    APP_VERSION, APP_NAME
)
from unified_log_reader import UnifiedLogReader
from enhanced_ai_analyzer import EnhancedAIAnalyzer
from web_searcher import WebSearcher
from ticket_manager import TicketManager
from event_filter import EventFilter
from theme_manager import ThemeManager


class UnifiedMonitorGUI:
    """Interface graphique unifiée pour toutes les sources de logs"""
    
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("1400x900")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # État
        self.monitoring = False
        self.monitor_thread = None
        self.initial_check_running = False
        self.dark_mode = ThemeManager.load_preference()
        self.current_theme = ThemeManager.DARK_THEME if self.dark_mode else ThemeManager.LIGHT_THEME
        
        ensure_directories()
        self.apply_theme()
        self.create_widgets()
        
        try:
            # Initialisation des composants
            self.log_reader = UnifiedLogReader(log_callback=self.log_message)
            self.ai_analyzer = EnhancedAIAnalyzer(log_callback=self.log_message)
            self.web_searcher = WebSearcher(log_callback=self.log_message)
            self.ticket_manager = TicketManager(OUTPUT_DIR)
            self.event_filter = EventFilter(log_callback=self.log_message)
            
            self.load_history()
            self.check_requirements()
            
        except Exception as e:
            self.log_message(f"Erreur d'initialisation: {e}", "error")
    
    def apply_theme(self):
        """Applique le thème actuel"""
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
        style.configure('Status.TLabel', 
                       background=theme['bg_main'], 
                       foreground=theme['fg_secondary'], 
                       font=('Segoe UI', 9))
        
        style.configure('Treeview', 
                       background=theme['tree_bg'], 
                       foreground=theme['tree_fg'], 
                       fieldbackground=theme['tree_bg'],
                       font=('Segoe UI', 9),
                       borderwidth=0)
        style.configure('Treeview.Heading', 
                       background=theme['tree_heading_bg'], 
                       foreground=theme['tree_heading_fg'], 
                       font=('Segoe UI', 10, 'bold'),
                       relief='flat',
                       borderwidth=0)
        style.map('Treeview.Heading',
                 background=[('active', theme['tree_heading_bg'])])
        style.map('Treeview',
                 background=[('selected', theme['select_bg'])],
                 foreground=[('selected', theme['fg_main'])])
    
    def toggle_theme(self):
        """Bascule entre mode clair et sombre"""
        self.dark_mode = not self.dark_mode
        self.current_theme = ThemeManager.DARK_THEME if self.dark_mode else ThemeManager.LIGHT_THEME
        ThemeManager.save_preference(self.dark_mode)
        
        self.apply_theme()
        self.update_widget_colors()
        
        theme_icon = "🌙" if not self.dark_mode else "☀️"
        self.theme_btn.config(text=f"{theme_icon} Thème")
    
    def update_widget_colors(self):
        """Met à jour les couleurs de tous les widgets"""
        theme = self.current_theme
        
        self.console.config(bg=theme['console_bg'], fg=theme['console_fg'])
        self.search_entry.config(bg=theme['entry_bg'], fg=theme['entry_fg'])
        self.detail_text.config(bg=theme['console_bg'], fg=theme['console_fg'])
        self.status_label.config(background=theme['bg_main'])
        self.last_check_label.config(background=theme['bg_main'], foreground=theme['fg_secondary'])
        self.stats_label.config(background=theme['bg_main'], foreground=theme['fg_secondary'])
        self.version_label.config(background=theme['bg_main'], foreground=theme['fg_secondary'])
    
    def load_history(self):
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    last_record = data.get('last_record', 0)
                    # Le UnifiedLogReader gère maintenant cet état
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
        """Vérifie les prérequis et sources disponibles"""
        self.log_message("=" * 80, "info")
        self.log_message(f"  {APP_NAME} v{APP_VERSION}", "success")
        self.log_message("  Système de détection des menaces multi-sources avec IA", "info")
        self.log_message("=" * 80, "info")
        
        # Validation configuration
        issues = validate_config()
        if issues:
            self.log_message("\n⚠️  Avertissements configuration:", "warning")
            for issue in issues:
                self.log_message(f"  • {issue}", "warning")
        
        # Vérification des sources de logs
        try:
            self.log_reader.check_availability()
            
            # Afficher les sources disponibles
            sources = self.log_reader.get_sources_summary()
            self.log_message("\n📊 SOURCES ACTIVES:", "success")
            for source in sources:
                self.log_message(f"  {source}", "success")
        
        except Exception as e:
            self.log_message(f"\n❌ Erreur vérification sources: {e}", "error")
        
        # Vérification endpoints IA
        self.ai_analyzer.check_ollama_endpoints()
        
        self.log_message("\n✅ Système opérationnel - Prêt à surveiller\n", "success")
    
    def on_closing(self):
        if self.monitoring:
            if messagebox.askokcancel("Fermeture", "La surveillance est active. Voulez-vous vraiment quitter ?"):
                self.monitoring = False
                self.save_history()
                self.root.destroy()
        else:
            self.save_history()
            self.root.destroy()
    
    def create_widgets(self):
        """Création de l'interface"""
        theme = self.current_theme
        
        # En-tête
        header = ttk.Frame(self.root, style='Header.TFrame', height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        header_content = ttk.Frame(header, style='Header.TFrame')
        header_content.pack(fill='both', expand=True, padx=30, pady=20)
        
        title = ttk.Label(header_content, text=APP_NAME, style='Header.TLabel')
        title.pack(side='left')
        
        subtitle = ttk.Label(header_content, 
                            text=f"v{APP_VERSION} - Multi-Sources", 
                            font=('Segoe UI', 9), 
                            foreground='#95a5a6',
                            background=theme['bg_header'])
        subtitle.pack(side='left', padx=(10, 0))
        
        # Bouton thème
        theme_icon = "🌙" if not self.dark_mode else "☀️"
        self.theme_btn = tk.Button(header_content,
                                   text=f"{theme_icon} Thème",
                                   command=self.toggle_theme,
                                   bg='#34495e', fg='white',
                                   font=('Segoe UI', 9),
                                   relief='flat', bd=0,
                                   padx=15, pady=8,
                                   cursor='hand2',
                                   activebackground='#2c3e50')
        self.theme_btn.pack(side='right')
        
        # Barre d'état
        status_bar = ttk.Frame(self.root, style='Main.TFrame')
        status_bar.pack(fill='x', padx=30, pady=(20, 10))
        
        self.status_label = ttk.Label(status_bar, 
                                      text="● Inactif", 
                                      font=('Segoe UI', 10, 'bold'),
                                      foreground='#95a5a6',
                                      background=theme['bg_main'])
        self.status_label.pack(side='left')
        
        self.last_check_label = ttk.Label(status_bar, 
                                         text="Dernière vérification: Jamais",
                                         font=('Segoe UI', 9),
                                         foreground=theme['fg_secondary'],
                                         background=theme['bg_main'])
        self.last_check_label.pack(side='right')
        
        # Panneau de contrôle
        control_panel = ttk.Frame(self.root, style='Main.TFrame')
        control_panel.pack(fill='x', padx=30, pady=(0, 20))
        
        btn_config = {
            'font': ('Segoe UI', 10),
            'relief': 'flat', 'bd': 0,
            'padx': 20, 'pady': 10,
            'cursor': 'hand2'
        }
        
        self.start_btn = tk.Button(control_panel, 
                                   text="▶ Surveillance",
                                   command=self.start_monitoring,
                                   bg='#27ae60', fg='white',
                                   activebackground='#229954',
                                   **btn_config)
        self.start_btn.pack(side='left', padx=(0, 10))
        
        self.stop_btn = tk.Button(control_panel, 
                                  text="⏸ Arrêter",
                                  command=self.stop_monitoring,
                                  bg='#e74c3c', fg='white',
                                  state='disabled',
                                  activebackground='#c0392b',
                                  **btn_config)
        self.stop_btn.pack(side='left', padx=(0, 10))
        
        tk.Button(control_panel, 
                 text="🔄 Actualiser",
                 command=self.refresh_tickets,
                 bg='#3498db', fg='white',
                 activebackground='#2980b9',
                 **btn_config).pack(side='left', padx=(0, 10))
        
        tk.Button(control_panel, 
                 text="📅 Analyse 24h",
                 command=self.initial_check,
                 bg='#e67e22', fg='white',
                 activebackground='#d35400',
                 **btn_config).pack(side='left', padx=(0, 10))
        
        self.stop_check_btn = tk.Button(control_panel, 
                                        text="⏹ Arrêter vérif.",
                                        command=self.stop_initial_check,
                                        bg='#c0392b', fg='white',
                                        state='disabled',
                                        activebackground='#a93226',
                                        **btn_config)
        self.stop_check_btn.pack(side='left', padx=(0, 10))
        
        tk.Button(control_panel, 
                 text="🗑 Nettoyer",
                 command=self.cleanup_old_tickets,
                 bg='#95a5a6', fg='white',
                 activebackground='#7f8c8d',
                 **btn_config).pack(side='left')
        
        # Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=30, pady=(0, 20))
        
        self.create_monitor_tab()
        self.create_history_tab()
        self.create_detail_tab()
        
        # Pied de page
        footer = ttk.Frame(self.root, style='Main.TFrame')
        footer.pack(fill='x', padx=30, pady=(0, 20))
        
        self.stats_label = ttk.Label(footer, 
                                     text="Incidents: 0 | Aujourd'hui: 0 | Statut: Prêt",
                                     font=('Segoe UI', 9),
                                     foreground=theme['fg_secondary'],
                                     background=theme['bg_main'])
        self.stats_label.pack(side='left')
        
        self.version_label = ttk.Label(footer, 
                                      text=f"Version {APP_VERSION} | © 2025",
                                      font=('Segoe UI', 8),
                                      foreground=theme['fg_secondary'],
                                      background=theme['bg_main'])
        self.version_label.pack(side='right')
    
    def create_monitor_tab(self):
        theme = self.current_theme
        frame = ttk.Frame(self.notebook, style='Card.TFrame')
        self.notebook.add(frame, text="  Console  ")
        
        card = ttk.Frame(frame, style='Card.TFrame')
        card.pack(fill='both', expand=True, padx=20, pady=20)
        
        title_label = ttk.Label(card, text="Console multi-sources", style='Title.TLabel')
        title_label.pack(anchor='w', pady=(0, 10))
        
        self.console = scrolledtext.ScrolledText(card, wrap=tk.WORD, height=28,
                                                bg=theme['console_bg'], 
                                                fg=theme['console_fg'],
                                                font=('Consolas', 9),
                                                relief='solid', bd=1,
                                                insertbackground='#3498db',
                                                selectbackground=theme['select_bg'])
        self.console.pack(fill='both', expand=True)
        
        self.console.tag_config("error", foreground="#e74c3c", font=('Consolas', 9, 'bold'))
        self.console.tag_config("warning", foreground="#e67e22", font=('Consolas', 9, 'bold'))
        self.console.tag_config("success", foreground="#27ae60", font=('Consolas', 9, 'bold'))
        self.console.tag_config("info", foreground="#3498db")
    
    def create_history_tab(self):
        theme = self.current_theme
        frame = ttk.Frame(self.notebook, style='Card.TFrame')
        self.notebook.add(frame, text="  Base de données  ")
        
        card = ttk.Frame(frame, style='Card.TFrame')
        card.pack(fill='both', expand=True, padx=20, pady=20)
        
        search_frame = ttk.Frame(card, style='Card.TFrame')
        search_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Label(search_frame, text="🔍 Rechercher:", style='Normal.TLabel').pack(side='left', padx=(0, 10))
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=60,
                                     bg=theme['entry_bg'], fg=theme['entry_fg'],
                                     font=('Segoe UI', 10),
                                     relief='solid', bd=1,
                                     insertbackground='#3498db')
        self.search_entry.pack(side='left', fill='x', expand=True)
        self.search_entry.bind('<KeyRelease>', lambda e: self.filter_tickets())
        
        list_frame = ttk.Frame(card, style='Card.TFrame')
        list_frame.pack(fill='both', expand=True)
        
        cols = ('Date', 'Type', 'Source', 'Event ID', 'Ordinateur', 'Occurrences')
        self.ticket_tree = ttk.Treeview(list_frame, columns=cols, show='tree headings', height=25)
        
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.ticket_tree.yview)
        hsb = ttk.Scrollbar(list_frame, orient="horizontal", command=self.ticket_tree.xview)
        self.ticket_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.ticket_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        self.ticket_tree.heading('#0', text='Incident')
        self.ticket_tree.column('#0', width=250)
        
        for col in cols:
            self.ticket_tree.heading(col, text=col)
            self.ticket_tree.column(col, width=120)
        
        self.ticket_tree.bind('<Double-1>', self.open_ticket)
        self.root.after(100, self.load_tickets)
    
    def create_detail_tab(self):
        theme = self.current_theme
        frame = ttk.Frame(self.notebook, style='Card.TFrame')
        self.notebook.add(frame, text="  Détails  ")
        
        card = ttk.Frame(frame, style='Card.TFrame')
        card.pack(fill='both', expand=True, padx=20, pady=20)
        
        title_label = ttk.Label(card, text="Rapport d'incident détaillé", style='Title.TLabel')
        title_label.pack(anchor='w', pady=(0, 10))
        
        self.detail_text = scrolledtext.ScrolledText(card, wrap=tk.WORD,
                                                     bg=theme['console_bg'], 
                                                     fg=theme['console_fg'],
                                                     font=('Consolas', 10),
                                                     relief='solid', bd=1)
        self.detail_text.pack(fill='both', expand=True)
        self.detail_text.insert('1.0', 
                               "Double-cliquez sur un incident dans 'Base de données' "
                               "pour afficher le rapport complet.")
    
    def log_message(self, message, tag="info"):
        """Affiche un message dans la console"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.console.insert(tk.END, f"[{timestamp}] {message}\n", tag)
            self.console.see(tk.END)
            self.root.update_idletasks()
        except:
            print(message)
    
    def analyze_and_create_ticket(self, event):
        try:
            web_results = self.web_searcher.search(event)
            analysis = self.ai_analyzer.analyze(event, web_results)
            
            web_links = []
            if web_results:
                for match in re.finditer(r'🔗 (https?://[^\s]+)', web_results):
                    web_links.append(match.group(1))
            
            self.ticket_manager.create_or_update_ticket(event, analysis, web_links, 
                                                       lambda msg: self.log_message(msg, "success"))
            
        except Exception as e:
            self.log_message(f"  Erreur lors de l'analyse: {e}", "error")
    
    def initial_check(self):
        if self.initial_check_running:
            messagebox.showwarning("En cours", "Une vérification est déjà en cours")
            return
        
        self.log_message("\n" + "=" * 80, "warning")
        self.log_message("🔍 ANALYSE MULTI-SOURCES - Fenêtre de 24 heures", "warning")
        self.log_message("=" * 80, "warning")
        
        self.initial_check_running = True
        self.stop_check_btn.config(state='normal')
        
        thread = threading.Thread(target=self._initial_check_thread, daemon=True)
        thread.start()
    
    def stop_initial_check(self):
        if self.initial_check_running:
            self.initial_check_running = False
            self.stop_check_btn.config(state='disabled')
            self.log_message("\n⏹ Vérification arrêtée par l'utilisateur\n", "warning")
    
    def _initial_check_thread(self):
        try:
            events = self.log_reader.read_initial_check(hours=INITIAL_CHECK_HOURS)
            
            if not self.initial_check_running:
                self.log_message("Vérification annulée", "warning")
                return
            
            if events:
                self.log_message(f"\n📋 {len(events)} événements bruts détectés", "info")
                
                filtered_events = self.event_filter.filter_events(events, enable_online_check=True)
                
                if not self.initial_check_running:
                    return
                
                if filtered_events:
                    self.log_message(f"\n⚠️ {len(filtered_events)} menaces à analyser\n", "warning")
                    
                    for i, event in enumerate(filtered_events, 1):
                        if not self.initial_check_running:
                            break
                        
                        self.log_message(f"[{i}/{len(filtered_events)}] Analyse: {event['source']} - Event {event['event_id']}", "warning")
                        self.analyze_and_create_ticket(event)
                    
                    self.save_history()
                    self.root.after(0, self.refresh_tickets)
                    
                    if self.initial_check_running:
                        self.log_message(f"\n✅ Analyse terminée: {len(filtered_events)} incident(s)\n", "success")
                else:
                    self.log_message(f"\n✅ Aucun événement critique après filtrage\n", "success")
            else:
                self.log_message("\n✅ Aucune menace détectée\n", "success")
                
        except Exception as e:
            self.log_message(f"Erreur lors de l'analyse: {e}", "error")
        finally:
            self.initial_check_running = False
            self.root.after(0, lambda: self.stop_check_btn.config(state='disabled'))
    
    def start_monitoring(self):
        self.monitoring = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.status_label.config(text="● Surveillance active", foreground='#27ae60')
        
        self.log_message(f"\nSurveillance multi-sources démarrée (intervalle: {POLLING_INTERVAL}s)", "success")
        self.log_message("Détection en temps réel sur toutes les sources disponibles\n", "success")
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        self.monitoring = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_label.config(text="● Inactif", foreground='#95a5a6')
        self.save_history()
        self.log_message("\nSurveillance arrêtée\n", "warning")
    
    def _monitor_loop(self):
        while self.monitoring:
            try:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.root.after(0, lambda t=now: self.last_check_label.config(text=f"Dernière vérification: {t}"))
                
                self.log_message("Vérification en cours sur toutes les sources...", "info")
                events = self.log_reader.read_new_events()
                
                if events:
                    filtered_events = self.event_filter.filter_events(events, enable_online_check=False)
                    
                    if filtered_events:
                        self.log_message(f"\n⚠️ {len(filtered_events)} nouvelle(s) menace(s)!", "warning")
                        for i, event in enumerate(filtered_events, 1):
                            self.log_message(f"[{i}/{len(filtered_events)}] {event['source']} - Event {event['event_id']}", "warning")
                            self.analyze_and_create_ticket(event)
                        
                        self.save_history()
                        self.root.after(0, self.refresh_tickets)
                        self.log_message(f"✅ {len(filtered_events)} incident(s) traité(s)\n", "success")
                    else:
                        self.log_message(f"✅ {len(events)} événement(s) détectés mais aucun critique\n", "info")
                else:
                    self.log_message("✅ Aucune nouvelle menace\n", "info")
                
                for _ in range(POLLING_INTERVAL):
                    if not self.monitoring:
                        break
                    threading.Event().wait(1)
                
            except Exception as e:
                self.log_message(f"Erreur de surveillance: {e}", "error")
                threading.Event().wait(POLLING_INTERVAL)
    
    def cleanup_old_tickets(self):
        if messagebox.askyesno("Nettoyage", "Supprimer les incidents de plus de 30 jours ?"):
            cleaned = self.ticket_manager.cleanup_old_tickets()
            if cleaned:
                self.log_message(f"🗑 {cleaned} incident(s) supprimé(s)", "success")
                self.refresh_tickets()
            else:
                self.log_message("✅ Aucun incident à supprimer", "info")
    
    def load_tickets(self):
        try:
            self.ticket_tree.delete(*self.ticket_tree.get_children())
            
            if not os.path.exists(OUTPUT_DIR):
                return
            
            total = 0
            today_count = 0
            today = datetime.now().date()
            
            for folder in sorted(os.listdir(OUTPUT_DIR)):
                folder_path = os.path.join(OUTPUT_DIR, folder)
                if not os.path.isdir(folder_path) or folder.startswith('.'):
                    continue
                
                folder_id = self.ticket_tree.insert('', 'end', text=folder, open=False)
                
                tickets = [f for f in os.listdir(folder_path) if f.startswith('ticket_')]
                tickets.sort(reverse=True)
                
                for ticket in tickets:
                    ticket_path = os.path.join(folder_path, ticket)
                    total += 1
                    
                    try:
                        with open(ticket_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        date_match = re.search(r'📅 CRÉÉ LE: (.+)', content)
                        type_match = re.search(r'⚠️ TYPE: (.+)', content)
                        source_match = re.search(r'Source: (.+)', content)
                        event_id_match = re.search(r'Event ID: (\d+)', content)
                        computer_match = re.search(r'Ordinateur: (.+)', content)
                        occ_match = re.search(r'📊 OCCURRENCES: (\d+)', content)
                        
                        values = (
                            date_match.group(1) if date_match else 'N/A',
                            type_match.group(1) if type_match else 'N/A',
                            source_match.group(1) if source_match else 'N/A',
                            event_id_match.group(1) if event_id_match else 'N/A',
                            computer_match.group(1) if computer_match else 'N/A',
                            occ_match.group(1) if occ_match else '1'
                        )
                        
                        self.ticket_tree.insert(folder_id, 'end', text=ticket, values=values, tags=('ticket',))
                        
                        # Compter aujourd'hui
                        if date_match:
                            try:
                                ticket_date = datetime.strptime(date_match.group(1), '%Y-%m-%d %H:%M:%S').date()
                                if ticket_date == today:
                                    today_count += 1
                            except:
                                pass
                    
                    except Exception as e:
                        self.log_message(f"Erreur lecture {ticket}: {e}", "warning")
            
            # Mise à jour statistiques
            self.stats_label.config(
                text=f"Incidents: {total} | Aujourd'hui: {today_count} | Statut: Opérationnel"
            )
            
        except Exception as e:
            self.log_message(f"Erreur chargement tickets: {e}", "error")
    
    def filter_tickets(self):
        """Filtre les tickets selon la recherche"""
        search_term = self.search_var.get().lower()
        
        for item in self.ticket_tree.get_children():
            # Parcourir les dossiers
            for child in self.ticket_tree.get_children(item):
                values = self.ticket_tree.item(child)['values']
                text = self.ticket_tree.item(child)['text']
                
                # Rechercher dans toutes les valeurs
                match = any(
                    search_term in str(val).lower() 
                    for val in [text] + list(values)
                )
                
                if match:
                    self.ticket_tree.item(child, tags=('ticket',))
                else:
                    self.ticket_tree.item(child, tags=('hidden',))
        
        # Masquer les items cachés
        self.ticket_tree.tag_configure('hidden', foreground='#cccccc')
    
    def refresh_tickets(self):
        """Recharge la liste des tickets"""
        self.log_message("🔄 Actualisation de la base de données...", "info")
        self.load_tickets()
        self.log_message("✅ Base de données actualisée\n", "success")
    
    def open_ticket(self, event=None):
        """Ouvre un ticket dans l'onglet détails"""
        selection = self.ticket_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        parent = self.ticket_tree.parent(item)
        
        if not parent:
            return
        
        folder_name = self.ticket_tree.item(parent)['text']
        ticket_name = self.ticket_tree.item(item)['text']
        
        ticket_path = os.path.join(OUTPUT_DIR, folder_name, ticket_name)
        
        try:
            with open(ticket_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.detail_text.delete('1.0', tk.END)
            self.detail_text.insert('1.0', content)
            
            # Basculer vers l'onglet détails
            self.notebook.select(2)
            
            self.log_message(f"📄 Ticket ouvert: {ticket_name}", "info")
        
        except Exception as e:
            self.log_message(f"Erreur ouverture ticket: {e}", "error")
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le ticket:\n{e}")


def main():
    """Point d'entrée principal"""
    root = tk.Tk()
    
    # Configurer l'icône si disponible
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