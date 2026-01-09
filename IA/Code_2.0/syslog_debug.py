"""
Script de diagnostic pour comprendre pourquoi les tentatives d'intrusion ne sont pas détectées
Fichier : syslog_debug.py
"""
import os
import re
from datetime import datetime, timedelta


def analyze_syslog_file(syslog_path, last_minutes=5):
    """
    Analyse les dernières minutes du fichier Syslog
    et affiche TOUT ce qui est détecté
    """
    
    print("=" * 80)
    print("🔍 DIAGNOSTIC SYSLOG - DÉTECTION D'INTRUSION")
    print("=" * 80)
    
    if not os.path.exists(syslog_path):
        print(f"❌ Fichier introuvable: {syslog_path}")
        return
    
    print(f"\n📂 Fichier: {syslog_path}")
    size_mb = os.path.getsize(syslog_path) / (1024 * 1024)
    print(f"📦 Taille: {size_mb:.2f} MB")
    
    # Lire les dernières lignes (plus rapide)
    cutoff_time = datetime.now() - timedelta(minutes=last_minutes)
    print(f"\n⏰ Recherche des événements depuis: {cutoff_time.strftime('%H:%M:%S')}")
    print(f"   (dernières {last_minutes} minutes)")
    
    print("\n" + "=" * 80)
    print("ANALYSE LIGNE PAR LIGNE")
    print("=" * 80)
    
    monitored_ips = ['192.168.1.254', '192.168.10.254', '192.168.1.15', '192.168.1.11']
    
    total_lines = 0
    relevant_lines = 0
    potential_intrusions = 0
    
    # Mots-clés liés aux intrusions
    intrusion_keywords = [
        'fail', 'failed', 'deny', 'denied', 'drop', 'dropped', 'block', 'blocked',
        'reject', 'rejected', 'unauthorized', 'invalid', 'authentication',
        'attack', 'intrusion', 'scan', 'probe', 'suspicious', 'malicious',
        'brute', 'force', 'attempt', 'violation', 'breach', 'alert'
    ]
    
    try:
        with open(syslog_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        
        # Prendre les 1000 dernières lignes pour aller plus vite
        lines = lines[-1000:] if len(lines) > 1000 else lines
        
        print(f"\n📊 Analyse de {len(lines)} dernières lignes du fichier...\n")
        
        for line in lines:
            total_lines += 1
            line = line.strip()
            
            if not line:
                continue
            
            # Vérifier si ligne contient une IP surveillée
            has_monitored_ip = any(ip in line for ip in monitored_ips)
            
            if not has_monitored_ip:
                continue
            
            relevant_lines += 1
            
            # Extraire l'IP
            found_ip = None
            for ip in monitored_ips:
                if line.startswith(ip):
                    found_ip = ip
                    break
            
            # Chercher timestamp
            time_match = re.search(r'(\w+)\s+(\d+)\s+(\d+:\d+:\d+)', line)
            timestamp_str = "N/A"
            if time_match:
                timestamp_str = f"{time_match.group(1)} {time_match.group(2)} {time_match.group(3)}"
            
            # Chercher severity
            severity = "UNKNOWN"
            severity_match = re.search(r'\b(emerg|alert|crit|err|error|warning|warn|notice|info|debug)\b', line, re.IGNORECASE)
            if severity_match:
                severity = severity_match.group(1).upper()
            
            # Chercher facility
            facility = "UNKNOWN"
            fac_match = re.search(r'\d+\s+(\w+)\s+(?:emerg|alert|crit|err|error|warning|warn|notice|info|debug)', line, re.IGNORECASE)
            if fac_match:
                facility = fac_match.group(1)
            
            # Chercher mots-clés d'intrusion
            line_lower = line.lower()
            found_keywords = [kw for kw in intrusion_keywords if kw in line_lower]
            
            if found_keywords:
                potential_intrusions += 1
                
                print("─" * 80)
                print(f"🚨 INTRUSION POTENTIELLE #{potential_intrusions}")
                print("─" * 80)
                print(f"⏰ Timestamp: {timestamp_str}")
                print(f"📍 IP Source: {found_ip or 'N/A'}")
                print(f"🏷️  Facility: {facility}")
                print(f"⚠️  Severity: {severity}")
                print(f"🔑 Mots-clés trouvés: {', '.join(found_keywords)}")
                print(f"\n📝 Message complet:")
                print(f"   {line[:200]}{'...' if len(line) > 200 else ''}")
                print()
            
            # Afficher aussi les lignes avec severity critique
            elif severity in ['EMERG', 'ALERT', 'CRIT', 'ERR', 'ERROR']:
                print("─" * 80)
                print(f"⚠️  SEVERITY ÉLEVÉE: {severity}")
                print("─" * 80)
                print(f"⏰ {timestamp_str} | 📍 {found_ip or 'N/A'} | 🏷️  {facility}")
                print(f"📝 {line[:200]}{'...' if len(line) > 200 else ''}")
                print()
        
        print("=" * 80)
        print("📊 RÉSUMÉ")
        print("=" * 80)
        print(f"Total de lignes analysées: {total_lines}")
        print(f"Lignes avec IP surveillée: {relevant_lines}")
        print(f"🚨 INTRUSIONS POTENTIELLES DÉTECTÉES: {potential_intrusions}")
        
        if potential_intrusions == 0:
            print("\n⚠️  AUCUNE INTRUSION DÉTECTÉE !")
            print("\n🔍 RAISONS POSSIBLES:")
            print("   1. Les tentatives d'intrusion ne sont pas loggées dans Syslog")
            print("   2. Le format des logs ne correspond pas aux patterns")
            print("   3. L'IP source n'est pas dans les appareils surveillés")
            print("   4. Les mots-clés utilisés ne matchent pas")
            print("\n💡 SUGGESTION:")
            print("   Copiez-collez ici 2-3 lignes EXACTES du Syslog")
            print("   correspondant à votre test d'intrusion")
        else:
            print(f"\n✅ {potential_intrusions} événement(s) suspect(s) trouvé(s)")
            print("\n🔍 VÉRIFIEZ:")
            print("   1. Ces événements correspondent-ils à votre test ?")
            print("   2. L'application devrait les avoir capturés")
            print("   3. Si non, vérifiez le MIN_PRIORITY_THRESHOLD dans config.py")
    
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()


def test_specific_line(line):
    """
    Teste une ligne spécifique de log
    """
    print("\n" + "=" * 80)
    print("🧪 TEST D'UNE LIGNE SPÉCIFIQUE")
    print("=" * 80)
    print(f"\n📝 Ligne à tester:")
    print(f"   {line}")
    
    monitored_ips = ['192.168.1.254', '192.168.10.254', '192.168.1.15', '192.168.1.11']
    
    # Test 1: IP détectée ?
    has_ip = any(ip in line for ip in monitored_ips)
    print(f"\n✓ Contient une IP surveillée: {'OUI' if has_ip else 'NON'}")
    if has_ip:
        for ip in monitored_ips:
            if ip in line:
                print(f"   → IP trouvée: {ip}")
    
    # Test 2: Severity détectée ?
    severity_match = re.search(r'\b(emerg|alert|crit|err|error|warning|warn|notice|info|debug)\b', line, re.IGNORECASE)
    print(f"\n✓ Severity détectée: {'OUI - ' + severity_match.group(1).upper() if severity_match else 'NON'}")
    
    # Test 3: Facility détectée ?
    fac_match = re.search(r'\d+\s+(\w+)\s+(?:emerg|alert|crit|err|error|warning|warn|notice|info|debug)', line, re.IGNORECASE)
    print(f"\n✓ Facility détectée: {'OUI - ' + fac_match.group(1) if fac_match else 'NON'}")
    
    # Test 4: Mots-clés d'intrusion ?
    intrusion_keywords = [
        'fail', 'failed', 'deny', 'denied', 'drop', 'dropped', 'block', 'blocked',
        'reject', 'rejected', 'unauthorized', 'invalid', 'authentication',
        'attack', 'intrusion', 'scan', 'probe', 'suspicious', 'malicious'
    ]
    
    line_lower = line.lower()
    found_keywords = [kw for kw in intrusion_keywords if kw in line_lower]
    print(f"\n✓ Mots-clés trouvés: {', '.join(found_keywords) if found_keywords else 'AUCUN'}")
    
    # Test 5: Calcul priorité
    priority = 3  # Par défaut
    
    severity_scores = {
        'emerg': 10, 'alert': 9, 'crit': 10,
        'err': 8, 'error': 8,
        'warning': 5, 'warn': 5
    }
    
    if severity_match:
        sev = severity_match.group(1).lower()
        if sev in severity_scores:
            priority = max(priority, severity_scores[sev])
    
    keyword_scores = {
        'attack': 10, 'intrusion': 10, 'breach': 10,
        'fail': 7, 'failed': 7, 'deny': 7, 'drop': 7,
        'unauthorized': 8, 'invalid': 6, 'authentication': 6
    }
    
    for kw in found_keywords:
        if kw in keyword_scores:
            priority = max(priority, keyword_scores[kw])
    
    print(f"\n✓ Priorité calculée: {priority}/10")
    
    # Test 6: Devrait créer un ticket ?
    should_create = priority >= 7  # Seuil par défaut
    print(f"\n✓ Devrait créer un TICKET: {'OUI ✅' if should_create else 'NON ❌'}")
    
    if not should_create:
        print(f"\n⚠️  RAISON: Priorité {priority}/10 < seuil minimum (7)")


if __name__ == "__main__":
    import sys
    
    # Chemin par défaut
    syslog_path = r"\\SRV-SYSLOG\surveillence$\syslog"
    
    print("\n🔧 SCRIPT DE DIAGNOSTIC SYSLOG")
    print("=" * 80)
    
    if len(sys.argv) > 1:
        # Mode test d'une ligne spécifique
        if sys.argv[1] == "--test-line":
            if len(sys.argv) > 2:
                line = " ".join(sys.argv[2:])
                test_specific_line(line)
            else:
                print("Usage: python syslog_debug.py --test-line 'votre ligne de log ici'")
        else:
            syslog_path = sys.argv[1]
            analyze_syslog_file(syslog_path, last_minutes=5)
    else:
        print("\nAnalyse du fichier Syslog par défaut...")
        analyze_syslog_file(syslog_path, last_minutes=10)
    
    print("\n" + "=" * 80)
    print("💡 UTILISATION:")
    print("   python syslog_debug.py                    → Analyse les 10 dernières minutes")
    print("   python syslog_debug.py chemin/fichier     → Analyse un fichier spécifique")
    print("   python syslog_debug.py --test-line 'log'  → Teste une ligne précise")
    print("=" * 80)