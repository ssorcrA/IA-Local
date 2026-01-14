"""
Gestionnaire de tickets - VERSION CORRIGÉE
Fichier : ticket_manager.py
CORRECTIFS:
- Regroupement par IP + hash du message
- Détection correcte des appareils (Windows + Syslog)
- Ticket UNIQUE par erreur unique, avec compteur
- Structure: Catégorie/IP_xxx/ticket_hash.txt
"""
import os
import json
import re
import hashlib
from datetime import datetime, timedelta, date
from config import OUTPUT_DIR, CLEANUP_DAYS, MONITORED_DEVICES, DEVICE_CATEGORIES


class TicketManager:
    """Gère les tickets avec regroupement intelligent"""
    
    def __init__(self, output_dir=OUTPUT_DIR):
        self.output_dir = output_dir
        self.ticket_index_file = os.path.join(output_dir, ".ticket_index.json")
        self.load_index()
        self.ensure_category_directories()
        
        # Stats pour le résumé final
        self.stats_created = 0
        self.stats_updated = 0
    
    def ensure_category_directories(self):
        """Crée les dossiers pour chaque catégorie"""
        for category in DEVICE_CATEGORIES.keys():
            category_path = os.path.join(self.output_dir, category)
            os.makedirs(category_path, exist_ok=True)
    
    def detect_category_from_ip(self, ip):
        """Détecte la catégorie depuis l'IP"""
        if not ip or ip == 'unknown':
            return None
        
        # Chercher dans MONITORED_DEVICES
        for device_ip, info in MONITORED_DEVICES.items():
            if ip == device_ip or device_ip in ip:
                return info['name']
        
        return None
    
    def detect_category_from_text(self, text):
        """Détecte la catégorie depuis le texte"""
        text_lower = text.lower()
        
        # Parcourir les catégories et leurs keywords
        for category, info in DEVICE_CATEGORIES.items():
            keywords = info.get('keywords', [])
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return category
        
        return None
    
    def detect_category(self, event):
        """
        🔥 DÉTECTION AMÉLIORÉE - Ordre de priorité:
        1. IP de l'appareil (Syslog ou Windows)
        2. Mots-clés dans source/computer
        3. "Autres" en dernier recours
        """
        # 1. Si c'est du Syslog, utiliser _device_ip
        if event.get('_is_syslog', False):
            ip = event.get('_device_ip', '')
            category = self.detect_category_from_ip(ip)
            if category:
                return category
        
        # 2. Extraire IP du champ 'computer' ou 'source' (Windows)
        computer = event.get('computer', '').lower()
        source = event.get('source', '').lower()
        
        # Chercher IP dans computer
        ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', computer)
        if ip_match:
            ip = ip_match.group(1)
            category = self.detect_category_from_ip(ip)
            if category:
                return category
        
        # Chercher IP dans source
        ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', source)
        if ip_match:
            ip = ip_match.group(1)
            category = self.detect_category_from_ip(ip)
            if category:
                return category
        
        # 3. Mots-clés dans source et computer
        full_text = f"{source} {computer}"
        category = self.detect_category_from_text(full_text)
        if category:
            return category
        
        # 4. Chercher dans le message complet
        message = event.get('message', '')
        category = self.detect_category_from_text(message)
        if category:
            return category
        
        # 5. Dernier recours: "Autres"
        return 'Autres'
    
    def get_message_hash(self, message):
        """
        🔥 HASH DU MESSAGE pour détecter les messages IDENTIQUES
        On normalise pour regrouper les messages similaires
        """
        # Normaliser: retirer IPs, nombres, timestamps
        normalized = message.lower()
        
        # Retirer IPs
        normalized = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', 'IP', normalized)
        
        # Retirer nombres (sauf Event IDs importants)
        normalized = re.sub(r'\b\d{5,}\b', 'NUM', normalized)
        
        # Retirer timestamps
        normalized = re.sub(r'\d{4}-\d{2}-\d{2}', 'DATE', normalized)
        normalized = re.sub(r'\d{2}:\d{2}:\d{2}', 'TIME', normalized)
        
        # Prendre les 200 premiers caractères pour le hash
        normalized = normalized[:200]
        
        # Créer hash
        return hashlib.md5(normalized.encode()).hexdigest()[:8]
    
    def get_ticket_key(self, event):
        """
        🔥 CLÉ DE REGROUPEMENT INTELLIGENTE:
        Catégorie + IP + Hash du message + Date
        
        Si 2 messages ont le MÊME hash → MÊME ticket (mis à jour)
        Si 2 messages ont un hash DIFFÉRENT → 2 tickets différents
        """
        category = self.detect_category(event)
        
        # Extraire l'IP
        ip = event.get('_device_ip', event.get('computer', 'unknown'))
        ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', ip)
        ip_clean = ip_match.group(1).replace('.', '_') if ip_match else 'unknown'
        
        # Hash du message
        message = event.get('message', '')
        msg_hash = self.get_message_hash(message)
        
        # Clé unique
        today = date.today().isoformat()
        key = f"{category}_{ip_clean}_{msg_hash}_{today}"
        
        return key
    
    def load_index(self):
        """Charge l'index des tickets"""
        try:
            if os.path.exists(self.ticket_index_file):
                with open(self.ticket_index_file, 'r', encoding='utf-8') as f:
                    self.ticket_index = json.load(f)
            else:
                self.ticket_index = {}
        except Exception as e:
            print(f"Erreur chargement index: {e}")
            self.ticket_index = {}
    
    def save_index(self):
        """Sauvegarde l'index"""
        try:
            with open(self.ticket_index_file, 'w', encoding='utf-8') as f:
                json.dump(self.ticket_index, f, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde index: {e}")
    
    def get_priority_emoji(self, priority):
        """Retourne l'emoji de priorité"""
        if priority >= 9:
            return "🔴"
        elif priority >= 7:
            return "🟠"
        elif priority >= 5:
            return "🟡"
        elif priority >= 3:
            return "🟢"
        else:
            return "⚪"
    
    def get_priority_label(self, priority):
        """Retourne le label de priorité"""
        emoji = self.get_priority_emoji(priority)
        if priority == 10:
            return f"{emoji} CRITIQUE 10/10"
        elif priority == 9:
            return f"{emoji} CRITIQUE 9/10"
        elif priority == 8:
            return f"🟠 HAUTE 8/10"
        elif priority == 7:
            return f"🟠 HAUTE 7/10"
        elif priority == 6:
            return f"🟡 MOYENNE 6/10"
        elif priority == 5:
            return f"🟡 MOYENNE 5/10"
        elif priority == 4:
            return f"🟢 BASSE 4/10"
        elif priority == 3:
            return f"🟢 BASSE 3/10"
        elif priority == 2:
            return f"🔵 INFO 2/10"
        else:
            return f"⚪ MINIMAL 1/10"
    
    def find_existing_ticket(self, event):
        """
        🔥 RECHERCHE UN TICKET EXISTANT
        Basé sur la clé intelligente (IP + hash message + date)
        """
        ticket_key = self.get_ticket_key(event)
        
        if ticket_key in self.ticket_index:
            ticket_path = self.ticket_index[ticket_key]
            if os.path.exists(ticket_path):
                return ticket_path
        
        return None
    
    def create_or_update_ticket(self, event, analysis, web_links, log_callback=None):
        """Crée ou met à jour un ticket"""
        existing_ticket = self.find_existing_ticket(event)
        
        if existing_ticket:
            if log_callback:
                log_callback(f"  📝 Ticket existant trouvé → Mise à jour")
            self.stats_updated += 1
            return self.update_existing_ticket(existing_ticket, event, log_callback)
        else:
            if log_callback:
                log_callback(f"  ✨ Nouvelle erreur → Création d'un ticket")
            self.stats_created += 1
            return self.create_new_ticket(event, analysis, web_links, log_callback)
    
    def create_new_ticket(self, event, analysis, web_links, log_callback=None):
        """Crée un nouveau ticket"""
        try:
            category = self.detect_category(event)
            category_info = DEVICE_CATEGORIES.get(category, {'icon': '❓', 'priority_boost': 0})
            
            # Extraire IP
            ip = event.get('_device_ip', event.get('computer', 'unknown'))
            ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', ip)
            ip_clean = ip_match.group(1).replace('.', '_') if ip_match else 'unknown'
            
            # Structure: Catégorie/IP_xxx_xxx_xxx_xxx/
            category_dir = os.path.join(self.output_dir, category)
            ip_dir = os.path.join(category_dir, f"IP_{ip_clean}")
            os.makedirs(ip_dir, exist_ok=True)
            
            # Hash du message
            msg_hash = self.get_message_hash(event.get('message', ''))
            
            # Nom du fichier
            today = date.today().isoformat()
            ticket_file = os.path.join(
                ip_dir,
                f"ticket_{today}_{msg_hash}.txt"
            )
            
            # Priorité
            priority = event.get('_priority', 5)
            if category in MONITORED_DEVICES:
                priority += MONITORED_DEVICES[category].get('priority_boost', 0)
            priority = min(priority, 10)
            
            priority_label = self.get_priority_label(priority)
            priority_emoji = self.get_priority_emoji(priority)
            
            # Severity
            severity = event.get('_severity', event.get('severity', 'unknown'))
            
            # Section web
            web_section = ""
            if web_links:
                web_section = "\n🌐 RESSOURCES WEB:\n"
                for i, link in enumerate(web_links, 1):
                    web_section += f"  [{i}] {link}\n"
            
            # Statut
            if priority >= 9:
                status = "🔴 CRITIQUE - ACTION IMMÉDIATE REQUISE"
            elif priority >= 7:
                status = "🟠 HAUTE - ACTION RAPIDE RECOMMANDÉE"
            elif priority >= 5:
                status = "🟡 MOYENNE - SURVEILLANCE NÉCESSAIRE"
            else:
                status = "🟢 BASSE - INFORMATION"
            
            # IP affichée
            ip_display = ip_match.group(1) if ip_match else ip
            
            content = f"""╔═══════════════════════════════════════════════════════════╗
║     {category_info['icon']} {category.upper()} - {priority_emoji} {priority_label}     ║
╚═══════════════════════════════════════════════════════════╝

📅 CRÉÉ LE: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
📊 OCCURRENCES: 1
🎯 PRIORITÉ: {priority_label}
📌 STATUT: {status}
🏷️ CATÉGORIE: {category_info['icon']} {category}
🔢 SEVERITY: {severity.upper()}

───────────────────────────────────────────────────────────

📊 INFORMATIONS TECHNIQUES:
  • Source: {event['source']}
  • IP/Appareil: {ip_display}
  • Première détection: {event['time_generated']}
  • Event ID: {event['event_id']}
  • Type: {event['event_type']}

───────────────────────────────────────────────────────────

📄 MESSAGE D'ERREUR:
{event['message'][:500]}...

───────────────────────────────────────────────────────────

📜 HISTORIQUE DES OCCURRENCES:

[1] {event['time_generated']}
    Message: {event['message'][:200]}...

───────────────────────────────────────────────────────────

🤖 ANALYSE & SOLUTION:
{analysis}
{web_section}
───────────────────────────────────────────────────────────

📋 ACTIONS RECOMMANDÉES:
"""
            
            if priority >= 9:
                content += """  1. ⚠️ BLOQUER IMMÉDIATEMENT l'accès si nécessaire
  2. 🔍 INVESTIGUER en urgence la source
  3. 📞 ALERTER l'équipe de sécurité
  4. 📋 DOCUMENTER tous les détails
  5. 🛡️ APPLIQUER les correctifs de sécurité
"""
            elif priority >= 7:
                content += """  1. 🔍 ANALYSER rapidement la situation
  2. 🛠️ APPLIQUER les solutions proposées
  3. 📊 SURVEILLER l'évolution
  4. 📝 DOCUMENTER les actions prises
"""
            elif priority >= 5:
                content += """  1. 📋 PLANIFIER une intervention
  2. 🔍 VÉRIFIER si le problème persiste
  3. 🛠️ APPLIQUER les correctifs recommandés
"""
            else:
                content += """  1. 📊 MONITORER la situation
  2. 📝 NOTER pour référence future
  3. ✅ APPLIQUER si temps disponible
"""
            
            content += f"""
───────────────────────────────────────────────────────────

📌 STATUT ACTUEL: NOUVEAU
🔔 NÉCESSITE ACTION: {"OUI - URGENT" if priority >= 7 else "OUI" if priority >= 5 else "SURVEILLANCE"}
⏰ DERNIÈRE MISE À JOUR: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
📈 TENDANCE: NOUVELLE DÉTECTION

═══════════════════════════════════════════════════════════
"""
            
            with open(ticket_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Indexer
            ticket_key = self.get_ticket_key(event)
            self.ticket_index[ticket_key] = ticket_file
            self.save_index()
            
            if log_callback:
                log_callback(f"  ✅ Ticket créé: {category}/IP_{ip_clean}/{os.path.basename(ticket_file)}")
            
            return ticket_file
            
        except Exception as e:
            if log_callback:
                log_callback(f"  ❌ Erreur création ticket: {e}")
            return None
    
    def update_existing_ticket(self, ticket_path, event, log_callback=None):
        """Met à jour un ticket existant"""
        try:
            with open(ticket_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Incrémenter occurrences
            occurrence_match = re.search(r'📊 OCCURRENCES: (\d+)', content)
            current_count = int(occurrence_match.group(1)) if occurrence_match else 1
            new_count = current_count + 1
            
            content = re.sub(
                r'📊 OCCURRENCES: \d+',
                f'📊 OCCURRENCES: {new_count}',
                content
            )
            
            # Ajouter dans historique
            new_occurrence = f"\n[{new_count}] {event['time_generated']}\n    Message: {event['message'][:200]}...\n"
            
            history_marker = "📜 HISTORIQUE DES OCCURRENCES:"
            if history_marker in content:
                parts = content.split("───────────────────────────────────────────────────────────")
                
                for i, part in enumerate(parts):
                    if history_marker in part:
                        parts[i] = part + new_occurrence
                        break
                
                content = "───────────────────────────────────────────────────────────".join(parts)
            
            # MAJ heure
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            content = re.sub(
                r'⏰ DERNIÈRE MISE À JOUR: .+',
                f'⏰ DERNIÈRE MISE À JOUR: {now}',
                content
            )
            
            # MAJ tendance
            if new_count >= 10:
                trend = "EN AUGMENTATION RAPIDE ⚠️"
            elif new_count >= 5:
                trend = "EN AUGMENTATION"
            else:
                trend = "STABLE"
            
            content = re.sub(
                r'📈 TENDANCE: .+',
                f'📈 TENDANCE: {trend} ({new_count} occurrences)',
                content
            )
            
            with open(ticket_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            if log_callback:
                log_callback(f"  📝 Ticket mis à jour: {new_count} occurrence(s)")
            
            return ticket_path
            
        except Exception as e:
            if log_callback:
                log_callback(f"  ❌ Erreur mise à jour ticket: {e}")
            return None
    
    def cleanup_old_tickets(self, days=CLEANUP_DAYS):
        """Nettoie les vieux tickets"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            cleaned = 0
            
            for category in DEVICE_CATEGORIES.keys():
                category_path = os.path.join(self.output_dir, category)
                if not os.path.exists(category_path):
                    continue
                
                for ip_folder in os.listdir(category_path):
                    ip_path = os.path.join(category_path, ip_folder)
                    
                    if not os.path.isdir(ip_path):
                        continue
                    
                    for ticket_file in os.listdir(ip_path):
                        if not ticket_file.startswith('ticket_'):
                            continue
                        
                        ticket_path = os.path.join(ip_path, ticket_file)
                        
                        if not os.path.isfile(ticket_path):
                            continue
                        
                        file_date = datetime.fromtimestamp(os.path.getmtime(ticket_path))
                        
                        if file_date < cutoff_date:
                            os.remove(ticket_path)
                            cleaned += 1
                    
                    if not os.listdir(ip_path):
                        os.rmdir(ip_path)
            
            self.ticket_index = {
                k: v for k, v in self.ticket_index.items()
                if os.path.exists(v)
            }
            self.save_index()
            
            return cleaned
            
        except Exception as e:
            print(f"Erreur nettoyage: {e}")
            return 0
    
    def get_stats(self):
        """Retourne les statistiques"""
        return {
            'created': self.stats_created,
            'updated': self.stats_updated,
            'total': self.stats_created + self.stats_updated
        }
    
    def reset_stats(self):
        """Réinitialise les statistiques"""
        self.stats_created = 0
        self.stats_updated = 0