"""
TreeView pour afficher : APPAREIL > TYPE_ERREUR > Tickets
Fichier : ticket_tree_view.py - VERSION CORRIGÉE v2
Structure: APPAREIL/TYPE_ERREUR/ticket_xxx.txt
"""
import os
import re
from datetime import datetime
from tkinter import ttk

class TicketTreeView:
    """TreeView pour afficher : APPAREIL > TYPE_ERREUR > Tickets"""
    
    def __init__(self, parent, output_dir, log_callback):
        self.output_dir = output_dir
        self.log_callback = log_callback
        
        cols = ('Date', 'Type', 'Source', 'Event ID', 'Occurrences', 'Priorité', 'Taille')
        self.tree = ttk.Treeview(parent, columns=cols, show='tree headings', height=18)
        
        self.tree.heading('#0', text='🖥️ Appareil / 📂 Type Erreur / 📄 Ticket')
        self.tree.column('#0', width=400, minwidth=300)
        
        col_widths = {
            'Date': 150, 'Type': 100, 'Source': 200, 'Event ID': 100,
            'Occurrences': 100, 'Priorité': 120, 'Taille': 80
        }
        
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 100))
    
    def load_tickets(self):
        """Charge les tickets avec structure : APPAREIL > TYPE_ERREUR > Tickets"""
        self.tree.delete(*self.tree.get_children())
        
        if not os.path.exists(self.output_dir):
            return 0, 0
        
        total = 0
        today_count = 0
        today = datetime.now().date()
        
        # Parcourir les appareils
        for device_folder in sorted(os.listdir(self.output_dir)):
            device_path = os.path.join(self.output_dir, device_folder)
            
            if not os.path.isdir(device_path) or device_folder.startswith('.'):
                continue
            
            # Compter les tickets dans cet appareil (récursif)
            ticket_count = 0
            for error_type_folder in os.listdir(device_path):
                error_type_path = os.path.join(device_path, error_type_folder)
                if os.path.isdir(error_type_path):
                    ticket_count += len([f for f in os.listdir(error_type_path) if f.startswith('ticket_')])
            
            # Icônes par appareil
            device_icons = {
                'Serveur AD': '🖥️',
                'Serveur IA': '🤖',
                'Stormshield': '🔥',
                'Switch Principal': '🔌',
                'Switch Secondaire': '🔌',
                'Borne WiFi': '📡',
                'Autres': '❓'
            }
            icon = device_icons.get(device_folder, '📟')
            
            device_display = f"{icon} {device_folder} ({ticket_count} ticket{'s' if ticket_count != 1 else ''})"
            device_id = self.tree.insert('', 'end', text=device_display, open=False)
            
            # Parcourir les types d'erreurs
            for error_type_folder in sorted(os.listdir(device_path)):
                error_type_path = os.path.join(device_path, error_type_folder)
                
                if not os.path.isdir(error_type_path):
                    continue
                
                # Compter les tickets dans ce type d'erreur
                tickets = sorted(
                    [f for f in os.listdir(error_type_path) if f.startswith('ticket_')],
                    reverse=True
                )
                
                if not tickets:
                    continue
                
                # Afficher le type d'erreur de façon lisible
                error_display = error_type_folder.replace('_', ' ').replace('Event ', 'Event ID ')
                error_display_full = f"📂 {error_display} ({len(tickets)} ticket{'s' if len(tickets) != 1 else ''})"
                error_node = self.tree.insert(device_id, 'end', text=error_display_full, open=False)
                
                # Ajouter les tickets
                for ticket in tickets:
                    ticket_path = os.path.join(error_type_path, ticket)
                    total += 1
                    
                    try:
                        values = self._extract_ticket_info(ticket_path)
                        display_name = f"📄 {ticket}"
                        
                        self.tree.insert(error_node, 'end', text=display_name, 
                                       values=values, tags=('ticket',))
                        
                        if self._is_today(values[0]):
                            today_count += 1
                    except Exception as e:
                        self.log_callback(f"⚠️ Erreur lecture {ticket}: {e}", "warning")
        
        return total, today_count
    
    def _extract_ticket_info(self, ticket_path):
        """Extrait les informations d'un ticket"""
        with open(ticket_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        date_match = re.search(r'📅 CRÉÉ LE: (.+)', content)
        type_match = re.search(r'Type: (.+)', content)
        source_match = re.search(r'Source: (.+)', content)
        event_id_match = re.search(r'Event ID: (\d+)', content)
        occ_match = re.search(r'📊 OCCURRENCES: (\d+)', content)
        priority_match = re.search(r'🎯 PRIORITÉ: (.+)', content)
        
        size = os.path.getsize(ticket_path) / 1024
        
        return (
            date_match.group(1) if date_match else 'N/A',
            type_match.group(1) if type_match else 'N/A',
            source_match.group(1) if source_match else 'N/A',
            event_id_match.group(1) if event_id_match else 'N/A',
            occ_match.group(1) if occ_match else '1',
            priority_match.group(1) if priority_match else 'N/A',
            f"{size:.1f} KB"
        )
    
    def _is_today(self, date_str):
        """Vérifie si la date est aujourd'hui"""
        try:
            ticket_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').date()
            return ticket_date == datetime.now().date()
        except:
            return False
    
    def filter_tickets(self, search_term):
        """Filtre les tickets par recherche"""
        search_term = search_term.lower()
        
        for device in self.tree.get_children():
            for error_type_node in self.tree.get_children(device):
                for ticket in self.tree.get_children(error_type_node):
                    values = self.tree.item(ticket)['values']
                    text = self.tree.item(ticket)['text']
                    
                    match = any(search_term in str(val).lower() for val in [text] + list(values))
                    
                    self.tree.item(ticket, tags=('ticket',) if match else ('hidden',))
        
        self.tree.tag_configure('hidden', foreground='#cccccc')
    
    def get_selected_ticket_path(self):
        """Retourne le chemin complet du ticket sélectionné"""
        selection = self.tree.selection()
        if not selection:
            return None
        
        item = selection[0]
        
        # Remonter la hiérarchie : ticket > error_type > device
        error_type_node = self.tree.parent(item)
        if not error_type_node:
            return None
        
        device_node = self.tree.parent(error_type_node)
        if not device_node:
            return None
        
        # Extraire les noms
        device_name = self.tree.item(device_node)['text']
        # Retirer l'icône et le compteur
        device_name = re.sub(r'^[^\s]+\s+', '', device_name)  # Retirer icône
        device_name = re.sub(r'\s+\(\d+\s+ticket.*\)$', '', device_name)  # Retirer compteur
        
        error_type_name = self.tree.item(error_type_node)['text']
        error_type_name = re.sub(r'^📂\s+', '', error_type_name)
        error_type_name = re.sub(r'\s+\(\d+\s+ticket.*\)$', '', error_type_name)
        # Reconvertir en nom de dossier
        error_type_folder = error_type_name.replace(' ', '_').replace('Event_ID_', 'Event_')
        
        ticket_name = self.tree.item(item)['text'].replace('📄 ', '')
        
        # Construire le chemin complet
        full_path = os.path.join(self.output_dir, device_name, error_type_folder, ticket_name)
        
        return full_path if os.path.exists(full_path) else None