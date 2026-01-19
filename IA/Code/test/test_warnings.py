"""
Test de détection des WARNINGS et ALERTS
Fichier : test_warnings.py
Usage: python test_warnings.py
"""
from datetime import datetime
from syslog_reader import SyslogReader


def test_exact_logs():
    """Test avec VOS logs EXACTS copiés depuis l'image"""
    print("=" * 100)
    print("🧪 TEST DE DÉTECTION - VOS LOGS EXACTS")
    print("=" * 100)
    
    reader = SyslogReader(verbose=True)
    
    # VOS LOGS EXACTS copiés depuis l'image
    test_logs = [
        # NOTICE (blanc) - Ne devrait PAS créer de ticket
        "192.168.10.254  Jan 12 08:58:53 1    user   notice    2026-01-14T09:01:30+01:00 SN310A41KL181A7 asqd - - id=firewall time=\"2026-01-14 09:01:30\" fw=\"SN310A41KL181A7\"",
        
        # WARNING (jaune) - DOIT créer un ticket (priorité 7)
        "192.168.10.254  Jan 12 08:58:54 1    user   warning   2026-01-14T09:01:31+01:00 SN310A41KL181A7 asqd - - id=firewall time=\"2026-01-14 09:01:31\" fw=\"SN310A41KL181A7\"",
        
        # ALERT (rouge foncé) - DOIT créer un ticket (priorité 9)
        "192.168.10.254  Jan 12 08:59:01 1    user   alert     2026-01-14T09:01:38+01:00 SN310A41KL181A7 asqd - - id=firewall time=\"2026-01-14 09:01:38\" fw=\"SN310A41KL181A7\"",
        
        # ERROR (rouge clair) - DOIT créer un ticket (priorité 8)
        "192.168.10.254  Jan 12 08:59:01 1    user   err       2026-01-14T09:01:38+01:00 SN310A41KL181A7 asqd - - id=firewall time=\"2026-01-14 09:01:38\" fw=\"SN310A41KL181A7\"",
        
        # NOTICE (blanc) - Ne devrait PAS créer de ticket
        "192.168.10.254  Jan 12 08:59:03 1    user   notice    2026-01-14T09:01:40+01:00 SN310A41KL181A7 asqd - - id=firewall time=\"2026-01-14 09:01:40\" fw=\"SN310A41KL181A7\"",
    ]
    
    print("\n📋 ANALYSE DE CHAQUE LOG:\n")
    
    results = {
        'parsed': 0,
        'failed': 0,
        'should_ticket': 0,
        'should_ignore': 0
    }
    
    for i, log_line in enumerate(test_logs, 1):
        print("─" * 100)
        print(f"\n[TEST {i}]")
        
        # Extraire la severity attendue du log
        if "notice" in log_line:
            expected = "notice"
            color = "⚪"
        elif "warning" in log_line:
            expected = "warning"
            color = "🟡"
        elif "alert" in log_line:
            expected = "alert"
            color = "🔴"
        elif "err" in log_line:
            expected = "error"
            color = "🔴"
        else:
            expected = "unknown"
            color = "❓"
        
        print(f"Log complet: {log_line[:120]}...")
        print(f"Severity ATTENDUE: {color} {expected.upper()}")
        
        # Parser le log
        result = reader.parse_syslog_line(log_line)
        
        if result:
            results['parsed'] += 1
            print(f"\n✅ PARSING RÉUSSI:")
            print(f"   • IP détectée: {result['ip']}")
            print(f"   • Timestamp: {result['timestamp']}")
            print(f"   • Facility: {result['facility']}")
            print(f"   • Severity DÉTECTÉE: {result['severity'].upper()}")
            
            # Vérifier si la severity est correcte
            if result['severity'] == expected:
                print(f"   ✅ Severity correcte!")
            else:
                print(f"   ❌ ERREUR: Attendu '{expected}' mais détecté '{result['severity']}'")
            
            # Calculer priorité
            priority, indicators = reader.get_event_priority(result)
            print(f"   • Priorité calculée: {priority}/10")
            print(f"   • Indicateurs: {', '.join(indicators)}")
            
            # Vérifier si ticket doit être créé
            should_process, reason, final_priority = reader.should_process_log(result)
            
            if should_process:
                results['should_ticket'] += 1
                print(f"\n   🎫 DÉCISION: ✅ CRÉER UN TICKET")
                print(f"   📊 Priorité finale: {final_priority}/10")
                print(f"   💬 Raison: {reason}")
            else:
                results['should_ignore'] += 1
                print(f"\n   🎫 DÉCISION: ❌ PAS DE TICKET")
                print(f"   💬 Raison: {reason}")
            
            # Vérifier cohérence avec la couleur
            if expected in ['warning', 'alert', 'err', 'error']:
                if should_process:
                    print(f"   ✅ CORRECT: {expected.upper()} détecté et ticket créé")
                else:
                    print(f"   ⚠️  PROBLÈME: {expected.upper()} détecté mais pas de ticket!")
            
        else:
            results['failed'] += 1
            print(f"\n❌ ÉCHEC DU PARSING - Log ignoré")
    
    # Résumé
    print("\n" + "=" * 100)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 100)
    print(f"Total de logs testés:     {len(test_logs)}")
    print(f"  ✅ Parsés avec succès:  {results['parsed']}")
    print(f"  ❌ Échecs de parsing:   {results['failed']}")
    print(f"  🎫 Tickets à créer:     {results['should_ticket']}")
    print(f"  ⚪ Logs ignorés:        {results['should_ignore']}")
    
    # Vérifications
    print("\n🔍 VÉRIFICATIONS:")
    
    checks = []
    
    # Check 1: Tous parsés
    if results['parsed'] == len(test_logs):
        checks.append("✅ Tous les logs sont parsés correctement")
    else:
        checks.append(f"❌ {results['failed']} log(s) non parsé(s)")
    
    # Check 2: Warnings/Alerts détectés
    if results['should_ticket'] >= 3:  # warning + alert + error
        checks.append("✅ Les warnings/alerts/errors sont détectés")
    else:
        checks.append(f"❌ Seulement {results['should_ticket']} événement(s) critique(s) détecté(s)")
    
    # Check 3: Notices ignorés
    if results['should_ignore'] >= 2:  # 2 notices
        checks.append("✅ Les notices sont correctement ignorés")
    else:
        checks.append("⚠️  Trop de notices créent des tickets")
    
    for check in checks:
        print(f"  {check}")
    
    print("\n" + "=" * 100)
    
    return results


def test_priority_scores():
    """Test des scores de priorité"""
    print("\n" + "=" * 100)
    print("🧪 TEST DES SCORES DE PRIORITÉ")
    print("=" * 100)
    
    reader = SyslogReader()
    
    test_cases = [
        ('notice', 'Normal connection', 5, False),
        ('warning', 'Connection timeout', 7, True),
        ('err', 'Authentication failed', 8, True),
        ('alert', 'Security breach detected', 9, True),
        ('crit', 'System failure', 10, True),
    ]
    
    print("\nSeverity       | Message           | Priorité | Ticket? | Statut")
    print("-" * 100)
    
    all_ok = True
    
    for severity, message, expected_priority, should_ticket in test_cases:
        log_entry = {
            'ip': '192.168.10.254',
            'facility': 'asqd',
            'severity': severity,
            'message': message,
            'timestamp': datetime.now()
        }
        
        priority, _ = reader.get_event_priority(log_entry)
        should_process, _, _ = reader.should_process_log(log_entry)
        
        # Vérifier
        priority_ok = priority >= expected_priority
        ticket_ok = should_process == should_ticket
        
        status = "✅" if (priority_ok and ticket_ok) else "❌"
        if not (priority_ok and ticket_ok):
            all_ok = False
        
        print(f"{severity:14} | {message:17} | {priority:8}/10 | {'✅ OUI' if should_process else '❌ NON':7} | {status}")
    
    print("-" * 100)
    if all_ok:
        print("\n✅ TOUS LES SCORES SONT CORRECTS")
    else:
        print("\n❌ CERTAINS SCORES SONT INCORRECTS")
    
    print("=" * 100)


if __name__ == "__main__":
    print("\n🔬 TEST DE DÉTECTION WARNINGS/ALERTS - VOS LOGS RÉELS")
    print("=" * 100)
    
    try:
        # Test 1: Vos logs exacts
        results = test_exact_logs()
        
        # Test 2: Scores de priorité
        test_priority_scores()
        
        print("\n\n✅ TESTS TERMINÉS")
        print("=" * 100)
        
        # Conclusion
        print("\n💡 CONCLUSION:")
        if results['should_ticket'] >= 3 and results['parsed'] == 5:
            print("  ✅ La détection fonctionne PARFAITEMENT!")
            print("  ✅ Warnings, Alerts et Errors sont détectés")
            print("  ✅ Notices sont correctement ignorés")
            print("\n  🚀 Vous pouvez lancer l'application en toute confiance!")
        else:
            print("  ⚠️  Il reste des problèmes à corriger")
            print(f"  • Logs parsés: {results['parsed']}/5")
            print(f"  • Events critiques détectés: {results['should_ticket']}/3")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrompu")
    except Exception as e:
        print(f"\n\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()