"""
Script de diagnostic pour détecter POURQUOI le Stormshield n'est pas capturé
Fichier : syslog_diagnostic.py
Utilisation : python syslog_diagnostic.py
"""
import os
import re
from datetime import datetime, timedelta

# ===== CONFIGURATION =====
SYSLOG_PATH = r"\\SRV-SYSLOG\surveillence$\syslog"
STORMSHIELD_IP = "192.168.10.254"
CHECK_LAST_MINUTES = 30

def test_file_access():
    """Test 1 : Accès au fichier"""
    print("=" * 80)
    print("TEST 1 : ACCÈS AU FICHIER SYSLOG")
    print("=" * 80)
    
    if not os.path.exists(SYSLOG_PATH):
        print(f"❌ FICHIER INTROUVABLE : {SYSLOG_PATH}")
        print("\n💡 VÉRIFIEZ :")
        print("   1. Le partage réseau est accessible")
        print("   2. Vous avez les droits de lecture")
        print("   3. Le chemin est correct")
        return False
    
    print(f"✅ Fichier trouvé : {SYSLOG_PATH}")
    
    try:
        size_mb = os.path.getsize(SYSLOG_PATH) / (1024 * 1024)
        print(f"📦 Taille : {size_mb:.2f} MB")
        
        with open(SYSLOG_PATH, 'r', encoding='utf-8', errors='replace') as f:
            first_line = f.readline()
            print(f"✅ Lecture OK")
            print(f"📄 Première ligne : {first_line[:100]}...")
        
        return True
    except PermissionError:
        print("❌ ACCÈS REFUSÉ - Droits insuffisants")
        return False
    except Exception as e:
        print(f"❌ ERREUR : {e}")
        return False

def test_stormshield_detection():
    """Test 2 : Détection Stormshield"""
    print("\n" + "=" * 80)
    print("TEST 2 : DÉTECTION STORMSHIELD (192.168.10.254)")
    print("=" * 80)
    
    if not os.path.exists(SYSLOG_PATH):
        return False
    
    try:
        print(f"🔍 Recherche des {CHECK_LAST_MINUTES} dernières minutes...")
        
        with open(SYSLOG_PATH, 'r', encoding='utf-8', errors='replace') as f:
            # Lire les 5000 dernières lignes (plus rapide)
            lines = f.readlines()
            lines = lines[-5000:] if len(lines) > 5000 else lines
        
        print(f"📊 Analyse de {len(lines)} lignes...\n")
        
        stormshield_lines = []
        total_with_ip = 0
        
        for line in lines:
            # Chercher l'IP du Stormshield
            if STORMSHIELD_IP in line:
                total_with_ip += 1
                stormshield_lines.append(line.strip())
        
        print(f"📈 RÉSULTAT : {total_with_ip} lignes contenant {STORMSHIELD_IP}")
        
        if total_with_ip == 0:
            print("\n❌ AUCUNE LIGNE STORMSHIELD TROUVÉE !")
            print("\n💡 RAISONS POSSIBLES :")
            print("   1. Le Stormshield n'envoie pas de logs au serveur Syslog")
            print("   2. L'IP configurée est incorrecte")
            print("   3. Les logs sont trop anciens (> 30 min)")
            print("\n🔧 ACTION :")
            print("   1. Vérifiez la config Syslog du Stormshield")
            print("   2. Faites un test (ex: bloquer un port)")
            print("   3. Attendez 1-2 minutes et relancez ce script")
            return False
        
        print(f"\n✅ STORMSHIELD DÉTECTÉ ({total_with_ip} événements)")
        print("\n📋 EXEMPLES DE LIGNES :")
        
        # Afficher les 5 premières lignes
        for i, line in enumerate(stormshield_lines[:5], 1):
            print(f"\n[{i}] {line[:150]}{'...' if len(line) > 150 else ''}")
        
        return True
    
    except Exception as e:
        print(f"❌ ERREUR : {e}")
        return False

def test_parsing():
    """Test 3 : Parsing des lignes"""
    print("\n" + "=" * 80)
    print("TEST 3 : PARSING DES LIGNES STORMSHIELD")
    print("=" * 80)
    
    if not os.path.exists(SYSLOG_PATH):
        return False
    
    try:
        with open(SYSLOG_PATH, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            lines = lines[-5000:] if len(lines) > 5000 else lines
        
        stormshield_lines = [l for l in lines if STORMSHIELD_IP in l]
        
        if not stormshield_lines:
            print("❌ Aucune ligne à parser")
            return False
        
        print(f"🔬 Test de parsing sur {min(3, len(stormshield_lines))} lignes...\n")
        
        for i, line in enumerate(stormshield_lines[:3], 1):
            print(f"─" * 80)
            print(f"LIGNE {i} :")
            print(f"─" * 80)
            print(f"Raw : {line[:200]}\n")
            
            # Extraire composants
            parts = re.split(r'\s+', line.strip())
            
            print(f"📊 Décomposition :")
            print(f"   Colonnes détectées : {len(parts)}")
            
            if len(parts) >= 10:
                print(f"   [0] IP       : {parts[0]}")
                print(f"   [1] Mois     : {parts[1]}")
                print(f"   [2] Jour     : {parts[2]}")
                print(f"   [3] Heure    : {parts[3]}")
                print(f"   [6] Severity : {parts[6] if len(parts) > 6 else 'N/A'}")
                print(f"   [8] Hostname : {parts[8] if len(parts) > 8 else 'N/A'}")
                print(f"   [9+] Message : {' '.join(parts[9:15])}...")
            else:
                print(f"   ⚠️  Format inattendu : seulement {len(parts)} colonnes")
            
            # Détection severity
            severity_match = re.search(r'\b(emerg|alert|crit|err|error|warning|warn|notice|info|debug)\b', line, re.IGNORECASE)
            if severity_match:
                print(f"   ✅ Severity trouvée : {severity_match.group(1).upper()}")
            else:
                print(f"   ❌ Severity NON trouvée")
            
            # Score de priorité
            priority = 5  # Défaut
            if severity_match:
                sev = severity_match.group(1).lower()
                severity_scores = {
                    'emerg': 10, 'alert': 10, 'crit': 10,
                    'err': 8, 'error': 8,
                    'warning': 7, 'warn': 7,
                    'notice': 6, 'info': 3
                }
                priority = severity_scores.get(sev, 5)
            
            # Mots-clés
            keywords = ['fail', 'error', 'deny', 'drop', 'block', 'alert', 'attack', 'alarm']
            found_keywords = [kw for kw in keywords if kw in line.lower()]
            
            if found_keywords:
                print(f"   🔑 Mots-clés : {', '.join(found_keywords)}")
                priority = max(priority, 7)
            
            print(f"   🎯 PRIORITÉ CALCULÉE : {priority}/10")
            
            # Verdict
            MIN_THRESHOLD = 5  # Depuis config.py
            if priority >= MIN_THRESHOLD:
                print(f"   ✅ DEVRAIT CRÉER UN TICKET (seuil = {MIN_THRESHOLD})")
            else:
                print(f"   ❌ SERA IGNORÉ (priorité {priority} < seuil {MIN_THRESHOLD})")
            
            print()
        
        return True
    
    except Exception as e:
        print(f"❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app_detection():
    """Test 4 : Vérifier si l'app détecte (SANS NOTICE)"""
    print("\n" + "=" * 80)
    print("TEST 4 : SIMULATION APP (FILTRE NOTICE)")
    print("=" * 80)
    
    print("\n🔧 Import des modules de l'app...")
    
    try:
        from syslog_reader import SyslogReader
        
        print("✅ Modules importés")
        
        # Créer lecteur
        reader = SyslogReader(log_callback=print, verbose=True)
        
        print("\n🔍 Test de lecture des 2 dernières heures...")
        events = reader.read_initial_check(hours=2)
        
        print(f"\n📊 RÉSULTAT BRUT : {len(events)} événements détectés")
        
        if events:
            # Filtrer Stormshield
            stormshield_events = [e for e in events if STORMSHIELD_IP in e.get('_device_ip', '')]
            
            print(f"🔥 Dont {len(stormshield_events)} depuis Stormshield")
            
            # FILTRE : Supprimer les NOTICE
            stormshield_no_notice = [
                e for e in stormshield_events 
                if e.get('_severity', '').lower() != 'notice'
            ]
            
            notice_count = len(stormshield_events) - len(stormshield_no_notice)
            
            print(f"ℹ️  {notice_count} NOTICE ignorées (infos)")
            print(f"⚠️  {len(stormshield_no_notice)} événements IMPORTANTS")
            
            if stormshield_no_notice:
                print("\n✅ ÉVÉNEMENTS À TRAITER :")
                
                # Stats par severity
                severity_counts = {}
                for e in stormshield_no_notice:
                    sev = e.get('_severity', 'unknown').upper()
                    severity_counts[sev] = severity_counts.get(sev, 0) + 1
                
                print("\n📊 Répartition :")
                for sev, count in sorted(severity_counts.items(), reverse=True):
                    print(f"   {sev}: {count}")
                
                print("\n📋 Exemples :")
                for i, event in enumerate(stormshield_no_notice[:5], 1):
                    sev = event.get('_severity', 'N/A').upper()
                    priority = event.get('_priority', 'N/A')
                    print(f"\n[{i}] Severity: {sev} | Priorité: {priority}/10")
                    print(f"    Source: {event.get('source', 'N/A')}")
                    print(f"    Message: {event.get('message', '')[:100]}...")
            else:
                print("\n⚠️  AUCUN ÉVÉNEMENT IMPORTANT (que des NOTICE)")
                print("\n💡 C'est normal si pas d'erreur récente")
                print("   → Les NOTICE ne créent pas de tickets")
        else:
            print("\n❌ AUCUN ÉVÉNEMENT DÉTECTÉ")
            print("\n💡 CAUSES POSSIBLES :")
            print("   1. Pas d'événements dans les 2 dernières heures")
            print("   2. Le seuil de priorité filtre tout")
            print("   3. Le parsing échoue silencieusement")
    
    except ImportError as e:
        print(f"❌ Impossible d'importer les modules : {e}")
        print("\n💡 Assurez-vous d'être dans le bon dossier (C:\\IA\\Code)")
        return False
    except Exception as e:
        print(f"❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Exécution complète des tests"""
    print("\n" + "=" * 80)
    print("🔬 DIAGNOSTIC STORMSHIELD - DÉTECTION DES PROBLÈMES")
    print("=" * 80)
    print(f"📁 Fichier Syslog : {SYSLOG_PATH}")
    print(f"🔥 IP Stormshield : {STORMSHIELD_IP}")
    print(f"⏰ Fenêtre : {CHECK_LAST_MINUTES} dernières minutes")
    print("=" * 80)
    
    # Test 1
    if not test_file_access():
        print("\n❌ ARRÊT : Fichier Syslog inaccessible")
        return
    
    # Test 2
    if not test_stormshield_detection():
        print("\n⚠️  Le Stormshield n'envoie pas de logs récents")
        print("   Impossible de continuer les tests")
        return
    
    # Test 3
    test_parsing()
    
    # Test 4
    test_app_detection()
    
    print("\n" + "=" * 80)
    print("✅ DIAGNOSTIC TERMINÉ")
    print("=" * 80)
    print("\n💡 PROCHAINES ÉTAPES :")
    print("   1. Si Stormshield détecté → Vérifier le seuil MIN_PRIORITY_THRESHOLD")
    print("   2. Si parsing échoue → Copier/coller une ligne ici pour analyse")
    print("   3. Si app ne détecte pas → Vérifier MONITORED_DEVICES dans config.py")

if __name__ == "__main__":
    main()