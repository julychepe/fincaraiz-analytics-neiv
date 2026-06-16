import asyncio
import logging
from core.database import init_db
from core.scraper import FincaRaizScraper

# Configuración de logs para ver el avance en consola
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    logger.info("--- [Fase 4] Iniciando Recolección Volumétrica de Datos ---")
    
    # 1. Asegurar que la base de datos y sus tablas existan
    try:
        init_db()
    except Exception as e:
        logger.error(f"Error crítico al inicializar la base de datos: {e}")
        return

    # 2. Configurar el objetivo de extracción
    # Cambiamos max_pages a 10 para recolectar volumen real de apartamentos en venta en Bogotá
    BASE_URL = "https://www.fincaraiz.com.co/apartamentos/venta/bogota"
    MAX_PAGES = 10 
    
    logger.info(f"Instanciando scraper para {BASE_URL} (Páginas a recorrer: {MAX_PAGES})")
    scraper = FincaRaizScraper(base_url=BASE_URL, max_pages=MAX_PAGES)
    
    # 3. Arrancar el motor de Playwright
    try:
        await scraper.start_scraping()
        logger.info("--- Proceso de extracción masiva completado con éxito ---")
    except Exception as e:
        logger.critical(f"El scraper falló inesperadamente durante la ejecución: {e}")

if __name__ == "__main__":
    # Ejecutar el bucle asíncrono principal
    asyncio.run(main())