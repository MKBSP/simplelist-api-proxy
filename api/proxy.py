
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import requests
from bs4 import BeautifulSoup
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(f"Received request for path: {self.path}")  # Debug log
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

        # Parse query parameters
        query_components = parse_qs(urlparse(self.path).query)
        url = query_components.get('url', [''])[0]

        print(f"Extracted URL parameter: {url}")  # Debug log

        if not url:
            print("No URL provided")  # Debug log
            self.wfile.write(json.dumps({'error': 'URL parameter is required'}).encode())
            return

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
            }
            
            print(f"Fetching URL: {url}")  # Debug log
            response = requests.get(url, headers=headers, timeout=10)
            print(f"Response status code: {response.status_code}")  # Debug log
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for structured data first (JSON-LD)
            ingredients = []
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    data = json.loads(script.string)
                    if isinstance(data, list):
                        data = next((item for item in data if isinstance(item, dict) and item.get('@type') == 'Recipe'), None)
                    
                    if isinstance(data, dict):
                        if '@type' in data and data['@type'] == 'Recipe':
                            ingredients = data.get('recipeIngredient', [])
                            print(f"Found {len(ingredients)} ingredients in JSON-LD")  # Debug log
                            break
                        elif '@graph' in data:
                            for item in data['@graph']:
                                if item.get('@type') == 'Recipe':
                                    ingredients = item.get('recipeIngredient', [])
                                    print(f"Found {len(ingredients)} ingredients in JSON-LD @graph")  # Debug log
                                    break
                except Exception as e:
                    print(f"Error parsing JSON-LD: {str(e)}")  # Debug log
                    continue

            # Fallback to HTML parsing if no structured data found
            if not ingredients:
                print("No ingredients found in JSON-LD, falling back to HTML parsing")  # Debug log
                selectors = [
                    '.ingredients-item-name',           # AllRecipes
                    '.mntl-structured-ingredients__list-item',  # AllRecipes new
                    '.wprm-recipe-ingredient',          # WordPress Recipe Maker
                    '.recipe-ingredients li',           # Generic
                    '.ingredients-list li',             # Generic
                    '.ingredient-list li',              # Generic
                    '[itemprop="recipeIngredient"]',    # Schema.org
                    '.ingredients li',                  # Generic
                    '.recipe__ingredients li',          # Generic
                    '.recipe-ingredients__list li',     # Generic
                    '.ingredient',                      # Generic
                    '.tasty-recipes-ingredients li',    # Generic
                ]
                
                for selector in selectors:
                    elements = soup.select(selector)
                    if elements:
                        ingredients = [el.text.strip() for el in elements if el.text.strip()]
                        print(f"Found {len(ingredients)} ingredients using selector: {selector}")  # Debug log
                        break

            response_data = {
                'ingredients': ingredients,
                'status': 'success'
            }
            
            print(f"Sending response with {len(ingredients)} ingredients")  # Debug log
            self.wfile.write(json.dumps(response_data).encode())
            
        except Exception as e:
            print(f"Error occurred: {str(e)}")  # Debug log
            self.wfile.write(json.dumps({
                'error': str(e),
                'status': 'error'
            }).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
