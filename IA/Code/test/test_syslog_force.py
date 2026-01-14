"""
Test BRUTAL de détection Syslog
Ce script va FORCER la détection en cherchant TOUT
Fichier : test_syslog_FORCE.py
"""
import re
import os
from datetime import datetime


def test_raw_file():
    """Test ultra basique - lecture brute"""
    print("=" * 100)
    print("🔥 TEST BRUTAL - LECTURE BRUTE DU FICHIER SYSLOG")
    print("=" * 100)
    
    syslog_path = r"\\SRV-SYSLOG\surveillence$\syslog"
    
    if not os.path.exists(syslog_path):
        print(f"❌ FICHIER INTROUVABLE: {syslog_path}")
        return
    
    print(f"\n✅ Fichier trouvé: {syslog_path}")
    size_mb = os.path.getsize(syslog_path) / (1024 * 1024)
    print(f"📦 Taille: {size_mb:.2f} MB")
    
    # Lecture brute
    print("\n📖 Lecture du fichier...")
    with open(syslog_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    
    print(f"✅ {len(lines)} lignes lues")
    
    # Compter les IPs
    print("\n🔍 RECHERCHE DES IPS...")
    ips_count = {}
    
    for line in lines:
        # Chercher toutes les IPs
        ip_match = re.match(r'^(\d+\.\d+\.\d+\.\d+)', line)
        if ip_match:
            ip = ip_match.group(1)
            ips_count[ip] = ips_count.get(ip, 0) + 1
    
    print(f"\n📊 IPS TROUVÉES:")
    for ip, count in sorted(ips_count.items(), key=lambda x: x[1], reverse=True):
        print(f"   {ip}: {count} lignes")
    
    # Compter les severities
    print("\n🔍 RECHERCHE DES SEVERITIES...")
    severities = {}
    
    for line in lines:
        for sev in ['emerg', 'alert', 'crit', 'err', 'error', 'warning', 'warn', 'notice', 'info', 'debug']:
            if f' {sev} ' in line.lower() or f'\t{sev}\t' in line.lower():
                severities[sev] = severities.get(sev, 0) + 1
                break
    
    print(f"\n📊 SEVERITIES TROUVÉES:")
    for sev, count in sorted(severities.items(), key=lambda x: x[1], reverse=True):
        icon = "🔴" if sev in ['emerg', 'alert', 'crit', 'err', 'error'] else "🟡" if sev in ['warning', 'warn'] else "⚪"
        print(f"   {icon} {sev}: {count} lignes")
    
    # Afficher échantillon
    print("\n📄 ÉCHANTILLON (premières lignes avec warnings/errors):")
    count = 0
    for i, line in enumerate(lines):
        if any(sev in line.lower() for sev in ['warning', 'warn', 'alert', 'err', 'error', 'crit']):
            print(f"\n[{i+1}] {line[:150]}...")
            count += 1
            if count >= 5:
                break


def test_parser_force():
    """Test du parser avec FORCE"""
    print("\n\n" + "=" * 100)
    print("🔥 TEST BRUTAL - PARSER AVEC FORCE")
    print("=" * 100)
    
    # Importer le reader
    try:
        from syslog_reader import SyslogReader
    except ImportError:
        print("❌ Impossible d'importer SyslogReader")
        return
    
    reader = SyslogReader(verbose=True)
    
    # Modifier temporairement pour détecter TOUT
    print("\n🔧 CONFIGURATION FORCÉE:")
    print("   • Seuil de priorité: 1 (capture TOUT)")
    print("   • Mode verbose: Activé")
    
    # Test de lecture
    print("\n📖 LECTURE FORCÉE DU FICHIER...")
    
    try:
        # Lire les 2 dernières heures
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(hours=2)
        
        events = reader.read_events(since_time=cutoff, force_full_scan=True, silent=False)
        
        print(f"\n✅ RÉSULTAT: {len(events)} événements détectés")
        
        if events:
            print("\n📋 DÉTAILS DES 10 PREMIERS ÉVÉNEMENTS:")
            for i, event in enumerate(events[:10], 1):
                print(f"\n[{i}]")
                print(f"   Source: {event['source']}")
                print(f"   Priorité: {event['_priority']}/10")
                print(f"   Type: {event['event_type']}")
                print(f"   Severity: {event.get('_severity', 'N/A')}")
                print(f"   Message: {event['message'][:100]}...")
        else:
            print("\n⚠️  AUCUN ÉVÉNEMENT DÉTECTÉ!")
            print("\n🔍 DIAGNOSTIC:")
            print("   1. Le parser ne reconnaît pas le format")
            print("   2. Les IPs ne correspondent pas")
            print("   3. Le seuil de priorité est trop haut")
            
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()


def test_parse_single_line():
    """Test brutal sur UNE ligne"""
    print("\n\n" + "=" * 100)
    print("🔥 TEST BRUTAL - UNE LIGNE")
    print("=" * 100)
    
    # Ligne copiée du diagnostic
    test_line = "192.168.10.254        Jan 06 08:42:59 1       user    notice          2026-01-09T08:41:34+01:00 SN310A41KL181A7 asqd - - - "
    
    print(f"\n📄 Ligne à tester:")
    print(f"   {test_line}")
    
    # Test manuel du parsing
    print("\n🔍 ANALYSE MANUELLE:")
    
    # Split
    parts = re.split(r'\s+', test_line)
    print(f"\n1️⃣  COLONNES (split par espaces):")
    for i, part in enumerate(parts[:12]):
        print(f"   [{i}] = '{part}'")
    
    # IP
    print(f"\n2️⃣  IP (colonne 0): {parts[0]}")
    
    # Severity
    if len(parts) > 5:
        print(f"\n3️⃣  SEVERITY (colonne 5): {parts[5]}")
    
    # Test avec le reader
    print("\n4️⃣  TEST AVEC LE READER:")
    try:
        from syslog_reader import SyslogReader
        reader = SyslogReader()
        
        result = reader.parse_syslog_line(test_line)
        
        if result:
            print(f"   ✅ PARSÉ AVEC SUCCÈS!")
            print(f"   • IP: {result['ip']}")
            print(f"   • Severity: {result['severity']}")
            print(f"   • Facility: {result['facility']}")
            
            # Test priorité
            priority, indicators = reader.get_event_priority(result)
            print(f"   • Priorité: {priority}/10")
            print(f"   • Indicateurs: {', '.join(map(str, indicators))}")
            
            # Test si doit créer ticket
            should_process, reason, _ = reader.should_process_log(result)
            print(f"   • Créer ticket: {'✅ OUI' if should_process else '❌ NON'}")
            print(f"   • Raison: {reason}")
        else:
            print(f"   ❌ ÉCHEC DU PARSING")
            
    except Exception as e:
        print(f"   ❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()


def test_monitored_ips():
    """Test des IPs surveillées"""
    print("\n\n" + "=" * 100)
    print("🔥 TEST - CONFIGURATION DES IPS")
    print("=" * 100)
    
    # Lire config.py
    print("\n📖 Lecture de config.py...")
    
    try:
        from config import MONITORED_DEVICES
        
        print(f"\n📊 IPS SURVEILLÉES DANS CONFIG.PY:")
        for ip, info in MONITORED_DEVICES.items():
            print(f"   {info['icon']} {ip} - {info['name']}")
        
        # Lire syslog_reader.py
        print(f"\n📖 Lecture de syslog_reader.py...")
        from syslog_reader import SyslogReader
        reader = SyslogReader()
        
        print(f"\n📊 IPS SURVEILLÉES DANS SYSLOG_READER.PY:")
        for ip, info in reader.MONITORED_DEVICES.items():
            print(f"   {info['icon']} {ip} - {info['name']}")
        
        # Comparer
        print(f"\n🔍 COMPARAISON:")
        config_ips = set(MONITORED_DEVICES.keys())
        reader_ips = set(reader.MONITORED_DEVICES.keys())
        
        if config_ips == reader_ips:
            print(f"   ✅ Les IPs correspondent!")
        else:
            print(f"   ⚠️  Les IPs ne correspondent pas!")
            only_config = config_ips - reader_ips
            only_reader = reader_ips - config_ips
            
            if only_config:
                print(f"\n   Uniquement dans config.py:")
                for ip in only_config:
                    print(f"      • {ip}")
            
            if only_reader:
                print(f"\n   Uniquement dans syslog_reader.py:")
                for ip in only_reader:
                    print(f"      • {ip}")
        
        # Vérifier si l'IP du fichier Syslog est surveillée
        syslog_ip = "192.168.10.254"
        print(f"\n🔍 IP PRINCIPALE DU FICHIER SYSLOG: {syslog_ip}")
        
        if syslog_ip in reader.MONITORED_DEVICES:
            print(f"   ✅ Cette IP EST surveillée dans syslog_reader.py")
        else:
            print(f"   ❌ Cette IP N'EST PAS surveillée!")
            print(f"   🔧 CORRECTIF NÉCESSAIRE!")
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🔬 TEST BRUTAL DE DÉTECTION SYSLOG")
    print("=" * 100)
    print("\nCe script va:")
    print("  1. Lire brutalement le fichier Syslog")
    print("  2. Compter TOUTES les IPs et severities")
    print("  3. Tester le parser avec force")
    print("  4. Vérifier la configuration des IPs")
    print("\n" + "=" * 100)
    
    input("\n▶️  Appuyez sur Entrée pour démarrer...")
    
    try:
        # Test 1: Lecture brute
        test_raw_file()
        
        # Test 2: IPs surveillées
        test_monitored_ips()
        
        # Test 3: Parse une ligne
        test_parse_single_line()
        
        # Test 4: Parser avec force
        test_parser_force()
        
        print("\n\n" + "=" * 100)
        print("✅ TOUS LES TESTS TERMINÉS")
        print("=" * 100)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrompus")
    except Exception as e:
        print(f"\n\n❌ ERREUR GLOBALE: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n\n▶️  Appuyez sur Entrée pour fermer...")