"""
Détecteur d'appareils centralisé - CORRECTIF SERVEUR IA
Fichier : device_detector.py - VERSION CORRIGÉE
✅ Détection robuste du Serveur IA (192.168.10.110)
✅ Patterns étendus pour ForwardedEvents
"""


class DeviceDetector:
    """Détecteur centralisé d'appareils réseau"""
    
    # 🔥 MAPPING OFFICIEL DES 6 APPAREILS
    DEVICE_MAP = {
        # RÉSEAU (Syslog)
        '192.168.10.254': {
            'name': 'Stormshield',
            'full_name': 'Stormshield UTM',
            'type': 'firewall',
            'icon': '🔥',
            'folder': 'Stormshield',
            'priority_boost': 3,
            'description': 'Pare-feu principal'
        },
        '192.168.10.11': {
            'name': 'Borne WiFi',
            'full_name': 'Borne WiFi Principale',
            'type': 'wifi',
            'icon': '📡',
            'folder': 'Borne WiFi',
            'priority_boost': 2,
            'description': 'Point d\'accès sans-fil'
        },
        '192.168.10.15': {
            'name': 'Switch Principal',
            'full_name': 'Switch Principal (Core)',
            'type': 'switch',
            'icon': '🔌',
            'folder': 'Switch Principal',
            'priority_boost': 2,
            'description': 'Commutateur principal'
        },
        '192.168.10.16': {
            'name': 'Switch Secondaire',
            'full_name': 'Switch Secondaire (Distribution)',
            'type': 'switch',
            'icon': '🔌',
            'folder': 'Switch Secondaire',
            'priority_boost': 2,
            'description': 'Commutateur secondaire'
        },
        
        # SERVEURS (ForwardedEvents)
        '192.168.10.10': {
            'name': 'Serveur AD',
            'full_name': 'Serveur Active Directory',
            'type': 'server',
            'icon': '🖥️',
            'folder': 'Serveur AD',
            'priority_boost': 3,
            'description': 'Contrôleur de domaine'
        },
        '192.168.10.110': {
            'name': 'Serveur IA',
            'full_name': 'Serveur Intelligence Artificielle',
            'type': 'server',
            'icon': '🤖',
            'folder': 'Serveur IA',
            'priority_boost': 1,
            'description': 'Serveur d\'analyse IA (Ollama)'
        }
    }
    
    @classmethod
    def detect_from_ip(cls, ip):
        """
        Détecte l'appareil depuis une IP
        Retourne les infos complètes ou None
        """
        if not ip:
            return None
        
        ip = ip.strip()
        
        if ip in cls.DEVICE_MAP:
            return cls.DEVICE_MAP[ip].copy()
        
        return None
    
    @classmethod
    def detect_from_event(cls, event):
        """
        Détecte l'appareil depuis un événement
        🔥 AMÉLIORATION : Détection ULTRA robuste
        """
        
        # 1. PRIORITÉ MAXIMALE : _device_ip (déjà extrait)
        device_ip = event.get('_device_ip', '').strip()
        if device_ip:
            device = cls.detect_from_ip(device_ip)
            if device:
                return device, device_ip
        
        # 2. Champ 'computer' (peut contenir une IP ou hostname)
        computer = event.get('computer', '').strip()
        if computer:
            # Vérifier si c'est directement une IP
            device = cls.detect_from_ip(computer)
            if device:
                return device, computer
            
            # 🔥 AMÉLIORATION : Patterns de hostname
            computer_lower = computer.lower()
            
            # Mapping hostname → IP
            hostname_map = {
                'srv-ia': '192.168.10.110',
                'serveur-ia': '192.168.10.110',
                'ollama': '192.168.10.110',
                'ia': '192.168.10.110',
                
                'srv-ad': '192.168.10.10',
                'dc': '192.168.10.10',
                'active-directory': '192.168.10.10',
                
                'stormshield': '192.168.10.254',
                'utm': '192.168.10.254',
                'firewall': '192.168.10.254',
                
                'wifi': '192.168.10.11',
                'ap': '192.168.10.11',
                'borne': '192.168.10.11',
                
                'switch-1': '192.168.10.15',
                'sw1': '192.168.10.15',
                
                'switch-2': '192.168.10.16',
                'sw2': '192.168.10.16',
            }
            
            for hostname_pattern, ip in hostname_map.items():
                if hostname_pattern in computer_lower:
                    device = cls.detect_from_ip(ip)
                    if device:
                        return device, ip
            
            # Chercher IP dans le texte computer
            for ip, dev_info in cls.DEVICE_MAP.items():
                if ip in computer:
                    return dev_info.copy(), ip
        
        # 3. Champ 'source'
        source = event.get('source', '').strip()
        if source:
            source_lower = source.lower()
            
            # 🔥 Patterns étendus pour source
            source_patterns = {
                # Serveur IA
                'ia': '192.168.10.110',
                'ollama': '192.168.10.110',
                'srv-ia': '192.168.10.110',
                'serveur-ia': '192.168.10.110',
                'gpu': '192.168.10.110',
                'machine learning': '192.168.10.110',
                
                # Serveur AD
                'active directory': '192.168.10.10',
                'ntds': '192.168.10.10',
                'ldap': '192.168.10.10',
                'kerberos': '192.168.10.10',
                'srv-ad': '192.168.10.10',
                'dc': '192.168.10.10',
                
                # Stormshield
                'stormshield': '192.168.10.254',
                'asqd': '192.168.10.254',
                'firewall': '192.168.10.254',
                'utm': '192.168.10.254',
                
                # WiFi
                'wifi': '192.168.10.11',
                'wireless': '192.168.10.11',
                'borne': '192.168.10.11',
                'ap': '192.168.10.11',
                
                # Switches
                'switch': '192.168.10.15',  # Par défaut principal
            }
            
            for pattern, ip in source_patterns.items():
                if pattern in source_lower:
                    device = cls.detect_from_ip(ip)
                    if device:
                        return device, ip
            
            # Chercher IP directement
            for ip, dev_info in cls.DEVICE_MAP.items():
                if ip in source:
                    return dev_info.copy(), ip
        
        # 4. _device_name (depuis syslog)
        device_name = event.get('_device_name', '').strip()
        if device_name:
            device_name_lower = device_name.lower()
            for ip, dev_info in cls.DEVICE_MAP.items():
                if dev_info['name'].lower() in device_name_lower:
                    return dev_info.copy(), ip
        
        # 5. Dernier recours : chercher IP dans le message
        message = event.get('message', '')
        for ip, dev_info in cls.DEVICE_MAP.items():
            if ip in message:
                return dev_info.copy(), ip
        
        # 6. 🔥 SUPER FALLBACK : Patterns dans le message
        message_lower = message.lower()
        
        message_patterns = {
            'ollama': '192.168.10.110',
            'ia': '192.168.10.110',
            'gpu': '192.168.10.110',
            'srv-ia': '192.168.10.110',
        }
        
        for pattern, ip in message_patterns.items():
            if pattern in message_lower:
                device = cls.detect_from_ip(ip)
                if device:
                    return device, ip
        
        # Aucun appareil détecté
        return None, None
    
    @classmethod
    def get_folder_name(cls, ip):
        """Retourne le nom du dossier pour une IP"""
        device = cls.detect_from_ip(ip)
        if device:
            return device['folder']
        return 'Autres'
    
    @classmethod
    def get_device_name(cls, ip):
        """Retourne le nom court de l'appareil"""
        device = cls.detect_from_ip(ip)
        if device:
            return device['name']
        return 'Inconnu'
    
    @classmethod
    def get_full_name(cls, ip):
        """Retourne le nom complet de l'appareil"""
        device = cls.detect_from_ip(ip)
        if device:
            return device['full_name']
        return 'Appareil inconnu'
    
    @classmethod
    def get_icon(cls, ip):
        """Retourne l'icône de l'appareil"""
        device = cls.detect_from_ip(ip)
        if device:
            return device['icon']
        return '❓'
    
    @classmethod
    def get_all_devices(cls):
        """Retourne la liste de tous les appareils surveillés"""
        return [
            {
                'ip': ip,
                **info
            }
            for ip, info in cls.DEVICE_MAP.items()
        ]
    
    @classmethod
    def get_summary(cls):
        """Retourne un résumé textuel des appareils"""
        lines = []
        lines.append("\n📡 APPAREILS SURVEILLÉS (6 équipements) :")
        lines.append("=" * 80)
        
        # Grouper par type
        by_type = {
            'firewall': [],
            'wifi': [],
            'switch': [],
            'server': []
        }
        
        for ip, info in cls.DEVICE_MAP.items():
            by_type[info['type']].append((ip, info))
        
        # Afficher par catégorie
        if by_type['firewall']:
            lines.append("\n🔥 PARE-FEU :")
            for ip, info in by_type['firewall']:
                lines.append(f"   {info['icon']} {ip} → {info['full_name']}")
        
        if by_type['wifi']:
            lines.append("\n📡 WIFI :")
            for ip, info in by_type['wifi']:
                lines.append(f"   {info['icon']} {ip} → {info['full_name']}")
        
        if by_type['switch']:
            lines.append("\n🔌 SWITCHES :")
            for ip, info in by_type['switch']:
                lines.append(f"   {info['icon']} {ip} → {info['full_name']}")
        
        if by_type['server']:
            lines.append("\n🖥️ SERVEURS :")
            for ip, info in by_type['server']:
                lines.append(f"   {info['icon']} {ip} → {info['full_name']}")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)