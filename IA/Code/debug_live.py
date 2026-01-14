"""
Debug LIVE - Voir EXACTEMENT ce qui est parsé
Fichier : debug_live.py
"""
import os
from datetime import datetime, timedelta
from syslog_reader import SyslogReader


def debug_live_parsing():
    """Affiche TOUT ce qui est parsé ligne par ligne"""
    print("=" * 120)
    print("🔬 DEBUG LIVE - PARSING LIGNE PAR LIGNE")
    print("=" * 120)
    
    reader = SyslogReader(verbose=True)
    
    syslog_path = r"\\SRV-SYSLOG\surveillence$\syslog"
    
    if not os.path.exists(syslog_path):
        print(f"❌ Fichier introuvable: {syslog_path}")
        return
    
    print(f"\n✅ Fichier: {syslog_path}")
    print(f"📦 Taille: {os.path.getsize(syslog_path) / (1024*1024):.2f} MB")
    
    # Lire le fichier
    print(f"\n📖 Lecture du fichier...")
    with open(syslog_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    
    print(f"✅ {len(lines)} lignes lues")
    
    # Stats
    stats = {
        'total': 0,
        'parsed': 0,
        'failed': 0,
        'ip_match': 0,
        'ip_no_match': 0,
        'should_process': 0,
        'should_ignore': 0,
        'by_ip': {},
        'by_severity': {},
        'by_reason': {}
    }
    
    print("\n" + "=" * 120)
    print("🔍 ANALYSE LIGNE PAR LIGNE (affichage des 20 premières intéressantes)")
    print("=" * 120)
    
    displayed = 0
    max_display = 20
    
    # Analyser les 1000 dernières lignes (plus récentes)
    recent_lines = lines[-1000:] if len(lines) > 1000 else lines
    
    for i, line in enumerate(recent_lines):
        stats['total'] += 1
        
        if not line.strip():
            continue
        
        # Parser
        result = reader.parse_syslog_line(line)
        
        if result:
            stats['parsed'] += 1
            stats['ip_match'] += 1
            
            # Stats par IP
            ip = result['ip']
            stats['by_ip'][ip] = stats['by_ip'].get(ip, 0) + 1
            
            # Stats par severity
            severity = result['severity']
            stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1
            
            # Tester si doit être traité
            should_process, reason, priority = reader.should_process_log(result)
            
            if should_process:
                stats['should_process'] += 1
                
                # AFFICHER
                if displayed < max_display:
                    displayed += 1
                    print(f"\n{'─' * 120}")
                    print(f"[{displayed}] Ligne {i+1}")
                    print(f"{'─' * 120}")
                    print(f"✅ DOIT ÊTRE TRAITÉ")
                    print(f"   IP: {result['ip']} ({reader.MONITORED_DEVICES[result['ip']]['name']})")
                    print(f"   Severity: {result['severity'].upper()}")
                    print(f"   Facility: {result['facility']}")
                    print(f"   Priorité: {priority}/10")
                    print(f"   Raison: {reason}")
                    print(f"   Message: {result['message'][:100]}...")
            else:
                stats['should_ignore'] += 1
                
                # Compter les raisons d'ignorance
                stats['by_reason'][reason] = stats['by_reason'].get(reason, 0) + 1
        else:
            stats['failed'] += 1
            
            # Vérifier si contient une IP surveillée
            contains_monitored_ip = any(ip in line for ip in reader.MONITORED_DEVICES.keys())
            if contains_monitored_ip:
                stats['ip_no_match'] += 1
    
    # RÉSUMÉ
    print("\n\n" + "=" * 120)
    print("📊 RÉSUMÉ DÉTAILLÉ")
    print("=" * 120)
    
    print(f"\n1️⃣  LIGNES ANALYSÉES:")
    print(f"   Total: {stats['total']}")
    print(f"   ✅ Parsées avec succès: {stats['parsed']}")
    print(f"   ❌ Échec de parsing: {stats['failed']}")
    
    print(f"\n2️⃣  FILTRAGE:")
    print(f"   ✅ À traiter (tickets): {stats['should_process']}")
    print(f"   ❌ Ignorés: {stats['should_ignore']}")
    
    if stats['parsed'] > 0:
        ratio = (stats['should_process'] / stats['parsed']) * 100
        print(f"   📊 Taux de capture: {ratio:.1f}%")
    
    print(f"\n3️⃣  RÉPARTITION PAR IP:")
    for ip, count in sorted(stats['by_ip'].items(), key=lambda x: x[1], reverse=True):
        device_name = reader.MONITORED_DEVICES.get(ip, {}).get('name', 'Unknown')
        device_icon = reader.MONITORED_DEVICES.get(ip, {}).get('icon', '❓')
        print(f"   {device_icon} {ip} ({device_name}): {count} lignes")
    
    print(f"\n4️⃣  RÉPARTITION PAR SEVERITY:")
    severity_order = ['emerg', 'alert', 'crit', 'err', 'error', 'warning', 'warn', 'notice', 'info', 'debug']
    for sev in severity_order:
        if sev in stats['by_severity']:
            count = stats['by_severity'][sev]
            icon = "🔴" if sev in ['emerg', 'alert', 'crit', 'err', 'error'] else "🟡" if sev in ['warning', 'warn'] else "⚪"
            print(f"   {icon} {sev}: {count} lignes")
    
    print(f"\n5️⃣  RAISONS D'IGNORANCE (top 5):")
    for reason, count in sorted(stats['by_reason'].items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"   • {reason}: {count} fois")
    
    # DIAGNOSTIC
    print("\n\n" + "=" * 120)
    print("🔍 DIAGNOSTIC")
    print("=" * 120)
    
    if stats['should_process'] == 0:
        print("\n❌ PROBLÈME: AUCUN ÉVÉNEMENT CAPTURÉ!")
        print("\n🔍 Causes possibles:")
        print("   1. Toutes les severities sont 'notice' (normaux)")
        print("   2. Le filtrage est trop strict")
        print("   3. Pas de mots-clés critiques détectés")
        
        print("\n💡 SOLUTIONS:")
        print("   1. Vérifier les raisons d'ignorance ci-dessus")
        print("   2. Abaisser le seuil dans should_process_log()")
        print("   3. Ajouter plus de mots-clés critiques")
        
    elif stats['should_process'] < 10:
        print("\n⚠️  DÉTECTION FAIBLE: Seulement quelques événements capturés")
        print("\n💡 Le filtrage est peut-être trop strict")
        
    else:
        print(f"\n✅ DÉTECTION OK: {stats['should_process']} événements capturés")
        print(f"   Sur {stats['parsed']} lignes parsées avec succès")
    
    print("\n" + "=" * 120)


if __name__ == "__main__":
    print("\n🔬 DEBUG LIVE - VOIR TOUT CE QUI EST PARSÉ")
    print("=" * 120)
    print("\nCe script va:")
    print("  1. Lire les 1000 dernières lignes du Syslog")
    print("  2. Parser CHAQUE ligne")
    print("  3. Afficher les 20 premiers événements capturés")
    print("  4. Donner un résumé détaillé")
    print("  5. Diagnostic du problème")
    print("\n" + "=" * 120)
    
    input("\n▶️  Appuyez sur Entrée pour démarrer...")
    
    try:
        debug_live_parsing()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompu")
    except Exception as e:
        print(f"\n\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n\n▶️  Appuyez sur Entrée pour fermer...")