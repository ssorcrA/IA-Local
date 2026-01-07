"""
Recherche Web de solutions
Fichier : web_searcher.py
"""
import requests
import re
from urllib.parse import quote_plus
from config import WEB_SEARCH_ENABLED, WEB_SEARCH_TIMEOUT, MAX_WEB_RESULTS

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class WebSearcher:
    """Recherche des solutions sur le web"""
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8'
        })
        self.enabled = BS4_AVAILABLE and WEB_SEARCH_ENABLED
    
    def log(self, message):
        if self.log_callback:
            try:
                self.log_callback(message)
            except:
                print(message)
        else:
            print(message)
    
    def search(self, event):
        """Recherche des solutions pour l'erreur"""
        if not self.enabled:
            self.log("  ⚠️ Recherche web désactivée")
            return None
        
        try:
            query = f"Event ID {event['event_id']} {event['source']} solution Windows"
            search_url = f"https://www.google.com/search?q={quote_plus(query)}&hl=fr&lr=lang_fr&num=10"
            
            self.log(f"  🔍 Recherche web: {query}")
            
            response = self.session.get(search_url, timeout=WEB_SEARCH_TIMEOUT)
            
            if response.status_code != 200:
                self.log(f"  ⚠️  Recherche échouée (HTTP {response.status_code})")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                if '/url?q=' in href:
                    url = href.split('/url?q=')[1].split('&')[0]
                    
                    if 'google.com' not in url and 'youtube.com' not in url:
                        title = link.get_text(strip=True)
                        
                        if url and url.startswith('http'):
                            links.append({'url': url, 'title': title})
                            
                            if len(links) >= MAX_WEB_RESULTS:
                                break
            
            if not links:
                self.log("  ⚠️  Aucun lien trouvé")
                return None
            
            self.log(f"  ✅ {len(links)} lien(s) trouvé(s)")
            
            results = []
            for i, link_data in enumerate(links, 1):
                self.log(f"  📄 Récupération source {i}: {link_data['url'][:60]}...")
                content = self.fetch_page_content(link_data['url'])
                results.append({
                    'url': link_data['url'],
                    'title': link_data['title'],
                    'content': content
                })
            
            return self.format_results(results)
            
        except Exception as e:
            self.log(f"  ⚠️ Erreur recherche web: {e}")
            return None
    
    def fetch_page_content(self, url):
        """Récupère le contenu d'une page"""
        try:
            response = self.session.get(url, timeout=WEB_SEARCH_TIMEOUT)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
                    tag.decompose()
                
                text = soup.get_text(separator=' ', strip=True)
                text = re.sub(r'\s+', ' ', text).strip()
                
                return text[:800] + '...' if len(text) > 800 else text
            
            return "Contenu non disponible"
            
        except Exception as e:
            return f"Erreur récupération: {str(e)}"
    
    def format_results(self, results):
        """Formate les résultats de recherche"""
        formatted = "\n\n"
        
        for i, result in enumerate(results, 1):
            formatted += f"""{'='*60}
📄 SOURCE {i}: {result['title'][:80]}
🔗 {result['url']}
{'='*60}

{result['content']}

"""
        
        return formatted