"""
AD Log Monitor - Version Unifiée Multi-Sources
Fichier : main.py - VERSION 3.0 COMPLÈTE ET CORRIGÉE
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
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
        self.initial_check_thread = None
        self.dark_mode = ThemeManager.load_preference()
        self.current_theme = ThemeManager.DARK_THEME if self.dark_mode else ThemeManager.LIGHT_THEME
        self.current_ticket_path = None  # Chemin du ticket actuel
        
        ensure_directories()
        self.apply_theme()
        self.create_widgets()
        
        try:
            # Initialisation des composants
            self.log_reader = UnifiedLogReader(log_callback=self.log_message)
            self.ai_analyzer = EnhancedAIAnalyzer(log_callback=self.log_ai_message)
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
                       borderwidth=0,
                       rowheight=25)
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
        self.ai_console.config(bg=theme['console_bg'], fg=theme['console_fg'])
        self.search_entry.config(bg=theme['entry_bg'], fg=theme['entry_fg'])
        self.detail_text.config(bg=theme['console_bg'], fg=theme['console_fg'])
        self.path_display.config(bg=theme['entry_bg'], fg='#3498db')
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
            self.log_message("\n⚠️ Avertissements configuration:", "warning")
            for issue in issues:
                self.log_message(f"  • {issue}", "warning")
        
        # Vérification des sources de logs
        try:
            self.log_reader.check_availability()
            
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
        if self.monitoring or self.initial_check_running:
            if messagebox.askokcancel("Fermeture", "Des opérations sont en cours. Voulez-vous vraiment quitter ?"):
                self.force_stop_all()
                self.root.after(500, self.root.destroy)
        else:
            self.save_history()
            self.root.destroy()
    
    def force_stop_all(self):
        """Arrête toutes les opérations en cours"""
        self.log_message("\n🛑 ARRÊT FORCÉ DE TOUTES LES OPÉRATIONS", "warning")
        
        if self.monitoring:
            self.monitoring = False
        
        if self.initial_check_running:
            self.initial_check_running = False
        
        if hasattr(self.log_reader, 'event_reader') and self.log_reader.event_reader:
            self.log_reader.event_reader.request_stop()
        if hasattr(self.log_reader, 'syslog_reader') and self.log_reader.syslog_reader:
            self.log_reader.syslog_reader.request_stop()
        
        if self.ai_analyzer:
            self.ai_analyzer.request_stop()
        
        self.save_history()
        self.log_message("✅ Toutes les opérations ont été arrêtées\n", "success")
    
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
                                      text="⚫ Inactif", 
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
        self.create_ai_log_tab()
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
    
    def create_ai_log_tab(self):
        """Onglet pour les logs IA"""
        theme = self.current_theme
        frame = ttk.Frame(self.notebook, style='Card.TFrame')
        self.notebook.add(frame, text="  🤖 Analyses IA  ")
        
        card = ttk.Frame(frame, style='Card.TFrame')
        card.pack(fill='both', expand=True, padx=20, pady=20)
        
        title_label = ttk.Label(card, text="Journal des analyses IA en temps réel", style='Title.TLabel')
        title_label.pack(anchor='w', pady=(0, 10))
        
        self.ai_console = scrolledtext.ScrolledText(card, wrap=tk.WORD, height=28,
                                                    bg=theme['console_bg'], 
                                                    fg=theme['console_fg'],
                                                    font=('Consolas', 9),
                                                    relief='solid', bd=1,
                                                    insertbackground='#3498db',
                                                    selectbackground=theme['select_bg'])
        self.ai_console.pack(fill='both', expand=True)
        
        self.ai_console.tag_config("ai_request", foreground="#9b59b6", font=('Consolas', 9, 'bold'))
        self.ai_console.tag_config("ai_response", foreground="#27ae60")
        self.ai_console.tag_config("ai_error", foreground="#e74c3c", font=('Consolas', 9, 'bold'))
        self.ai_console.tag_config("ai_info", foreground="#3498db")
    
    def create_history_tab(self):
        """Onglet Base de données AMÉLIORÉ"""
        theme = self.current_theme
        frame = ttk.Frame(self.notebook, style='Card.TFrame')
        self.notebook.add(frame, text="  📁 Base de données  ")
        
        card = ttk.Frame(frame, style='Card.TFrame')
        card.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Barre d'outils
        toolbar = ttk.Frame(card, style='Card.TFrame')
        toolbar.pack(fill='x', pady=(0, 10))
        
        # Recherche
        search_frame = ttk.Frame(toolbar, style='Card.TFrame')
        search_frame.pack(side='left', fill='x', expand=True)
        
        ttk.Label(search_frame, text="🔍", style='Normal.TLabel').pack(side='left', padx=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=50,
                                     bg=theme['entry_bg'], fg=theme['entry_fg'],
                                     font=('Segoe UI', 10),
                                     relief='solid', bd=1,
                                     insertbackground='#3498db')
        self.search_entry.pack(side='left', fill='x', expand=True)
        self.search_entry.bind('<KeyRelease>', lambda e: self.filter_tickets())
        
        # Boutons d'action
        btn_frame = ttk.Frame(toolbar, style='Card.TFrame')
        btn_frame.pack(side='right', padx=(10, 0))
        
        btn_config = {'font': ('Segoe UI', 9), 'relief': 'flat', 'bd': 0, 'padx': 12, 'pady': 6, 'cursor': 'hand2'}
        
        tk.Button(btn_frame, text="📂 Ouvrir", command=self.open_ticket_folder,
                 bg='#3498db', fg='white', activebackground='#2980b9', **btn_config).pack(side='left', padx=(0, 5))
        
        tk.Button(btn_frame, text="📋 Copier", command=self.copy_ticket_path,
                 bg='#9b59b6', fg='white', activebackground='#8e44ad', **btn_config).pack(side='left', padx=(0, 5))
        
        tk.Button(btn_frame, text="🔄 Actualiser", command=self.refresh_tickets,
                 bg='#27ae60', fg='white', activebackground='#229954', **btn_config).pack(side='left')
        
        # Affichage du chemin
        path_frame = ttk.Frame(card, style='Card.TFrame')
        path_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(path_frame, text="📍 Chemin complet:", style='Normal.TLabel').pack(anchor='w', pady=(0, 5))
        
        self.path_display = tk.Text(path_frame, height=3, wrap=tk.WORD,
                                   bg=theme['entry_bg'], fg='#3498db',
                                   font=('Consolas', 9), relief='solid', bd=1, state='disabled')
        self.path_display.pack(fill='x')
        
        # Boutons pour le chemin
        path_btn_frame = ttk.Frame(card, style='Card.TFrame')
        path_btn_frame.pack(fill='x', pady=(0, 10))
        
        tk.Button(path_btn_frame, text="📋 Copier le chemin", command=self.copy_displayed_path,
                 bg='#9b59b6', fg='white', activebackground='#8e44ad',
                 font=('Segoe UI', 8), relief='flat', bd=0, padx=10, pady=4, cursor='hand2').pack(side='left', padx=(0, 5))
        
        tk.Button(path_btn_frame, text="📂 Ouvrir l'emplacement", command=self.open_path_location,
                 bg='#3498db', fg='white', activebackground='#2980b9',
                 font=('Segoe UI', 8), relief='flat', bd=0, padx=10, pady=4, cursor='hand2').pack(side='left')
        
        # Arborescence
        list_frame = ttk.Frame(card, style='Card.TFrame')
        list_frame.pack(fill='both', expand=True)
        
        cols = ('Date', 'Type', 'Source', 'Event ID', 'Ordinateur', 'Occurrences', 'Priorité', 'Taille')
        self.ticket_tree = ttk.Treeview(list_frame, columns=cols, show='tree headings', height=18)
        
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.ticket_tree.yview)
        hsb = ttk.Scrollbar(list_frame, orient="horizontal", command=self.ticket_tree.xview)
        self.ticket_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.ticket_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        self.ticket_tree.heading('#0', text='📁 Catégorie / 📄 Fichier')
        self.ticket_tree.column('#0', width=300, minwidth=200)
        
        col_widths = {'Date': 150, 'Type': 80, 'Source': 180, 'Event ID': 80, 
                     'Ordinateur': 130, 'Occurrences': 100, 'Priorité': 100, 'Taille': 80}
        
        for col in cols:
            self.ticket_tree.heading(col, text=col)
            self.ticket_tree.column(col, width=col_widths.get(col, 100))
        
        # Bindings
        self.ticket_tree.bind('<ButtonRelease-1>', self.on_ticket_select)
        self.ticket_tree.bind('<Double-1>', self.open_ticket)
        self.ticket_tree.bind('<Button-3>', self.show_tree_menu)
        self.ticket_tree.bind('<Return>', lambda e: self.open_ticket())
        
        # Menu contextuel
        self.tree_menu = tk.Menu(self.ticket_tree, tearoff=0)
        self.tree_menu.add_command(label="📄 Voir le contenu", command=self.open_ticket, font=('Segoe UI', 9, 'bold'))
        self.tree_menu.add_separator()
        self.tree_menu.add_command(label="📂 Ouvrir le dossier", command=self.open_ticket_folder)
        self.tree_menu.add_command(label="📂 Ouvrir dans l'explorateur", command=self.open_in_explorer)
        self.tree_menu.add_separator()
        self.tree_menu.add_command(label="📋 Copier le chemin complet", command=self.copy_ticket_path)
        self.tree_menu.add_command(label="📋 Copier le nom du fichier", command=self.copy_ticket_name)
        self.tree_menu.add_separator()
        self.tree_menu.add_command(label="🔍 Afficher les détails", command=self.show_ticket_details)
        self.tree_menu.add_command(label="🔄 Actualiser", command=self.refresh_tickets)
        
        self.root.after(100, self.load_tickets)
    
    def create_detail_tab(self):
        theme = self.current_theme
        frame = ttk.Frame(self.notebook, style='Card.TFrame')
        self.notebook.add(frame, text="  📋 Détails  ")
        
        card = ttk.Frame(frame, style='Card.TFrame')
        card.pack(fill='both', expand=True, padx=20, pady=20)
        
        toolbar = ttk.Frame(card, style='Card.TFrame')
        toolbar.pack(fill='x', pady=(0, 10))
        
        title_label = ttk.Label(toolbar, text="Rapport d'incident détaillé", style='Title.TLabel')
        title_label.pack(side='left')
        
        btn_config = {'font': ('Segoe UI', 9), 'relief': 'flat', 'bd': 0, 'padx': 12, 'pady': 6, 'cursor': 'hand2'}
        
        tk.Button(toolbar, text="💾 Exporter", command=self.export_current_ticket,
                 bg='#3498db', fg='white', activebackground='#2980b9', **btn_config).pack(side='right', padx=(5, 0))
        
        tk.Button(toolbar, text="📋 Copier", command=self.copy_ticket_content,
                 bg='#9b59b6', fg='white', activebackground='#8e44ad', **btn_config).pack(side='right')
        
        self.detail_text = scrolledtext.ScrolledText(card, wrap=tk.WORD,
                                                     bg=theme['console_bg'], fg=theme['console_fg'],
                                                     font=('Consolas', 10), relief='solid', bd=1)
        self.detail_text.pack(fill='both', expand=True)
        self.detail_text.insert('1.0', 
                               "📋 EXPLORATEUR DE TICKETS\n"
                               "═══════════════════════════════════════════════════\n\n"
                               "Double-cliquez sur un ticket dans 'Base de données'\n"
                               "pour afficher son contenu complet ici.\n\n"
                               "🖱️ ACTIONS DISPONIBLES:\n"
                               "  • Clic sur un fichier → Voir son chemin\n"
                               "  • Double-clic → Afficher le contenu\n"
                               "  • Clic droit → Menu contextuel\n\n"
                               "Les chemins complets sont affichés en permanence.")
    
    def log_message(self, message, tag="info"):
        """Affiche un message dans la console principale"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.console.insert(tk.END, f"[{timestamp}] {message}\n", tag)
            self.console.see(tk.END)
            self.root.update_idletasks()
        except:
            print(message)
    
    def log_ai_message(self, message, tag="ai_info"):
        """Affiche un message dans la console IA"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.ai_console.insert(tk.END, f"[{timestamp}] {message}\n", tag)
            self.ai_console.see(tk.END)
            self.root.update_idletasks()
        except:
            print(message)
    
    def on_ticket_select(self, event=None):
        """Mise à jour du chemin lors de la sélection"""
        selection = self.ticket_tree.selection()
        if not selection:
            self.update_path_display("Aucun fichier sélectionné")
            return
        
        item = selection[0]
        parent = self.ticket_tree.parent(item)
        
        if not parent:  # C'est une catégorie
            category_name = self.ticket_tree.item(item)['text']
            category_path = os.path.join(OUTPUT_DIR, category_name.replace('📁 ', '').split(' (')[0])
            self.current_ticket_path = category_path
            self.update_path_display(f"📁 Dossier: {category_path}")
        else:  # C'est un fichier
            folder_name = self.ticket_tree.item(parent)['text'].replace('📁 ', '').split(' (')[0]
            ticket_name = self.ticket_tree.item(item)['text'].replace('📄 ', '')
            
            ticket_path = os.path.join(OUTPUT_DIR, folder_name, ticket_name)
            self.current_ticket_path = ticket_path
            
            if os.path.exists(ticket_path):
                size = os.path.getsize(ticket_path)
                size_kb = size / 1024
                modified = datetime.fromtimestamp(os.path.getmtime(ticket_path))
                
                info = f"📄 Fichier: {ticket_path}\n"
                info += f"📦 Taille: {size_kb:.2f} KB ({size} octets)\n"
                info += f"🕐 Modifié: {modified.strftime('%Y-%m-%d %H:%M:%S')}"
                
                self.update_path_display(info)
            else:
                self.update_path_display(f"⚠️ Fichier introuvable: {ticket_path}")
    
    def update_path_display(self, text):
        """Met à jour l'affichage du chemin"""
        self.path_display.config(state='normal')
        self.path_display.delete('1.0', tk.END)
        self.path_display.insert('1.0', text)
        self.path_display.config(state='disabled')
    
    def copy_displayed_path(self):
        """Copie le chemin affiché"""
        if not self.current_ticket_path:
            messagebox.showwarning("Aucune sélection", "Veuillez d'abord sélectionner un fichier ou dossier")
            return
        
        self.root.clipboard_clear()
        self.root.clipboard_append(self.current_ticket_path)
        self.log_message(f"📋 Chemin copié: {self.current_ticket_path}", "info")
        
        original_text = self.path_display.get('1.0', tk.END).strip()
        self.update_path_display("✅ Chemin copié dans le presse-papier!")
        self.root.after(2000, lambda: self.update_path_display(original_text))
    
    def open_path_location(self):
        """Ouvre l'emplacement du fichier/dossier"""
        if not self.current_ticket_path:
            messagebox.showwarning("Aucune sélection", "Veuillez d'abord sélectionner un fichier ou dossier")
            return
        
        if os.path.isfile(self.current_ticket_path):
            os.system(f'explorer /select,"{self.current_ticket_path}"')
            self.log_message(f"📂 Fichier sélectionné dans l'explorateur", "info")
        elif os.path.isdir(self.current_ticket_path):
            os.startfile(self.current_ticket_path)
            self.log_message(f"📂 Dossier ouvert: {self.current_ticket_path}", "info")
        else:
            messagebox.showerror("Erreur", f"Chemin introuvable:\n{self.current_ticket_path}")
    
    def copy_ticket_path(self):
        """Copie le chemin complet du ticket sélectionné"""
        selection = self.ticket_tree.selection()
        if not selection:
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner un ticket")
            return
        
        item = selection[0]
        parent = self.ticket_tree.parent(item)
        
        if not parent:
            messagebox.showinfo("Information", "Veuillez sélectionner un fichier, pas une catégorie")
            return
        
        folder_name = self.ticket_tree.item(parent)['text'].replace('📁 ', '').split(' (')[0]
        ticket_name = self.ticket_tree.item(item)['text'].replace('📄 ', '')
        ticket_path = os.path.join(OUTPUT_DIR, folder_name, ticket_name)
        
        self.root.clipboard_clear()
        self.root.clipboard_append(ticket_path)
        
        messagebox.showinfo("Chemin copié", 
            f"Le chemin complet a été copié:\n\n"
            f"📄 {os.path.basename(ticket_path)}\n\n"
            f"📁 {os.path.dirname(ticket_path)}\n\n"
            f"📍 {ticket_path}")
        
        self.log_message(f"📋 Chemin copié: {ticket_path}", "info")
    
    def copy_ticket_name(self):
        """Copie uniquement le nom du fichier"""
        selection = self.ticket_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        parent = self.ticket_tree.parent(item)
        
        if not parent:
            return
        
        ticket_name = self.ticket_tree.item(item)['text'].replace('📄 ', '')
        
        self.root.clipboard_clear()
        self.root.clipboard_append(ticket_name)
        
        self.log_message(f"📋 Nom copié: {ticket_name}", "info")
        messagebox.showinfo("Nom copié", f"Nom du fichier copié:\n{ticket_name}")
    
    def open_in_explorer(self):
        """Ouvre dans l'explorateur Windows"""
        selection = self.ticket_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        parent = self.ticket_tree.parent(item)
        
        if not parent:
            category_name = self.ticket_tree.item(item)['text'].replace('📁 ', '').split(' (')[0]
            category_path = os.path.join(OUTPUT_DIR, category_name)
            if os.path.exists(category_path):
                os.startfile(category_path)
                self.log_message(f"📂 Catégorie ouverte: {category_name}", "info")
        else:
            folder_name = self.ticket_tree.item(parent)['text'].replace('📁 ', '').split(' (')[0]
            ticket_name = self.ticket_tree.item(item)['text'].replace('📄 ', '')
            ticket_path = os.path.join(OUTPUT_DIR, folder_name, ticket_name)
            
            if os.path.exists(ticket_path):
                os.system(f'explorer /select,"{ticket_path}"')
                self.log_message(f"📂 Fichier ouvert dans l'explorateur", "info")
    
    def show_ticket_details(self):
        """Affiche une fenêtre avec tous les détails du ticket"""
        selection = self.ticket_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        parent = self.ticket_tree.parent(item)
        
        if not parent:
            return
        
        folder_name = self.ticket_tree.item(parent)['text'].replace('📁 ', '').split(' (')[0]
        ticket_name = self.ticket_tree.item(item)['text'].replace('📄 ', '')
        ticket_path = os.path.join(OUTPUT_DIR, folder_name, ticket_name)
        
        if not os.path.exists(ticket_path):
            messagebox.showerror("Erreur", "Fichier introuvable")
            return
        
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Détails - {ticket_name}")
        details_window.geometry("700x500")
        
        main_frame = ttk.Frame(details_window, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        title_label = ttk.Label(main_frame, text="📋 INFORMATIONS DU TICKET", 
                               font=('Segoe UI', 14, 'bold'))
        title_label.pack(anchor='w', pady=(0, 20))
        
        info_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=20, font=('Consolas', 10))
        info_text.pack(fill='both', expand=True)
        
        size = os.path.getsize(ticket_path)
        size_kb = size / 1024
        created = datetime.fromtimestamp(os.path.getctime(ticket_path))
        modified = datetime.fromtimestamp(os.path.getmtime(ticket_path))
        
        details = f"""╔═══════════════════════════════════════════════════════════════╗
║  IDENTIFICATION                                              ║
╚═══════════════════════════════════════════════════════════════╝

📄 Nom: {ticket_name}
📁 Catégorie: {folder_name}

╔═══════════════════════════════════════════════════════════════╗
║  EMPLACEMENT                                                 ║
╚═══════════════════════════════════════════════════════════════╝

📍 Chemin complet:
{ticket_path}

📂 Dossier parent:
{os.path.dirname(ticket_path)}

╔═══════════════════════════════════════════════════════════════╗
║  PROPRIÉTÉS                                                  ║
╚═══════════════════════════════════════════════════════════════╝

📦 Taille: {size_kb:.2f} KB ({size} octets)
🕐 Créé: {created.strftime('%Y-%m-%d %H:%M:%S')}
🕐 Modifié: {modified.strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        info_text.insert('1.0', details)
        info_text.config(state='disabled')
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=(10, 0))
        
        tk.Button(btn_frame, text="📂 Ouvrir dossier", 
                 command=lambda: os.startfile(os.path.dirname(ticket_path)),
                 bg='#3498db', fg='white', font=('Segoe UI', 9),
                 relief='flat', bd=0, padx=15, pady=8, cursor='hand2').pack(side='left', padx=(0, 10))
        
        tk.Button(btn_frame, text="📋 Copier chemin", 
                 command=lambda: [self.root.clipboard_clear(), self.root.clipboard_append(ticket_path)],
                 bg='#9b59b6', fg='white', font=('Segoe UI', 9),
                 relief='flat', bd=0, padx=15, pady=8, cursor='hand2').pack(side='left', padx=(0, 10))
        
        tk.Button(btn_frame, text="✖ Fermer", command=details_window.destroy,
                 bg='#95a5a6', fg='white', font=('Segoe UI', 9),
                 relief='flat', bd=0, padx=15, pady=8, cursor='hand2').pack(side='right')
    
    def show_tree_menu(self, event):
        """Affiche le menu contextuel"""
        item = self.ticket_tree.identify_row(event.y)
        if item:
            self.ticket_tree.selection_set(item)
            self.tree_menu.post(event.x_root, event.y_root)
    
    def open_ticket_folder(self):
        """Ouvre le dossier du ticket dans l'explorateur"""
        selection = self.ticket_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        parent = self.ticket_tree.parent(item)
        
        if not parent:
            category_name = self.ticket_tree.item(item)['text'].replace('📁 ', '').split(' (')[0]
            category_path = os.path.join(OUTPUT_DIR, category_name)
            if os.path.exists(category_path):
                os.startfile(category_path)
        else:
            folder_name = self.ticket_tree.item(parent)['text'].replace('📁 ', '').split(' (')[0]
            ticket_name = self.ticket_tree.item(item)['text'].replace('📄 ', '')
            ticket_path = os.path.join(OUTPUT_DIR, folder_name, ticket_name)
            ticket_dir = os.path.dirname(ticket_path)
            
            if os.path.exists(ticket_dir):
                os.startfile(ticket_dir)
                self.log_message(f"📂 Dossier ouvert: {ticket_dir}", "info")
    
    def load_tickets(self):
        """Charge TOUS les tickets avec informations complètes"""
        try:
            self.ticket_tree.delete(*self.ticket_tree.get_children())
            
            if not os.path.exists(OUTPUT_DIR):
                return
            
            total = 0
            today_count = 0
            today = datetime.now().date()
            
            for category in sorted(os.listdir(OUTPUT_DIR)):
                category_path = os.path.join(OUTPUT_DIR, category)
                
                if not os.path.isdir(category_path) or category.startswith('.'):
                    continue
                
                ticket_count = 0
                for root, dirs, files in os.walk(category_path):
                    ticket_count += len([f for f in files if f.startswith('ticket_')])
                
                category_display = f"📁 {category} ({ticket_count} ticket{'s' if ticket_count != 1 else ''})"
                category_id = self.ticket_tree.insert('', 'end', text=category_display, open=False)
                
                for subfolder in sorted(os.listdir(category_path)):
                    subfolder_path = os.path.join(category_path, subfolder)
                    
                    if not os.path.isdir(subfolder_path):
                        continue
                    
                    tickets = [f for f in os.listdir(subfolder_path) if f.startswith('ticket_')]
                    tickets.sort(reverse=True)
                    
                    for ticket in tickets:
                        ticket_path = os.path.join(subfolder_path, ticket)
                        total += 1
                        
                        try:
                            with open(ticket_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            date_match = re.search(r'📅 CRÉÉ LE: (.+)', content)
                            type_match = re.search(r'⚠️ TYPE: (.+)', content)
                            source_match = re.search(r'Source: (.+)', content)
                            event_id_match = re.search(r'Event ID: (\d+)', content)
                            computer_match = re.search(r'Computer: (.+)', content)
                            occ_match = re.search(r'📊 OCCURRENCES: (\d+)', content)
                            priority_match = re.search(r'🎯 PRIORITÉ: (.+)', content)
                            
                            size = os.path.getsize(ticket_path) / 1024
                            
                            values = (
                                date_match.group(1) if date_match else 'N/A',
                                type_match.group(1) if type_match else 'N/A',
                                source_match.group(1) if source_match else 'N/A',
                                event_id_match.group(1) if event_id_match else 'N/A',
                                computer_match.group(1) if computer_match else 'N/A',
                                occ_match.group(1) if occ_match else '1',
                                priority_match.group(1) if priority_match else 'N/A',
                                f"{size:.1f} KB"
                            )
                            
                            display_name = f"📄 {ticket}"
                            
                            self.ticket_tree.insert(category_id, 'end', text=display_name, 
                                                  values=values, tags=('ticket',))
                            
                            if date_match:
                                try:
                                    ticket_date = datetime.strptime(date_match.group(1), '%Y-%m-%d %H:%M:%S').date()
                                    if ticket_date == today:
                                        today_count += 1
                                except:
                                    pass
                        
                        except Exception as e:
                            self.log_message(f"⚠️ Erreur lecture {ticket}: {e}", "warning")
            
            self.stats_label.config(text=f"Incidents: {total} | Aujourd'hui: {today_count} | Opérationnel")
            self.log_message(f"✅ {total} ticket(s) chargé(s)", "success")
            
        except Exception as e:
            self.log_message(f"❌ Erreur chargement tickets: {e}", "error")
    
    def export_current_ticket(self):
        """Exporte le ticket affiché vers un fichier"""
        content = self.detail_text.get('1.0', tk.END).strip()
        
        if not content or content.startswith("📋 EXPLORATEUR"):
            messagebox.showwarning("Aucun ticket", "Aucun ticket n'est actuellement affiché")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")],
            initialfile=f"ticket_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Exporté", f"Ticket exporté vers:\n{filename}")
                self.log_message(f"💾 Ticket exporté: {filename}", "success")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'exporter:\n{e}")
    
    def copy_ticket_content(self):
        """Copie tout le contenu du ticket affiché"""
        content = self.detail_text.get('1.0', tk.END).strip()
        
        if not content or content.startswith("📋 EXPLORATEUR"):
            messagebox.showwarning("Aucun ticket", "Aucun ticket n'est actuellement affiché")
            return
        
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        messagebox.showinfo("Copié", "Le contenu du ticket a été copié dans le presse-papier")
        self.log_message("📋 Contenu du ticket copié", "info")
    
    def filter_tickets(self):
        """Filtre les tickets selon la recherche"""
        search_term = self.search_var.get().lower()
        
        for item in self.ticket_tree.get_children():
            for child in self.ticket_tree.get_children(item):
                values = self.ticket_tree.item(child)['values']
                text = self.ticket_tree.item(child)['text']
                
                match = any(search_term in str(val).lower() for val in [text] + list(values))
                
                if match:
                    self.ticket_tree.item(child, tags=('ticket',))
                else:
                    self.ticket_tree.item(child, tags=('hidden',))
        
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
        
        folder_name = self.ticket_tree.item(parent)['text'].replace('📁 ', '').split(' (')[0]
        ticket_name = self.ticket_tree.item(item)['text'].replace('📄 ', '')
        
        ticket_path = os.path.join(OUTPUT_DIR, folder_name, ticket_name)
        
        try:
            with open(ticket_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.detail_text.delete('1.0', tk.END)
            self.detail_text.insert('1.0', content)
            
            self.notebook.select(3)
            
            self.log_message(f"📄 Ticket ouvert: {ticket_name}", "info")
            self.log_message(f"📍 Emplacement: {ticket_path}", "info")
        
        except Exception as e:
            self.log_message(f"Erreur ouverture ticket: {e}", "error")
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le ticket:\n{e}")
    
    def analyze_and_create_ticket(self, event):
        """Analyse avec logs IA et affichage du chemin"""
        try:
            if not self.monitoring and not self.initial_check_running:
                self.log_message("  🛑 Analyse annulée (arrêt demandé)", "warning")
                return False
            
            web_results = self.web_searcher.search(event)
            
            if not self.monitoring and not self.initial_check_running:
                self.log_message("  🛑 Analyse annulée après recherche web", "warning")
                return False
            
            self.log_ai_message("="*80, "ai_request")
            self.log_ai_message(f"🔍 REQUÊTE D'ANALYSE", "ai_request")
            self.log_ai_message(f"   Source: {event['source']}", "ai_request")
            self.log_ai_message(f"   Event ID: {event['event_id']}", "ai_request")
            self.log_ai_message(f"   Type: {event['event_type']}", "ai_request")
            self.log_ai_message(f"   Priorité: {event.get('_priority', 5)}/10", "ai_request")
            self.log_ai_message("="*80, "ai_request")
            
            analysis = self.ai_analyzer.analyze(event, web_results)
            
            if not self.monitoring and not self.initial_check_running:
                self.log_message("  🛑 Analyse annulée après IA", "warning")
                return False
            
            self.log_ai_message("\n💡 RÉPONSE IA REÇUE:", "ai_response")
            preview = analysis[:2000] + "..." if len(analysis) > 2000 else analysis
            self.log_ai_message(preview, "ai_response")
            self.log_ai_message(f"\n📏 Longueur totale: {len(analysis)} caractères", "ai_info")
            self.log_ai_message("="*80 + "\n", "ai_response")
            
            web_links = []
            if web_results:
                for match in re.finditer(r'🔗 (https?://[^\s]+)', web_results):
                    web_links.append(match.group(1))
            
            ticket_path = self.ticket_manager.create_or_update_ticket(
                event, analysis, web_links, 
                lambda msg: self.log_message(msg, "success")
            )
            
            if ticket_path:
                self.log_message(f"  📄 Ticket: {os.path.basename(ticket_path)}", "success")
                self.log_message(f"  📍 Chemin complet: {ticket_path}", "info")
                
                try:
                    rel_path = os.path.relpath(ticket_path, OUTPUT_DIR)
                    category = os.path.dirname(rel_path)
                    self.log_message(f"  📂 Catégorie: {category}", "info")
                except:
                    pass
            
            return True
            
        except Exception as e:
            self.log_message(f"  ❌ Erreur lors de l'analyse: {e}", "error")
            self.log_ai_message(f"❌ ERREUR: {e}", "ai_error")
            return False
    
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
        self.stop_check_btn.config(state='normal')
        self.start_btn.config(state='disabled')
        
        self.initial_check_thread = threading.Thread(target=self._initial_check_thread, daemon=True)
        self.initial_check_thread.start()
    
    def stop_initial_check(self):
        """ARRÊT COMPLET"""
        self.log_message("\n🛑 ARRÊT COMPLET DE TOUTES LES OPÉRATIONS", "warning")
        
        if self.initial_check_running:
            self.initial_check_running = False
            self.log_message("  ✓ Analyse 24h arrêtée", "warning")
        
        if self.monitoring:
            self.monitoring = False
            self.log_message("  ✓ Surveillance continue arrêtée", "warning")
        
        if hasattr(self.log_reader, 'event_reader') and self.log_reader.event_reader:
            self.log_reader.event_reader.request_stop()
            self.log_message("  ✓ Lecteur ForwardedEvents arrêté", "warning")
        
        if hasattr(self.log_reader, 'syslog_reader') and self.log_reader.syslog_reader:
            self.log_reader.syslog_reader.request_stop()
            self.log_message("  ✓ Lecteur Syslog arrêté", "warning")
        
        if self.ai_analyzer:
            self.ai_analyzer.request_stop()
            self.log_message("  ✓ Analyseur IA arrêté", "warning")
        
        if self.web_searcher:
            self.log_message("  ✓ Recherche web arrêtée", "warning")
        
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.stop_check_btn.config(state='disabled')
        self.status_label.config(text="⚫ Inactif", foreground='#95a5a6')
        
        self.save_history()
        
        self.log_message("\n✅ TOUT EST ARRÊTÉ - Système en pause\n", "success")
    
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
                            self.log_message(f"\n🛑 Analyse interrompue à {i}/{len(filtered_events)}", "warning")
                            break
                        
                        self.log_message(f"[{i}/{len(filtered_events)}] Analyse: {event['source']} - Event {event['event_id']}", "warning")
                        
                        success = self.analyze_and_create_ticket(event)
                        if not success:
                            break
                    
                    if self.initial_check_running:
                        self.save_history()
                        self.root.after(0, self.refresh_tickets)
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
            self.root.after(0, lambda: self.start_btn.config(state='normal'))
    
    def start_monitoring(self):
        if self.initial_check_running:
            messagebox.showwarning("Analyse en cours", "Attendez la fin de l'analyse 24h")
            return
        
        self.monitoring = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.status_label.config(text="🟢 Surveillance active", foreground='#27ae60')
        
        self.log_message(f"\nSurveillance multi-sources démarrée (intervalle: {POLLING_INTERVAL}s)", "success")
        self.log_message("Détection en temps réel sur toutes les sources disponibles\n", "success")
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """ARRÊT COMPLET - STOPPE TOUT CE QUI EST EN COURS"""
        self.log_message("\n🛑 ARRÊT COMPLET DE TOUTES LES OPÉRATIONS", "warning")
        
        if self.monitoring:
            self.monitoring = False
            self.log_message("  ✓ Surveillance continue arrêtée", "warning")
        
        if self.initial_check_running:
            self.initial_check_running = False
            self.log_message("  ✓ Analyse 24h arrêtée", "warning")
        
        if hasattr(self.log_reader, 'event_reader') and self.log_reader.event_reader:
            self.log_reader.event_reader.request_stop()
            self.log_message("  ✓ Lecteur ForwardedEvents arrêté", "warning")
        
        if hasattr(self.log_reader, 'syslog_reader') and self.log_reader.syslog_reader:
            self.log_reader.syslog_reader.request_stop()
            self.log_message("  ✓ Lecteur Syslog arrêté", "warning")
        
        if self.ai_analyzer:
            self.ai_analyzer.request_stop()
            self.log_message("  ✓ Analyseur IA arrêté (requêtes interrompues)", "warning")
        
        if self.web_searcher:
            self.log_message("  ✓ Recherche web arrêtée", "warning")
        
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.stop_check_btn.config(state='disabled')
        self.status_label.config(text="⚫ Inactif", foreground='#95a5a6')
        
        self.save_history()
        
        self.log_message("\n✅ TOUT EST ARRÊTÉ - Système en pause\n", "success")
    
    def _monitor_loop(self):
        while self.monitoring:
            try:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.root.after(0, lambda t=now: self.last_check_label.config(text=f"Dernière vérification: {t}"))
                
                self.log_message("Vérification en cours sur toutes les sources...", "info")
                events = self.log_reader.read_new_events()
                
                if not self.monitoring:
                    break
                
                if events:
                    filtered_events = self.event_filter.filter_events(events, enable_online_check=False)
                    
                    if not self.monitoring:
                        break
                    
                    if filtered_events:
                        self.log_message(f"\n⚠️ {len(filtered_events)} nouvelle(s) menace(s)!", "warning")
                        for i, event in enumerate(filtered_events, 1):
                            if not self.monitoring:
                                self.log_message(f"\n🛑 Analyse interrompue à {i}/{len(filtered_events)}", "warning")
                                break
                            
                            self.log_message(f"[{i}/{len(filtered_events)}] {event['source']} - Event {event['event_id']}", "warning")
                            success = self.analyze_and_create_ticket(event)
                            if not success:
                                break
                        
                        if self.monitoring:
                            self.save_history()
                            self.root.after(0, self.refresh_tickets)
                            self.log_message(f"✅ {len(filtered_events)} incident(s) traités\n", "success")
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
                self.log_message(f"🗑 {cleaned} incident(s) supprimés", "success")
                self.refresh_tickets()
            else:
                self.log_message("✅ Aucun incident à supprimer", "info")


def main():
    """Point d'entrée principal"""
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