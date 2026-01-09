"""
Test de détection des modèles Ollama
Fichier : test_ollama_models.py
"""
import requests
import json

# URLs à tester
urls = [
    "http://localhost:11434",
    "http://192.168.10.110:11434"
]

print("🔍 TEST DE DÉTECTION DES MODÈLES OLLAMA")
print("=" * 80)

for url in urls:
    print(f"\n📡 Test de {url}")
    print("-" * 80)
    
    try:
        # Test de connexion
        response = requests.get(f"{url}/api/tags", timeout=5)
        
        if response.status_code == 200:
            print(f"✅ API accessible")
            
            data = response.json()
            models = data.get('models', [])
            
            print(f"\n📦 {len(models)} modèle(s) trouvé(s):")
            
            for model in models:
                name = model.get('name', 'Unknown')
                size = model.get('size', 0) / (1024**3)  # Convertir en GB
                modified = model.get('modified_at', 'Unknown')
                
                print(f"\n   🤖 Nom exact: '{name}'")
                print(f"      Taille: {size:.2f} GB")
                print(f"      Modifié: {modified}")
                
                # Vérifier les variations de nom
                print(f"      Variations possibles:")
                print(f"        - '{name}'")
                print(f"        - '{name.split(':')[0]}'")
                if ':' in name:
                    base, tag = name.split(':', 1)
                    print(f"        - Base: '{base}', Tag: '{tag}'")
            
            # Test de génération rapide
            print(f"\n🧪 Test de génération avec le premier modèle...")
            if models:
                test_model = models[0]['name']
                print(f"   Modèle testé: {test_model}")
                
                try:
                    gen_response = requests.post(
                        f"{url}/api/generate",
                        json={
                            'model': test_model,
                            'prompt': 'Dis juste "OK"',
                            'stream': False
                        },
                        timeout=10
                    )
                    
                    if gen_response.status_code == 200:
                        result = gen_response.json().get('response', '')
                        print(f"   ✅ Génération réussie: {result[:50]}")
                    else:
                        print(f"   ⚠️ Erreur HTTP {gen_response.status_code}")
                
                except Exception as e:
                    print(f"   ❌ Erreur génération: {e}")
        else:
            print(f"❌ API répond avec code {response.status_code}")
    
    except requests.exceptions.ConnectionError:
        print(f"❌ Impossible de se connecter")
    except Exception as e:
        print(f"❌ Erreur: {e}")

print("\n" + "=" * 80)
print("\n💡 CONSEIL:")
print("   Si votre modèle s'appelle 'llama3.2:latest', utilisez:")
print("   OLLAMA_MODEL = 'llama3.2:latest'")
print("   ou simplement:")
print("   OLLAMA_MODEL = 'llama3.2'")
print("\n" + "=" * 80)

input("\nAppuyez sur ENTRÉE pour fermer...")