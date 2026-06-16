import asyncio
import json
import random
import logging
from bs4 import BeautifulSoup
import os
from playwright.async_api import async_playwright
from core.database import SessionLocal, upsert_property

ciudad_url = os.getenv("TARGET_CITY", "bogota")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15"
]

class FincaRaizScraper:
    def __init__(self, base_url: str, max_pages: int = 1):
        self.base_url = base_url
        self.max_pages = max_pages

    def _extract_from_search_fast(self, search_fast) -> list:
        """Extrae la lista de inmuebles del nuevo nodo searchFast de FincaRaíz"""
        if not isinstance(search_fast, dict):
            return []
        
        for key in ['properties', 'results', 'listings', 'nodes', 'data']:
            if key in search_fast and isinstance(search_fast[key], list):
                return search_fast[key]
                
        for key, val in search_fast.items():
            if isinstance(val, dict):
                sub_res = self._extract_from_search_fast(val)
                if sub_res:
                    return sub_res
        return []

    async def parse_next_data(self, html_source: str) -> list:
        """Extrae el JSON de Next.js buscando en la raíz de los resultados masivos"""
        soup = BeautifulSoup(html_source, 'html.parser')
        script_tag = soup.find('script', id='__NEXT_DATA__')
        
        parsed_properties = []
        if not script_tag:
            logger.warning("No se detectó el bloque __NEXT_DATA__ en esta página.")
            return parsed_properties

        try:
            data = json.loads(script_tag.string)
            page_props = data.get('props', {}).get('pageProps', {})
            fetch_result = page_props.get('fetchResult', {})
            
            properties_source = []

            if isinstance(fetch_result, dict):
                search_fast = fetch_result.get('searchFast', {})
                properties_source = self._extract_from_search_fast(search_fast)
                
                if not properties_source and 'properties' in fetch_result:
                    properties_source = fetch_result.get('properties', [])

            if not properties_source and isinstance(page_props, dict) and 'apolloState' in page_props:
                apollo = page_props.get('apolloState', {})
                if isinstance(apollo, dict):
                    properties_source = [
                        val for key, val in apollo.items() 
                        if isinstance(val, dict) and 'id' in val and ('title' in val or 'price' in val)
                    ]

            if not properties_source and isinstance(fetch_result, dict) and 'property' in fetch_result:
                prop_individual = fetch_result.get('property')
                if prop_individual:
                    properties_source = [prop_individual]

            logger.info(f"🎯 Bloque analizado con éxito. Procesando {len(properties_source)} elementos crudos...")

            for item in properties_source:
                if not item or not isinstance(item, dict): 
                    continue
                try:
                    prop_id = str(item.get('id', ''))
                    if not prop_id or len(prop_id) < 4: 
                        continue
                    
                    # 1. Extracción del precio
                    price_data = item.get('price', {})
                    price_val = 0.0
                    currency_val = "COP"
                    
                    if isinstance(price_data, dict):
                        price_val = float(price_data.get('amount', 0))
                        currency_val = price_data.get('currency', {}).get('name', 'COP') if 'currency' in price_data else 'COP'
                    else:
                        price_val = float(item.get('price', 0))

                    # 2. Extracción directa de la raíz para listado masivo
                    area_val = item.get('m2') or item.get('m2Built') or item.get('m2apto') or item.get('areaConstruida')
                    if area_val:
                        try:
                            clean_area = str(area_val).replace('m2', '').replace(' ', '').replace(',', '.').strip()
                            area_val = float(clean_area)
                        except Exception:
                            area_val = None

                    bathrooms_val = item.get('bathrooms') or item.get('baths') or item.get('baños')
                    bedrooms_val = item.get('bedrooms') or item.get('rooms') or item.get('habitaciones')
                    stratum_val = item.get('stratum') or item.get('estrato')
                    
                    construction_state_val = item.get('construction_state_name') or item.get('constructionState')
                    property_type_val = item.get('property_type_name') or ("Apartamento" if item.get('typeID') == 2 else "Inmueble")

                    bathrooms_val = int(float(bathrooms_val)) if bathrooms_val and str(bathrooms_val).replace('.','').replace('-','').isdigit() else None
                    bedrooms_val = int(float(bedrooms_val)) if bedrooms_val and str(bedrooms_val).replace('.','').replace('-','').isdigit() else None
                    stratum_val = int(float(stratum_val)) if stratum_val and str(stratum_val).replace('.','').replace('-','').isdigit() else None

                    # 3. Ubicación y Coordenadas (Estructura de Try/Except Corregida)
                    locations_data = item.get('locations', {})
                    zone_val = None
                    lat_val = item.get('latitude') or item.get('lat')
                    lon_val = item.get('longitude') or item.get('lng')
                    
                    if isinstance(locations_data, dict):
                        location_main = locations_data.get('location_main', {})
                        if isinstance(location_main, dict):
                            zone_val = location_main.get('name', '')
                        
                        if not lat_val or not lon_val:
                            point_string = locations_data.get('location_point', '')
                            if point_string and "POINT" in point_string:
                                try:
                                    clean_coords = point_string.replace("POINT", "").replace("(", "").replace(")", "").strip()
                                    parts = clean_coords.split()
                                    if len(parts) == 2:
                                        lon_val = float(parts[0])
                                        lat_val = float(parts[1])
                                except Exception:
                                    pass

                    prop_dict = {
                        "id": prop_id,
                        "title": item.get('title', 'Sin título'),
                        "price": price_val,
                        "currency": currency_val,
                        "area_m2": area_val,
                        "property_type": property_type_val,
                        "contract_type": "Venta",
                        "city": os.getenv("CITY_LABEL", "Bogotá"),
                        "zone": zone_val,
                        "address": item.get('address', ''),
                        "latitude": lat_val,
                        "longitude": lon_val,
                        "construction_state": str(construction_state_val) if construction_state_val else None,
                        "bathrooms": bathrooms_val,
                        "bedrooms": bedrooms_val,
                        "stratum": stratum_val
                    }
                    parsed_properties.append(prop_dict)
                except Exception as item_err:
                    logger.debug(f"Elemento omitido por inconsistencia: {item_err}")
                    continue

        except Exception as e:
            logger.error(f"Error devorando el JSON principal: {e}")
            
        return parsed_properties

    async def start_scraping(self):
        """Orquesta la navegación con Playwright y extrae los datos de las páginas"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
            page = await context.new_page()
            db_session = SessionLocal()

            try:
                for current_page in range(1, self.max_pages + 1):
                    # Paginación corregida para FincaRaíz nativa (?page=)
                    if "?" in self.base_url:
                        url = f"{self.base_url}&page={current_page}"
                    else:
                        url = f"{self.base_url}?page={current_page}"
                        
                    logger.info(f"Escaneando url: {url}")
                    
                    await page.goto(url, wait_until="networkidle", timeout=60000)
                    await asyncio.sleep(random.uniform(2, 4))
                    
                    html = await page.content()
                    properties = await self.parse_next_data(html)
                    
                    logger.info(f"Se encontraron {len(properties)} propiedades en la página {current_page}.")
                    
                    for prop in properties:
                        try:
                            upsert_property(db_session, prop)
                            logger.info(f" -> Guardado con éxito ID: {prop['id']} ({prop['title'][:25]})")
                        except Exception as db_err:
                            logger.error(f"Error guardando en DB el ID {prop.get('id')}: {db_err}")
                            
            finally:
                db_session.close()
                await context.close()
                await browser.close()