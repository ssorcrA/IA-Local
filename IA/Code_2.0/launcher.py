"""
Lanceur silencieux - se cache automatiquement
Fichier : launcher.pyw (IMPORTANT: .pyw pas .py)
À placer dans C:\IA\Code\
"""
import sys
import os

# Cacher la console si lancée avec python.exe au lieu de pythonw.exe
if sys.platform == 'win32':
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

try:
    # Import direct sans vérifications inutiles
    from main import main
    main()
    
except Exception as e:
    # Afficher l'erreur dans une boîte de dialogue
    import tkinter as tk
    from tkinter import messagebox
    
    root = tk.Tk()
    root.withdraw()
    
    messagebox.showerror("Erreur AD Monitor", 
                        f"Impossible de démarrer l'application:\n\n{str(e)}\n\n"
                        f"Vérifiez que tous les fichiers sont présents dans C:\\IA\\Code\\")
    
    root.destroy()