
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import requests
from bs4 import BeautifulSoup
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

        # Parse query parameters
        query_components = parse_qs(urlparse(self.path).query)
        url = query_components.get('url', [''])[0]

        if not url:
            self.wfile.write(json.dumps({'error': 'URL parameter is required'}).encode())
            return

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for structured data first (JSON-LD)
            ingredients = []
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        if '@type' in data and data['@type'] == 'Recipe':
                            ingredients = data.get('recipeIngredient', [])
                            break
                        elif '@graph' in data:
                            for item in data['@graph']:
                                if item.get('@type') == 'Recipe':
                                    ingredients = item.get('recipeIngredient', [])
                                    break
                except:
                    continue

            # Fallback to HTML parsing if no structured data found
            if not ingredients:
                selectors = [
                    '.tasty-recipes-ingredients li',
                    '.wprm-recipe-ingredient',
                    '.recipe-ingredients li',
                    '.ingredients-list li',
                    '.ingredient-list li',
                    '[itemprop="recipeIngredient"]',
                    '.ingredients li',
                    '.recipe__ingredients li',
                    '.recipe-ingredients__list li',
                    '.ingredient'
                ]
                
                for selector in selectors:
                    elements = soup.select(selector)
                    if elements:
                        ingredients = [el.text.strip() for el in elements if el.text.strip()]
                        break

            response_data = {
                'ingredients': ingredients,
                'status': 'success'
            }
            
            self.wfile.write(json.dumps(response_data).encode())
            
        except Exception as e:
            self.wfile.write(json.dumps({
                'error': str(e),
                'status': 'error'
            }).encode())
