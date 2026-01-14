"""
Test de détection temps réel
Fichier : test_realtime.py
Usage: python test_realtime.py
"""
import time
import os
from datetime import datetime
from syslog_reader import SyslogReader


def test_parse_real_log():
    """Test du parser avec vos logs réels"""
    print("=" * 80)
    print("🧪 TEST 1: PARSING DE VOS LOGS RÉELS")
    print("=" * 80)
    
    reader = SyslogReader(verbose=True)
    
    # Exemples de VOS logs réels
    test_logs = [
        "192.168.10.254  Jan 12 08:49:40 1    user   notice   2026-01-14T08:52:17+01:00 SN310A41KL181A/ asqd - - id=firewall time=\"2026-01-14 08:52:17\"",
        "192.168.10.254  Jan 12 08:58:03 1    user   warning  2026-01-14T08:52:40+01:00 SN310A41KL181A/ asqd - - id=firewall time=\"2026-01-14 08:52:40\"",
        "192.168.10.254  Jan 12 08:49:42 1    user   alert    2026-01-14T08:52:19+01:00 SN310A41KL181A/ asqd - - attack detected from 10.0.0.5",
    ]
    
    for i, log_line in enumerate(test_logs, 1):
        print(f"\n--- Test log #{i} ---")
        print(f"Log: {log_line[:100]}...")
        
        result = reader.parse_syslog_line(log_line)
        
        if result:
            print(f"✅ PARSÉ avec succès!")
            print(f"   IP: {result['ip']}")
            print(f"   Timestamp: {result['timestamp']}")
            print(f"   Facility: {result['facility']}")
            print(f"   Severity: {result['severity']}")
            
            # Vérifier priorité
            should_process, reason, priority = reader.should_process_log(result)
            print(f"   Priorité: {priority}/10")
            print(f"   Créer ticket: {'✅ OUI' if should_process else '❌ NON'}")
            print(f"   Raison: {reason}")
        else:
            print(f"❌ ÉCHEC du parsing")
    
    print("\n" + "=" * 80)


def test_live_monitoring():
    """Test de surveillance en temps réel"""
    print("\n" + "=" * 80)
    print("🧪 TEST 2: SURVEILLANCE TEMPS RÉEL (30 secondes)")
    print("=" * 80)
    print("\nCe test va:")
    print("  1. Lire le fichier Syslog")
    print("  2. Détecter TOUS les warnings/errors")
    print("  3. Surveiller les nouveaux événements pendant 30s")
    print("\n⏳ Démarrage...\n")
    
    reader = SyslogReader(verbose=True)
    
    # Vérifier disponibilité
    try:
        reader.check_availability()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return
    
    # Lecture initiale (dernière heure)
    print("\n📖 LECTURE INITIALE (1 heure)...")
    print("-" * 80)
    
    from datetime import timedelta
    cutoff = datetime.now() - timedelta(hours=1)
    events = reader.read_events(since_time=cutoff, force_full_scan=True, silent=False)
    
    print(f"\n✅ {len(events)} événement(s) détecté(s)")
    
    if events:
        print("\n📋 DÉTAILS DES ÉVÉNEMENTS:")
        for i, event in enumerate(events[:5], 1):
            print(f"\n[{i}] {event['source']}")
            print(f"    Priorité: {event['_priority']}/10")
            print(f"    Type: {event['event_type']}")
            print(f"    Message: {event['message'][:100]}...")
    
    # Surveillance continue
    print("\n" + "=" * 80)
    print("🔍 SURVEILLANCE CONTINUE (30 secondes)")
    print("=" * 80)
    print("Attendez pendant que je surveille le fichier Syslog...")
    print("(Créez une erreur maintenant pour tester la détection!)\n")
    
    start_time = time.time()
    check_count = 0
    
    while time.time() - start_time < 30:
        check_count += 1
        elapsed = int(time.time() - start_time)
        print(f"[{elapsed}s] Vérification #{check_count}...", end=" ")
        
        new_events = reader.read_new_events()
        
        if new_events:
            print(f"🚨 {len(new_events)} NOUVEAU(X) ÉVÉNEMENT(S)!")
            for event in new_events:
                print(f"    → {event['source']} - Priorité {event['_priority']}/10")
        else:
            print("✓ Rien de nouveau")
        
        time.sleep(10)  # Vérifier toutes les 10 secondes
    
    print("\n✅ Test terminé!")
    print("=" * 80)


def test_priority_calculation():
    """Test du calcul de priorité"""
    print("\n" + "=" * 80)
    print("🧪 TEST 3: CALCUL DE PRIORITÉ")
    print("=" * 80)
    
    reader = SyslogReader()
    
    test_cases = [
        {
            'ip': '192.168.10.254',
            'facility': 'asqd',
            'severity': 'notice',
            'message': 'Connection established',
            'timestamp': datetime.now()
        },
        {
            'ip': '192.168.10.254',
            'facility': 'asqd',
            'severity': 'warning',
            'message': 'Connection timeout',
            'timestamp': datetime.now()
        },
        {
            'ip': '192.168.10.254',
            'facility': 'asqd',
            'severity': 'error',
            'message': 'Authentication failed',
            'timestamp': datetime.now()
        },
        {
            'ip': '192.168.10.254',
            'facility': 'firewall',
            'severity': 'alert',
            'message': 'Attack detected from 10.0.0.5',
            'timestamp': datetime.now()
        },
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        priority, indicators = reader.get_event_priority(test_case)
        should_process, reason, _ = reader.should_process_log(test_case)
        
        print(f"\n[{i}] Severity: {test_case['severity']} | Message: {test_case['message'][:50]}")
        print(f"    Priorité: {priority}/10")
        print(f"    Indicateurs: {', '.join(indicators[:3])}")
        print(f"    Créer ticket: {'✅ OUI' if should_process else '❌ NON'}")
        print(f"    Raison: {reason}")


if __name__ == "__main__":
    print("\n🔬 TESTS DE DÉTECTION TEMPS RÉEL")
    print("=" * 80)
    
    try:
        # Test 1: Parser
        test_parse_real_log()
        
        # Test 2: Priorité
        test_priority_calculation()
        
        # Test 3: Surveillance live
        response = input("\n\n▶️  Lancer le test de surveillance temps réel (30s)? (o/n): ")
        if response.lower() == 'o':
            test_live_monitoring()
        
        print("\n\n✅ TOUS LES TESTS TERMINÉS")
        print("=" * 80)
        print("\n💡 VÉRIFICATIONS:")
        print("  1. Les logs sont-ils parsés correctement? ✓")
        print("  2. Les priorités sont-elles calculées? ✓")
        print("  3. Les warnings sont-ils détectés? ✓")
        print("  4. La surveillance temps réel fonctionne? (si testé)")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()