"""
OUTIL DE DIAGNOSTIC COMPLET - AD Log Monitor Pro
Fichier : diagnostic_complet.py
USAGE : python diagnostic_complet.py
"""
import os
import sys
import time
from datetime import datetime, timedelta

# Ajouter le chemin pour importer les modules
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 80)
print("  DIAGNOSTIC COMPLET - AD LOG MONITOR PRO")
print("=" * 80)

# ============================================================================
# PROBLÈME 1 : DÉTECTION DES NOUVELLES ERREURS FORWARDEDEVENTS
# ============================================================================
print("\n🔍 PROBLÈME 1 : DÉTECTION NOUVELLES ERREURS FORWARDEDEVENTS")
print("-" * 80)

try:
    from event_reader import EventReader
    from config import LOG_FILE
    
    print(f"📂 Fichier surveillé : {LOG_FILE}")
    
    if os.path.exists(LOG_FILE):
        size_mb = os.path.getsize(LOG_FILE) / (1024 * 1024)
        mtime = datetime.fromtimestamp(os.path.getmtime(LOG_FILE))
        print(f"✅ Fichier existe : {size_mb:.2f} MB")
        print(f"📅 Dernière modification : {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Tester la lecture
        reader = EventReader()
        
        print("\n🧪 TEST 1 : Lecture des 5 dernières minutes...")
        cutoff = datetime.now() - timedelta(minutes=5)
        events_5min = reader.read_events(since_time=cutoff)
        print(f"   Résultat : {len(events_5min)} événements trouvés")
        
        print("\n🧪 TEST 2 : Lecture de la dernière heure...")
        cutoff = datetime.now() - timedelta(hours=1)
        events_1h = reader.read_events(since_time=cutoff)
        print(f"   Résultat : {len(events_1h)} événements trouvés")
        
        print("\n🧪 TEST 3 : Vérification du dernier record number...")
        last_record = reader.get_last_record_number()
        print(f"   Dernier record enregistré : #{last_record}")
        
        if last_record > 0:
            print(f"\n🧪 TEST 4 : Lecture après record #{last_record}...")
            new_events = reader.read_events(since_record=last_record)
            print(f"   Résultat : {len(new_events)} nouveaux événements")
            
            if new_events:
                print("\n📋 NOUVEAUX ÉVÉNEMENTS DÉTECTÉS :")
                for i, event in enumerate(new_events[:5], 1):
                    print(f"   [{i}] Record #{event['record_number']} - {event['source']} - Event {event['event_id']}")
            else:
                print("\n⚠️  PROBLÈME IDENTIFIÉ : Aucun nouvel événement détecté")
                print("   CAUSES POSSIBLES :")
                print("   1. Le fichier ForwardedEvents n'est pas mis à jour en temps réel")
                print("   2. Le service EventLog Forwarding n'est pas actif")
                print("   3. Les sources ne génèrent pas d'erreurs")
                print("\n   SOLUTIONS :")
                print("   • Vérifier le service Windows Event Collector (wecsvc)")
                print("   • Vérifier les abonnements Event Forwarding")
                print("   • Créer une erreur test pour vérifier la détection")
        
        # Diagnostic de rafraîchissement
        print("\n🧪 TEST 5 : Monitoring du fichier en temps réel (10 secondes)...")
        print("   Création d'une erreur test dans l'Event Viewer pour voir si elle est détectée...")
        
        initial_mtime = os.path.getmtime(LOG_FILE)
        initial_size = os.path.getsize(LOG_FILE)
        
        for i in range(10):
            time.sleep(1)
            current_mtime = os.path.getmtime(LOG_FILE)
            current_size = os.path.getsize(LOG_FILE)
            
            if current_mtime != initial_mtime or current_size != initial_size:
                print(f"\n   ✅ FICHIER MODIFIÉ après {i+1} secondes !")
                print(f"      Taille : {initial_size} → {current_size} bytes")
                break
        else:
            print("\n   ⚠️  PROBLÈME : Fichier non modifié pendant 10 secondes")
            print("   → Le fichier ForwardedEvents ne reçoit pas de nouvelles données")
    
    else:
        print(f"❌ Fichier introuvable : {LOG_FILE}")
        print("   SOLUTION : Vérifier le chemin dans config.py")

except Exception as e:
    print(f"❌ ERREUR : {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# PROBLÈME 2 : DÉTECTION ERREURS SYSLOG
# ============================================================================
print("\n\n🔍 PROBLÈME 2 : DÉTECTION ERREURS SYSLOG")
print("-" * 80)

try:
    from syslog_reader import SyslogReader
    from config import SYSLOG_PATH
    
    print(f"📂 Fichier Syslog : {SYSLOG_PATH}")
    
    if os.path.exists(SYSLOG_PATH):
        size_mb = os.path.getsize(SYSLOG_PATH) / (1024 * 1024)
        mtime = datetime.fromtimestamp(os.path.getmtime(SYSLOG_PATH))
        print(f"✅ Fichier existe : {size_mb:.2f} MB")
        print(f"📅 Dernière modification : {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Analyser le contenu
        print("\n🧪 TEST 1 : Analyse du contenu brut...")
        
        with open(SYSLOG_PATH, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        
        print(f"   Total de lignes : {len(lines)}")
        
        # Chercher les IPs surveillées
        monitored_ips = ['192.168.1.254', '192.168.1.15', '192.168.1.11']
        ip_counts = {ip: 0 for ip in monitored_ips}
        
        print(f"\n   Recherche des IPs surveillées dans le fichier...")
        for line in lines:
            for ip in monitored_ips:
                if ip in line:
                    ip_counts[ip] += 1
        
        print(f"\n   📊 RÉSULTAT DE LA RECHERCHE D'IPS :")
        for ip, count in ip_counts.items():
            icon = "✅" if count > 0 else "⚠️ "
            print(f"      {icon} {ip} : {count} ligne(s)")
        
        if sum(ip_counts.values()) == 0:
            print("\n   ❌ PROBLÈME MAJEUR : Aucune IP surveillée trouvée dans le fichier !")
            print("   CAUSES POSSIBLES :")
            print("   1. Le fichier Syslog ne contient pas les logs des équipements")
            print("   2. Les IPs dans config.py sont incorrectes")
            print("   3. Les équipements n'envoient pas leurs logs au serveur Syslog")
            print("\n   SOLUTIONS :")
            print("   • Vérifier la configuration du serveur Syslog")
            print("   • Vérifier que les équipements envoient bien leurs logs")
            print("   • Afficher quelques lignes du fichier pour analyse")
            
            print("\n   📄 ÉCHANTILLON DES 10 PREMIÈRES LIGNES :")
            for i, line in enumerate(lines[:10], 1):
                print(f"      [{i}] {line.strip()[:100]}")
        
        # Tester le parser
        print("\n\n🧪 TEST 2 : Test du parser Syslog...")
        reader = SyslogReader()
        
        parsed_count = 0
        errors_found = 0
        
        for line in lines[-100:]:  # Tester les 100 dernières lignes
            log_entry = reader.parse_syslog_line(line)
            if log_entry:
                parsed_count += 1
                priority = reader.get_event_priority(log_entry)
                if priority >= 5:
                    errors_found += 1
        
        print(f"   Lignes testées : 100 (les plus récentes)")
        print(f"   Lignes parsées avec IP surveillée : {parsed_count}")
        print(f"   Erreurs de priorité ≥5 : {errors_found}")
        
        if parsed_count == 0:
            print("\n   ❌ PROBLÈME : Parser ne reconnaît aucune ligne")
            print("   → Les logs ne correspondent pas au format attendu")
        
        # Test de lecture complète
        print("\n\n🧪 TEST 3 : Lecture complète avec le SyslogReader...")
        reader.reset()
        events = reader.read_events()
        
        print(f"   Événements détectés : {len(events)}")
        
        if events:
            print("\n   📋 DERNIERS ÉVÉNEMENTS DÉTECTÉS :")
            for i, event in enumerate(events[-5:], 1):
                priority_emoji = reader.get_priority_emoji(event['_priority'])
                print(f"   [{i}] {priority_emoji} {event['source']} - Priorité {event['_priority']}/10")
                print(f"       Message : {event['message'][:80]}...")
        else:
            print("\n   ⚠️  PROBLÈME : Aucun événement détecté après filtrage")
            print("   → Vérifier le seuil de priorité dans syslog_reader.py")
    
    else:
        print(f"❌ Fichier Syslog introuvable : {SYSLOG_PATH}")
        print("   SOLUTION : Vérifier le chemin réseau et les permissions")

except Exception as e:
    print(f"❌ ERREUR : {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# PROBLÈME 3 : OUVERTURE DES TICKETS
# ============================================================================
print("\n\n🔍 PROBLÈME 3 : OUVERTURE DES TICKETS")
print("-" * 80)

try:
    from config import OUTPUT_DIR
    
    print(f"📂 Dossier des tickets : {OUTPUT_DIR}")
    
    if os.path.exists(OUTPUT_DIR):
        print("✅ Dossier existe")
        
        # Lister les catégories
        categories = [d for d in os.listdir(OUTPUT_DIR) 
                     if os.path.isdir(os.path.join(OUTPUT_DIR, d)) and not d.startswith('.')]
        
        print(f"\n📁 Catégories trouvées : {len(categories)}")
        
        total_tickets = 0
        for category in categories:
            category_path = os.path.join(OUTPUT_DIR, category)
            ticket_count = sum(
                len([f for f in files if f.startswith('ticket_')])
                for _, _, files in os.walk(category_path)
            )
            total_tickets += ticket_count
            print(f"   • {category} : {ticket_count} ticket(s)")
        
        print(f"\n📊 TOTAL : {total_tickets} ticket(s)")
        
        if total_tickets > 0:
            print("\n🧪 TEST : Tentative d'ouverture d'un ticket...")
            
            # Trouver un ticket
            test_ticket = None
            for category in categories:
                category_path = os.path.join(OUTPUT_DIR, category)
                for root, dirs, files in os.walk(category_path):
                    for file in files:
                        if file.startswith('ticket_'):
                            test_ticket = os.path.join(root, file)
                            break
                    if test_ticket:
                        break
                if test_ticket:
                    break
            
            if test_ticket:
                print(f"   Ticket test : {test_ticket}")
                print(f"   Existe : {os.path.exists(test_ticket)}")
                
                # Tester l'ouverture
                print("\n   Tentative d'ouverture avec os.startfile()...")
                try:
                    import subprocess
                    subprocess.Popen(['notepad.exe', test_ticket])
                    print("   ✅ Ouverture réussie avec notepad")
                except Exception as e:
                    print(f"   ❌ Échec : {e}")
                    print("\n   SOLUTION :")
                    print("   • Modifier ticket_operations.py pour utiliser subprocess.Popen")
            else:
                print("   ⚠️  Aucun ticket trouvé pour tester")
        else:
            print("\n⚠️  Aucun ticket n'existe encore")
            print("   → Exécuter une analyse 24h pour créer des tickets")
    
    else:
        print(f"❌ Dossier introuvable : {OUTPUT_DIR}")

except Exception as e:
    print(f"❌ ERREUR : {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# RECOMMANDATIONS FINALES
# ============================================================================
print("\n\n" + "=" * 80)
print("  📋 RECOMMANDATIONS")
print("=" * 80)

print("""
1️⃣  DÉTECTION NOUVELLES ERREURS :
   • Vérifier que le service 'Windows Event Collector' est démarré
   • Vérifier les abonnements Event Forwarding
   • Le fichier ForwardedEvents doit être mis à jour en temps réel
   • Réduire POLLING_INTERVAL à 30 secondes pour des tests

2️⃣  DÉTECTION SYSLOG :
   • Vérifier que les équipements envoient bien leurs logs
   • Les IPs dans MONITORED_DEVICES doivent correspondre aux logs
   • Réduire le seuil de priorité dans syslog_reader.py (ligne ~218)
   • Activer le mode verbose pour voir toutes les lignes parsées

3️⃣  OUVERTURE DES TICKETS :
   • Remplacer os.startfile() par subprocess.Popen(['notepad.exe', path])
   • Ajouter un fallback si Notepad échoue
   • Vérifier les permissions d'accès aux fichiers

4️⃣  TESTS RECOMMANDÉS :
   • Créer manuellement une erreur dans Event Viewer
   • Envoyer un log test depuis un équipement réseau
   • Vérifier que la surveillance détecte ces événements
""")

print("\n" + "=" * 80)
print("  DIAGNOSTIC TERMINÉ")
print("=" * 80)
input("\nAppuyez sur ENTRÉE pour fermer...")