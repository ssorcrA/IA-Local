import os
import tkinter as tk
from tkinter import messagebox, filedialog
from datetime import datetime


class TicketOperations:
    """Gère toutes les opérations sur les tickets (ouverture, copie, export, etc.)"""
    
    def __init__(self, ticket_tree_view, output_dir, detail_text, log_callback, notebook, root):
        self.ticket_tree_view = ticket_tree_view
        self.output_dir = output_dir
        self.detail_text = detail_text
        self.log_callback = log_callback
        self.notebook = notebook
        self.root = root
    
    def update_path_display(self, ticket_path, path_display):
        """Met à jour l'affichage du chemin avec les informations du fichier"""
        if not ticket_path:
            self._set_path_text(path_display, "Aucun fichier sélectionné")
            return
        
        if os.path.isfile(ticket_path):
            size = os.path.getsize(ticket_path)
            size_kb = size / 1024
            modified = datetime.fromtimestamp(os.path.getmtime(ticket_path))
            
            info = f"📄 Fichier: {ticket_path}\n"
            info += f"📦 Taille: {size_kb:.2f} KB ({size} octets)\n"
            info += f"🕐 Modifié: {modified.strftime('%Y-%m-%d %H:%M:%S')}"
            
            self._set_path_text(path_display, info)
        elif os.path.isdir(ticket_path):
            self._set_path_text(path_display, f"📁 Dossier: {ticket_path}")
        else:
            self._set_path_text(path_display, f"⚠️ Fichier introuvable: {ticket_path}")
    
    def _set_path_text(self, path_display, text):
        """Utilitaire pour mettre à jour le texte du path_display"""
        path_display.config(state='normal')
        path_display.delete('1.0', tk.END)
        path_display.insert('1.0', text)
        path_display.config(state='disabled')
    
    def open_ticket(self, ticket_path):
        """Ouvre un ticket dans l'onglet détails"""
        if not ticket_path or not os.path.isfile(ticket_path):
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner un ticket valide")
            return
        
        try:
            with open(ticket_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.detail_text.delete('1.0', tk.END)
            self.detail_text.insert('1.0', content)
            
            # Bascule vers l'onglet détails (index 3)
            self.notebook.select(3)
            
            ticket_name = os.path.basename(ticket_path)
            self.log_callback(f"📄 Ticket ouvert: {ticket_name}", "info")
            self.log_callback(f"📂 Emplacement: {ticket_path}", "info")
        
        except Exception as e:
            self.log_callback(f"Erreur ouverture ticket: {e}", "error")
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le ticket:\n{e}")
    
    def export_ticket(self, detail_text):
        """Exporte le ticket affiché vers un fichier"""
        content = detail_text.get('1.0', tk.END).strip()
        
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
                self.log_callback(f"💾 Ticket exporté: {filename}", "success")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'exporter:\n{e}")
    
    def copy_content(self, detail_text):
        """Copie tout le contenu du ticket affiché"""
        content = detail_text.get('1.0', tk.END).strip()
        
        if not content or content.startswith("📋 EXPLORATEUR"):
            messagebox.showwarning("Aucun ticket", "Aucun ticket n'est actuellement affiché")
            return
        
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        messagebox.showinfo("Copié", "Le contenu du ticket a été copié dans le presse-papier")
        self.log_callback("📋 Contenu du ticket copié", "info")
    
    def copy_ticket_path(self, ticket_path):
        """Copie le chemin complet du ticket"""
        if not ticket_path:
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner un ticket")
            return
        
        self.root.clipboard_clear()
        self.root.clipboard_append(ticket_path)
        
        messagebox.showinfo("Chemin copié", 
            f"Le chemin complet a été copié:\n\n"
            f"📄 {os.path.basename(ticket_path)}\n\n"
            f"📂 {os.path.dirname(ticket_path)}\n\n"
            f"📍 {ticket_path}")
        
        self.log_callback(f"📋 Chemin copié: {ticket_path}", "info")
    
    def open_ticket_folder(self, ticket_path):
        """Ouvre le dossier contenant le ticket dans l'explorateur"""
        if not ticket_path:
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner un ticket")
            return
        
        if os.path.isfile(ticket_path):
            ticket_dir = os.path.dirname(ticket_path)
        elif os.path.isdir(ticket_path):
            ticket_dir = ticket_path
        else:
            messagebox.showerror("Erreur", f"Chemin introuvable:\n{ticket_path}")
            return
        
        if os.path.exists(ticket_dir):
            os.startfile(ticket_dir)
            self.log_callback(f"📂 Dossier ouvert: {ticket_dir}", "info")
        else:
            messagebox.showerror("Erreur", "Le dossier n'existe pas")
    
    def open_in_explorer(self, ticket_path):
        """Ouvre et sélectionne le fichier dans l'explorateur Windows"""
        if not ticket_path:
            return
        
        if os.path.isfile(ticket_path):
            os.system(f'explorer /select,"{ticket_path}"')
            self.log_callback(f"📂 Fichier sélectionné dans l'explorateur", "info")
        elif os.path.isdir(ticket_path):
            os.startfile(ticket_path)
            self.log_callback(f"📂 Dossier ouvert: {ticket_path}", "info")
        else:
            messagebox.showerror("Erreur", f"Chemin introuvable:\n{ticket_path}")
    
    def show_ticket_details(self, ticket_path):
        """Affiche une fenêtre modale avec tous les détails du ticket"""
        if not ticket_path or not os.path.isfile(ticket_path):
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner un ticket valide")
            return
        
        details_window = tk.Toplevel(self.root)
        details_window.title(f"Détails - {os.path.basename(ticket_path)}")
        details_window.geometry("700x500")
        
        from tkinter import ttk, scrolledtext
        
        main_frame = ttk.Frame(details_window, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        title_label = ttk.Label(main_frame, text="📋 INFORMATIONS DU TICKET", 
                               font=('Segoe UI', 14, 'bold'))
        title_label.pack(anchor='w', pady=(0, 20))
        
        info_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=20, font=('Consolas', 10))
        info_text.pack(fill='both', expand=True)
        
        # Récupération des informations
        size = os.path.getsize(ticket_path)
        size_kb = size / 1024
        created = datetime.fromtimestamp(os.path.getctime(ticket_path))
        modified = datetime.fromtimestamp(os.path.getmtime(ticket_path))
        ticket_name = os.path.basename(ticket_path)
        category = os.path.basename(os.path.dirname(ticket_path))
        
        details = f"""╔═══════════════════════════════════════════════════════════╗
║  IDENTIFICATION                                           ║
╚═══════════════════════════════════════════════════════════╝

📄 Nom: {ticket_name}
📁 Catégorie: {category}

╔═══════════════════════════════════════════════════════════╗
║  EMPLACEMENT                                              ║
╚═══════════════════════════════════════════════════════════╝

📍 Chemin complet:
{ticket_path}

📂 Dossier parent:
{os.path.dirname(ticket_path)}

╔═══════════════════════════════════════════════════════════╗
║  PROPRIÉTÉS                                               ║
╚═══════════════════════════════════════════════════════════╝

📦 Taille: {size_kb:.2f} KB ({size} octets)
🕐 Créé: {created.strftime('%Y-%m-%d %H:%M:%S')}
🕐 Modifié: {modified.strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        info_text.insert('1.0', details)
        info_text.config(state='disabled')
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=(10, 0))
        
        tk.Button(
            btn_frame, text="📂 Ouvrir dossier", 
            command=lambda: os.startfile(os.path.dirname(ticket_path)),
            bg='#3498db', fg='white', font=('Segoe UI', 9),
            relief='flat', bd=0, padx=15, pady=8, cursor='hand2'
        ).pack(side='left', padx=(0, 10))
        
        tk.Button(
            btn_frame, text="📋 Copier chemin", 
            command=lambda: [self.root.clipboard_clear(), self.root.clipboard_append(ticket_path)],
            bg='#9b59b6', fg='white', font=('Segoe UI', 9),
            relief='flat', bd=0, padx=15, pady=8, cursor='hand2'
        ).pack(side='left', padx=(0, 10))
        
        tk.Button(
            btn_frame, text="✖ Fermer", command=details_window.destroy,
            bg='#95a5a6', fg='white', font=('Segoe UI', 9),
            relief='flat', bd=0, padx=15, pady=8, cursor='hand2'
        ).pack(side='right')