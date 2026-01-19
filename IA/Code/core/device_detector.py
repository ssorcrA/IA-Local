"""
Détecteur d'appareils - RÈGLES CLAIRES
Fichier : device_detector.py - VERSION FINALE

✅ RÈGLES SIMPLES :
1. _is_syslog = True → Équipements réseau (par IP)
2. _source_type = 'forwarded_events' → Serveur AD (192.168.10.10)
3. Sinon → Serveur IA (192.168.10.110)
"""


class DeviceDetector:
    """Détecteur centralisé d'appareils avec règles claires"""
    
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
        
        # SERVEURS (Windows)
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
        """Détecte l'appareil depuis une IP"""
        if not ip:
            return None
        
        ip = ip.strip()
        
        if ip in cls.DEVICE_MAP:
            return cls.DEVICE_MAP[ip].copy()
        
        return None
    
    @classmethod
    def detect_from_event(cls, event):
        """
        🔥 DÉTECTION AVEC RÈGLES CLAIRES
        
        ORDRE DE PRIORITÉ :
        1. Si _is_syslog = True → Chercher IP dans équipements réseau
        2. Si _source_type = 'forwarded_events' → Serveur AD
        3. Sinon → Serveur IA
        
        Returns:
            (device_info: dict, device_ip: str) ou (None, None)
        """
        
        # ==========================================
        # RÈGLE 1 : SYSLOG = ÉQUIPEMENTS RÉSEAU
        # ==========================================
        if event.get('_is_syslog'):
            # Chercher dans _device_ip
            device_ip = event.get('_device_ip', '').strip()
            if device_ip:
                device = cls.detect_from_ip(device_ip)
                if device:
                    return device, device_ip
            
            # Chercher dans computer
            computer = event.get('computer', '').strip()
            if computer:
                device = cls.detect_from_ip(computer)
                if device:
                    return device, computer
            
            # Chercher dans source
            source = event.get('source', '').strip()
            for ip, dev_info in cls.DEVICE_MAP.items():
                if ip in source:
                    return dev_info.copy(), ip
            
            # Syslog mais IP non reconnue
            return None, None
        
        # ==========================================
        # RÈGLE 2 : FORWARDEDEVENTS = SERVEUR AD
        # ==========================================
        if event.get('_source_type') == 'forwarded_events':
            device = cls.DEVICE_MAP['192.168.10.10'].copy()
            return device, '192.168.10.10'
        
        # ==========================================
        # RÈGLE 3 : AUTRES WINDOWS = SERVEUR IA
        # ==========================================
        device = cls.DEVICE_MAP['192.168.10.110'].copy()
        return device, '192.168.10.110'
    
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
        """Retourne tous les appareils surveillés"""
        return [
            {
                'ip': ip,
                **info
            }
            for ip, info in cls.DEVICE_MAP.items()
        ]
    
    @classmethod
    def get_summary(cls):
        """Retourne un résumé des appareils surveillés"""
        lines = []
        lines.append("\n📡 APPAREILS SURVEILLÉS (6 équipements) :")
        lines.append("=" * 80)
        
        by_type = {
            'firewall': [],
            'wifi': [],
            'switch': [],
            'server': []
        }
        
        for ip, info in cls.DEVICE_MAP.items():
            by_type[info['type']].append((ip, info))
        
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