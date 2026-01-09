import tkinter as tk
from tkinter import ttk

class StatusBar:
    def __init__(self, parent, theme):
        self.frame = ttk.Frame(parent, style='Main.TFrame')
        self.frame.pack(fill='x', padx=30, pady=(20, 10))
        
        self.status_label = ttk.Label(
            self.frame, 
            text="⚫ Inactif", 
            font=('Segoe UI', 10, 'bold'),
            foreground='#95a5a6',
            background=theme['bg_main']
        )
        self.status_label.pack(side='left')
        
        self.last_check_label = ttk.Label(
            self.frame, 
            text="Dernière vérification: Jamais",
            font=('Segoe UI', 9),
            foreground=theme['fg_secondary'],
            background=theme['bg_main']
        )
        self.last_check_label.pack(side='right')
    
    def update_status(self, text, color='#95a5a6'):
        self.status_label.config(text=text, foreground=color)
    
    def update_last_check(self, text):
        self.last_check_label.config(text=f"Dernière vérification: {text}")


class ControlPanel:
    def __init__(self, parent, callbacks):
        self.frame = ttk.Frame(parent, style='Main.TFrame')
        self.frame.pack(fill='x', padx=30, pady=(0, 20))
        
        btn_config = {
            'font': ('Segoe UI', 10),
            'relief': 'flat', 'bd': 0,
            'padx': 20, 'pady': 10,
            'cursor': 'hand2'
        }
        
        self.start_btn = tk.Button(
            self.frame, 
            text="▶ Surveillance",
            command=callbacks['start'],
            bg='#27ae60', fg='white',
            activebackground='#229954',
            **btn_config
        )
        self.start_btn.pack(side='left', padx=(0, 10))
        
        self.stop_btn = tk.Button(
            self.frame, 
            text="⏸ Arrêter",
            command=callbacks['stop'],
            bg='#e74c3c', fg='white',
            state='disabled',
            activebackground='#c0392b',
            **btn_config
        )
        self.stop_btn.pack(side='left', padx=(0, 10))
        
        tk.Button(
            self.frame, 
            text="🔄 Actualiser",
            command=callbacks['refresh'],
            bg='#3498db', fg='white',
            activebackground='#2980b9',
            **btn_config
        ).pack(side='left', padx=(0, 10))
        
        tk.Button(
            self.frame, 
            text="📅 Analyse 24h",
            command=callbacks['initial_check'],
            bg='#e67e22', fg='white',
            activebackground='#d35400',
            **btn_config
        ).pack(side='left', padx=(0, 10))
        
        self.stop_check_btn = tk.Button(
            self.frame, 
            text="⏹ Arrêter vérif.",
            command=callbacks['stop_check'],
            bg='#c0392b', fg='white',
            state='disabled',
            activebackground='#a93226',
            **btn_config
        )
        self.stop_check_btn.pack(side='left', padx=(0, 10))
        
        tk.Button(
            self.frame, 
            text="🗑 Nettoyer",
            command=callbacks['cleanup'],
            bg='#95a5a6', fg='white',
            activebackground='#7f8c8d',
            **btn_config
        ).pack(side='left')
    
    def set_monitoring_state(self, is_monitoring):
        if is_monitoring:
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
        else:
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
    
    def set_check_state(self, is_checking):
        self.stop_check_btn.config(state='normal' if is_checking else 'disabled')


class Footer:
    def __init__(self, parent, theme, version):
        self.frame = ttk.Frame(parent, style='Main.TFrame')
        self.frame.pack(fill='x', padx=30, pady=(0, 20))
        
        self.stats_label = ttk.Label(
            self.frame, 
            text="Incidents: 0 | Aujourd'hui: 0 | Statut: Prêt",
            font=('Segoe UI', 9),
            foreground=theme['fg_secondary'],
            background=theme['bg_main']
        )
        self.stats_label.pack(side='left')
        
        self.version_label = ttk.Label(
            self.frame, 
            text=f"Version {version} | © 2025",
            font=('Segoe UI', 8),
            foreground=theme['fg_secondary'],
            background=theme['bg_main']
        )
        self.version_label.pack(side='right')
    
    def update_stats(self, total, today, status="Opérationnel"):
        self.stats_label.config(text=f"Incidents: {total} | Aujourd'hui: {today} | {status}")