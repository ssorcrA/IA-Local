"""
TreeView pour afficher : Catégorie > IP > Tickets
Fichier : ticket_tree_view.py - VERSION CORRIGÉE
Structure: Catégorie/IP_xxx_xxx_xxx_xxx/ticket_xxx.txt
"""
import os
import re
from datetime import datetime
from tkinter import ttk

class TicketTreeView:
    """TreeView pour afficher : Catégorie > IP > Tickets"""
    
    def __init__(self, parent, output_dir, log_callback):
        self.output_dir = output_dir
        self.log_callback = log_callback
        
        cols = ('Date', 'Type', 'Source', 'Event ID', 'Ordinateur', 'Occurrences', 'Priorité', 'Taille')
        self.tree = ttk.Treeview(parent, columns=cols, show='tree headings', height=18)
        
        self.tree.heading('#0', text='📁 Catégorie / 📍 IP / 📄 Ticket')
        self.tree.column('#0', width=350, minwidth=250)
        
        col_widths = {
            'Date': 150, 'Type': 80, 'Source': 180, 'Event ID': 80,
            'Ordinateur': 130, 'Occurrences': 100, 'Priorité': 100, 'Taille': 80
        }
        
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 100))
    
    def load_tickets(self):
        """Charge les tickets avec structure : Catégorie > IP > Tickets"""
        self.tree.delete(*self.tree.get_children())
        
        if not os.path.exists(self.output_dir):
            return 0, 0
        
        total = 0
        today_count = 0
        today = datetime.now().date()
        
        # Parcourir les catégories
        for category in sorted(os.listdir(self.output_dir)):
            category_path = os.path.join(self.output_dir, category)
            
            if not os.path.isdir(category_path) or category.startswith('.'):
                continue
            
            # Compter les tickets dans cette catégorie (récursif)
            ticket_count = 0
            for ip_folder in os.listdir(category_path):
                ip_path = os.path.join(category_path, ip_folder)
                if os.path.isdir(ip_path):
                    ticket_count += len([f for f in os.listdir(ip_path) if f.startswith('ticket_')])
            
            category_display = f"📁 {category} ({ticket_count} ticket{'s' if ticket_count != 1 else ''})"
            category_id = self.tree.insert('', 'end', text=category_display, open=False)
            
            # Parcourir les dossiers IP
            for ip_folder in sorted(os.listdir(category_path)):
                ip_path = os.path.join(category_path, ip_folder)
                
                if not os.path.isdir(ip_path) or not ip_folder.startswith('IP_'):
                    continue
                
                # Extraire l'IP du nom du dossier
                ip_display = ip_folder.replace('IP_', '').replace('_', '.')
                
                # Compter les tickets dans cet IP
                tickets = sorted(
                    [f for f in os.listdir(ip_path) if f.startswith('ticket_')],
                    reverse=True
                )
                
                if not tickets:
                    continue
                
                ip_display_full = f"📍 {ip_display} ({len(tickets)} ticket{'s' if len(tickets) != 1 else ''})"
                ip_node = self.tree.insert(category_id, 'end', text=ip_display_full, open=False)
                
                # Ajouter les tickets
                for ticket in tickets:
                    ticket_path = os.path.join(ip_path, ticket)
                    total += 1
                    
                    try:
                        values = self._extract_ticket_info(ticket_path)
                        display_name = f"📄 {ticket}"
                        
                        self.tree.insert(ip_node, 'end', text=display_name, 
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
        type_match = re.search(r'⚠️ TYPE: (.+)', content)
        source_match = re.search(r'Source: (.+)', content)
        event_id_match = re.search(r'Event ID: (\d+)', content)
        computer_match = re.search(r'Computer: (.+)', content)
        occ_match = re.search(r'📊 OCCURRENCES: (\d+)', content)
        priority_match = re.search(r'🎯 PRIORITÉ: (.+)', content)
        
        # Extraire IP/Computer
        ip_match = re.search(r'IP/Appareil: (.+)', content)
        computer = ip_match.group(1) if ip_match else (computer_match.group(1) if computer_match else 'N/A')
        
        size = os.path.getsize(ticket_path) / 1024
        
        return (
            date_match.group(1) if date_match else 'N/A',
            type_match.group(1) if type_match else 'N/A',
            source_match.group(1) if source_match else 'N/A',
            event_id_match.group(1) if event_id_match else 'N/A',
            computer,
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
        
        for category in self.tree.get_children():
            for ip_node in self.tree.get_children(category):
                for ticket in self.tree.get_children(ip_node):
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
        
        # Remonter la hiérarchie : ticket > ip > category
        ip_node = self.tree.parent(item)
        if not ip_node:
            return None
        
        category_node = self.tree.parent(ip_node)
        if not category_node:
            return None
        
        # Extraire les noms
        category_name = self.tree.item(category_node)['text'].replace('📁 ', '').split(' (')[0]
        ip_name = self.tree.item(ip_node)['text'].replace('📍 ', '').split(' (')[0]
        ip_folder = f"IP_{ip_name.replace('.', '_')}"
        ticket_name = self.tree.item(item)['text'].replace('📄 ', '')
        
        # Construire le chemin complet
        full_path = os.path.join(self.output_dir, category_name, ip_folder, ticket_name)
        
        return full_path if os.path.exists(full_path) else None