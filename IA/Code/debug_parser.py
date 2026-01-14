"""
Debug du parser - Analyse colonne par colonne
Fichier : debug_parser.py
"""
import re


def debug_parse_line(line):
    """Parse une ligne et affiche CHAQUE ÉTAPE"""
    print("=" * 120)
    print("🔍 ANALYSE DÉTAILLÉE DU LOG")
    print("=" * 120)
    
    print(f"\n📄 LOG COMPLET:\n{line}\n")
    
    # Split par espaces multiples
    parts = re.split(r'\s+', line)
    
    print(f"📊 COLONNES DÉTECTÉES (split par espaces):")
    print(f"   Total: {len(parts)} colonnes\n")
    
    for i, part in enumerate(parts[:15]):  # Afficher les 15 premières
        print(f"   [{i:2d}] = '{part}'")
    
    print("\n" + "-" * 120)
    print("🎯 EXTRACTION DES CHAMPS CLÉS")
    print("-" * 120)
    
    # IP
    ip = parts[0] if len(parts) > 0 else "N/A"
    print(f"\n1️⃣  IP (colonne 0):")
    print(f"    Valeur: {ip}")
    print(f"    Type: {'✅ Valide' if re.match(r'^\d+\.\d+\.\d+\.\d+$', ip) else '❌ Invalide'}")
    
    # Timestamp
    if len(parts) >= 4:
        month = parts[1]
        day = parts[2]
        time = parts[3]
        print(f"\n2️⃣  TIMESTAMP (colonnes 1-3):")
        print(f"    Mois: {month}")
        print(f"    Jour: {day}")
        print(f"    Heure: {time}")
        print(f"    Format: {month} {day} {time}")
    
    # Priority
    if len(parts) >= 5:
        priority = parts[4]
        print(f"\n3️⃣  PRIORITY (colonne 4):")
        print(f"    Valeur: {priority}")
    
    # User
    if len(parts) >= 6:
        user = parts[5]
        print(f"\n4️⃣  USER (colonne 5):")
        print(f"    Valeur: {user}")
    
    # SEVERITY - LA COLONNE CRITIQUE
    if len(parts) >= 7:
        severity = parts[6]
        print(f"\n5️⃣  SEVERITY (colonne 6) - ⭐ COLONNE CRITIQUE:")
        print(f"    Valeur détectée: '{severity}'")
        
        valid_severities = ['emerg', 'emergency', 'alert', 'crit', 'critical', 
                          'err', 'error', 'warning', 'warn', 'notice', 'info', 'debug']
        
        severity_lower = severity.lower()
        if severity_lower in valid_severities:
            print(f"    ✅ SEVERITY VALIDE!")
            
            # Afficher le niveau
            if severity_lower in ['emerg', 'emergency', 'alert', 'crit', 'critical']:
                print(f"    🔴 Niveau: CRITIQUE (9-10)")
            elif severity_lower in ['err', 'error']:
                print(f"    🔴 Niveau: ERROR (8)")
            elif severity_lower in ['warning', 'warn']:
                print(f"    🟡 Niveau: WARNING (7)")
            elif severity_lower == 'notice':
                print(f"    ⚪ Niveau: NOTICE (5)")
            else:
                print(f"    🔵 Niveau: INFO/DEBUG (2-3)")
        else:
            print(f"    ❌ SEVERITY INVALIDE (pas dans la liste)")
            print(f"    ⚠️  Ce log risque d'être traité comme 'notice' par défaut")
    
    # ISO Timestamp
    if len(parts) >= 8:
        iso_timestamp = parts[7]
        print(f"\n6️⃣  ISO TIMESTAMP (colonne 7):")
        print(f"    Valeur: {iso_timestamp}")
    
    # Hostname
    if len(parts) >= 9:
        hostname = parts[8]
        print(f"\n7️⃣  HOSTNAME (colonne 8):")
        print(f"    Valeur: {hostname}")
    
    # Facility (chercher asqd, firewall, etc.)
    facility = "syslog"
    for part in parts[7:]:
        if part in ['asqd', 'firewall', 'auth', 'kernel', 'system']:
            facility = part
            break
    
    print(f"\n8️⃣  FACILITY (recherché dans le message):")
    print(f"    Valeur: {facility}")
    
    print("\n" + "=" * 120)
    
    # Résumé
    if len(parts) >= 7:
        severity_value = parts[6].lower()
        valid = severity_value in ['emerg', 'emergency', 'alert', 'crit', 'critical', 
                                   'err', 'error', 'warning', 'warn', 'notice', 'info', 'debug']
        
        print("\n📋 RÉSUMÉ:")
        print(f"   IP: {ip}")
        print(f"   Severity: {severity_value}")
        print(f"   Validation: {'✅ OK' if valid else '❌ ERREUR'}")
        
        if valid:
            if severity_value in ['warning', 'warn', 'alert', 'err', 'error', 'crit', 'critical', 'emerg']:
                print(f"   🎫 Devrait créer un ticket: ✅ OUI")
            else:
                print(f"   🎫 Devrait créer un ticket: ❌ NON")
    
    print("=" * 120)


def test_multiple_logs():
    """Test avec plusieurs types de logs"""
    test_logs = [
        ("NOTICE", "192.168.10.254  Jan 12 08:58:53 1    user   notice    2026-01-14T09:01:30+01:00 SN310A41KL181A7 asqd - - id=firewall"),
        ("WARNING", "192.168.10.254  Jan 12 08:58:54 1    user   warning   2026-01-14T09:01:31+01:00 SN310A41KL181A7 asqd - - id=firewall"),
        ("ALERT", "192.168.10.254  Jan 12 08:59:01 1    user   alert     2026-01-14T09:01:38+01:00 SN310A41KL181A7 asqd - - id=firewall"),
        ("ERROR", "192.168.10.254  Jan 12 08:59:01 1    user   err       2026-01-14T09:01:38+01:00 SN310A41KL181A7 asqd - - id=firewall"),
    ]
    
    print("\n\n")
    print("╔" + "═" * 118 + "╗")
    print("║" + " " * 40 + "TEST DE PLUSIEURS LOGS" + " " * 56 + "║")
    print("╚" + "═" * 118 + "╝")
    
    for label, log in test_logs:
        print(f"\n\n{'#' * 120}")
        print(f"# {label}")
        print(f"{'#' * 120}")
        debug_parse_line(log)
        
        input(f"\n⏸️  Appuyez sur Entrée pour continuer vers {label} suivant...")


if __name__ == "__main__":
    print("\n🔬 DEBUG DU PARSER SYSLOG")
    print("=" * 120)
    
    # Menu
    print("\nQue voulez-vous faire?")
    print("  1. Analyser UNE ligne personnalisée")
    print("  2. Tester les 4 types de logs (notice, warning, alert, error)")
    print("  3. Quitter")
    
    choice = input("\nVotre choix (1/2/3): ")
    
    if choice == "1":
        print("\n📝 Collez votre ligne de log Syslog:")
        log_line = input("> ")
        debug_parse_line(log_line)
        
    elif choice == "2":
        test_multiple_logs()
        
    else:
        print("\n👋 Au revoir!")