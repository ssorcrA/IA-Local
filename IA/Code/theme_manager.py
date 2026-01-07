"""
Gestionnaire de thèmes clair/sombre
"""
import os
import json
from config import OUTPUT_DIR


class ThemeManager:
    """Gestionnaire de thèmes clair/sombre"""
    
    LIGHT_THEME = {
        'bg_main': '#f5f5f5',
        'bg_card': '#ffffff',
        'bg_header': '#2c3e50',
        'fg_header': '#ffffff',
        'fg_main': '#2c3e50',
        'fg_secondary': '#7f8c8d',
        'console_bg': '#ffffff',
        'console_fg': '#2c3e50',
        'entry_bg': '#ffffff',
        'entry_fg': '#2c3e50',
        'tree_bg': '#ffffff',
        'tree_fg': '#2c3e50',
        'tree_heading_bg': '#ecf0f1',
        'tree_heading_fg': '#2c3e50',
        'border': '#d5dbdb',
        'select_bg': '#d5e8f7',
        'btn_active': '#27ae60',
        'btn_active_hover': '#229954',
        'btn_disabled': '#95a5a6',
    }
    
    DARK_THEME = {
        'bg_main': '#1a1a1a',
        'bg_card': '#2d2d2d',
        'bg_header': '#1a1a1a',
        'fg_header': '#ffffff',
        'fg_main': '#e0e0e0',
        'fg_secondary': '#a0a0a0',
        'console_bg': '#1e1e1e',
        'console_fg': '#d4d4d4',
        'entry_bg': '#3d3d3d',
        'entry_fg': '#e0e0e0',
        'tree_bg': '#2d2d2d',
        'tree_fg': '#e0e0e0',
        'tree_heading_bg': '#3d3d3d',
        'tree_heading_fg': '#e0e0e0',
        'border': '#4d4d4d',
        'select_bg': '#264f78',
        'btn_active': '#27ae60',
        'btn_active_hover': '#229954',
        'btn_disabled': '#5d5d5d',
    }
    
    PREFERENCES_FILE = os.path.join(OUTPUT_DIR, '.theme_preferences.json')
    
    @classmethod
    def load_preference(cls):
        """Charge la préférence de thème"""
        try:
            if os.path.exists(cls.PREFERENCES_FILE):
                with open(cls.PREFERENCES_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get('dark_mode', False)
        except:
            pass
        return False
    
    @classmethod
    def save_preference(cls, dark_mode):
        """Sauvegarde la préférence de thème"""
        try:
            with open(cls.PREFERENCES_FILE, 'w') as f:
                json.dump({'dark_mode': dark_mode}, f)
        except:
            pass