import tkinter as tk
from tkinter import ttk, scrolledtext


class TabCreators:
    """Classe pour créer tous les onglets de l'interface"""
    
    def __init__(self, notebook, theme):
        self.notebook = notebook
        self.theme = theme
    
    def create_monitor_tab(self):
        """Crée l'onglet Console de monitoring"""
        frame = ttk.Frame(self.notebook, style='Card.TFrame')
        self.notebook.add(frame, text="  Console  ")
        
        card = ttk.Frame(frame, style='Card.TFrame')
        card.pack(fill='both', expand=True, padx=20, pady=20)
        
        title_label = ttk.Label(card, text="Console multi-sources", style='Title.TLabel')
        title_label.pack(anchor='w', pady=(0, 10))
        
        console = scrolledtext.ScrolledText(
            card, wrap=tk.WORD, height=28,
            bg=self.theme['console_bg'], 
            fg=self.theme['console_fg'],
            font=('Consolas', 9),
            relief='solid', bd=1,
            insertbackground='#3498db',
            selectbackground=self.theme['select_bg']
        )
        console.pack(fill='both', expand=True)
        
        return console
    
    def create_ai_log_tab(self):
        """Crée l'onglet des logs IA"""
        frame = ttk.Frame(self.notebook, style='Card.TFrame')
        self.notebook.add(frame, text="  🤖 Analyses IA  ")
        
        card = ttk.Frame(frame, style='Card.TFrame')
        card.pack(fill='both', expand=True, padx=20, pady=20)
        
        title_label = ttk.Label(card, text="Journal des analyses IA en temps réel", style='Title.TLabel')
        title_label.pack(anchor='w', pady=(0, 10))
        
        ai_console = scrolledtext.ScrolledText(
            card, wrap=tk.WORD, height=28,
            bg=self.theme['console_bg'], 
            fg=self.theme['console_fg'],
            font=('Consolas', 9),
            relief='solid', bd=1,
            insertbackground='#3498db',
            selectbackground=self.theme['select_bg']
        )
        ai_console.pack(fill='both', expand=True)
        
        return ai_console
    
    def create_history_tab(self, output_dir, log_callback, on_select_callback, 
                          on_open_callback, on_menu_callback):
        """Crée l'onglet Base de données avec TreeView"""
        from ticket_tree_view import TicketTreeView
        
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
        
        search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame, textvariable=search_var, width=50,
            bg=self.theme['entry_bg'], fg=self.theme['entry_fg'],
            font=('Segoe UI', 10),
            relief='solid', bd=1,
            insertbackground='#3498db'
        )
        search_entry.pack(side='left', fill='x', expand=True)
        
        # Affichage du chemin
        path_frame = ttk.Frame(card, style='Card.TFrame')
        path_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(path_frame, text="📂 Chemin complet:", style='Normal.TLabel').pack(anchor='w', pady=(0, 5))
        
        path_display = tk.Text(
            path_frame, height=3, wrap=tk.WORD,
            bg=self.theme['entry_bg'], fg='#3498db',
            font=('Consolas', 9), relief='solid', bd=1, state='disabled'
        )
        path_display.pack(fill='x')
        
        # TreeView
        list_frame = ttk.Frame(card, style='Card.TFrame')
        list_frame.pack(fill='both', expand=True)
        
        # Créer le TicketTreeView
        ticket_tree_view = TicketTreeView(list_frame, output_dir, log_callback)
        
        # Scrollbars
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=ticket_tree_view.tree.yview)
        hsb = ttk.Scrollbar(list_frame, orient="horizontal", command=ticket_tree_view.tree.xview)
        ticket_tree_view.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        ticket_tree_view.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Bindings
        ticket_tree_view.tree.bind('<ButtonRelease-1>', on_select_callback)
        ticket_tree_view.tree.bind('<Double-1>', on_open_callback)
        ticket_tree_view.tree.bind('<Button-3>', on_menu_callback)
        ticket_tree_view.tree.bind('<Return>', lambda e: on_open_callback())
        
        # Recherche en temps réel
        search_entry.bind('<KeyRelease>', 
                         lambda e: ticket_tree_view.filter_tickets(search_var.get()))
        
        return ticket_tree_view, path_display, search_entry
    
    def create_detail_tab(self, export_callback, copy_callback):
        """Crée l'onglet des détails de ticket"""
        frame = ttk.Frame(self.notebook, style='Card.TFrame')
        self.notebook.add(frame, text="  📋 Détails  ")
        
        card = ttk.Frame(frame, style='Card.TFrame')
        card.pack(fill='both', expand=True, padx=20, pady=20)
        
        toolbar = ttk.Frame(card, style='Card.TFrame')
        toolbar.pack(fill='x', pady=(0, 10))
        
        title_label = ttk.Label(toolbar, text="Rapport d'incident détaillé", style='Title.TLabel')
        title_label.pack(side='left')
        
        btn_config = {
            'font': ('Segoe UI', 9), 
            'relief': 'flat', 'bd': 0, 
            'padx': 12, 'pady': 6, 
            'cursor': 'hand2'
        }
        
        tk.Button(
            toolbar, text="💾 Exporter", command=export_callback,
            bg='#3498db', fg='white', activebackground='#2980b9', **btn_config
        ).pack(side='right', padx=(5, 0))
        
        tk.Button(
            toolbar, text="📋 Copier", command=copy_callback,
            bg='#9b59b6', fg='white', activebackground='#8e44ad', **btn_config
        ).pack(side='right')
        
        detail_text = scrolledtext.ScrolledText(
            card, wrap=tk.WORD,
            bg=self.theme['console_bg'], fg=self.theme['console_fg'],
            font=('Consolas', 10), relief='solid', bd=1
        )
        detail_text.pack(fill='both', expand=True)
        
        detail_text.insert('1.0', 
            "📋 EXPLORATEUR DE TICKETS\n"
            "═══════════════════════════════════════════════════════════\n\n"
            "Double-cliquez sur un ticket dans 'Base de données'\n"
            "pour afficher son contenu complet ici.\n\n"
            "🖱️ ACTIONS DISPONIBLES:\n"
            "  • Clic sur un fichier → Voir son chemin\n"
            "  • Double-clic → Afficher le contenu\n"
            "  • Clic droit → Menu contextuel\n\n"
            "Les chemins complets sont affichés en permanence."
        )
        
        return detail_text