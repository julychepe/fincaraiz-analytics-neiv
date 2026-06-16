import asyncio
import os
import logging
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from core.scraper import FincaRaizScraper
# 🚨 REEMPLAZO CRÍTICO: Eliminamos MarketAnalyzer e importamos tu nuevo análisis unificado
from core.Analisis_final import ejecutar_pipeline_unificado_neiva

# 📌 1. CARGA DE ENTORNO E IMPORTS SEGUROS
load_dotenv()

# Ajuste de ruta absoluta para evitar fallos de VS Code con carpetas relativas
BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "outputs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Configuración del log del pipeline
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [PIPELINE] - %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "pipeline_execution.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

async def run_weekly_pipeline():
    logger.info("==================================================================")
    logger.info(f"🚀 INICIANDO PIPELINE INMOBILIARIO AUTOMÁTICO - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    logger.info("==================================================================")
    
    # 📌 2. GARANTIZAR ESTRUCTURA DE LA BASE DE DATOS
    # Como quitamos MarketAnalyzer, creamos la conexión directa a SQLite aquí para verificar la tabla
    try:
        logger.info("🗄️ Verificando estructura de la base de datos...")
        from sqlalchemy import create_engine, text
        
        # Construimos la ruta absoluta a la base de datos idéntica a tus otros scripts
        root_dir = Path("c:/Users/ACER/fincaraiz_analytics")
        db_path = root_dir / "data" / "market_data.db"
        engine = create_engine(f"sqlite:///{db_path.as_posix()}")
        
        create_properties_table_query = """
        CREATE TABLE IF NOT EXISTS properties (
            id TEXT PRIMARY KEY,
            title TEXT,
            price REAL,
            currency TEXT,
            area_m2 REAL,
            price_per_m2 REAL,
            property_type TEXT,
            contract_type TEXT,
            city TEXT,
            zone TEXT,
            address TEXT,
            latitude REAL,
            longitude REAL,
            construction_state TEXT,
            bathrooms INTEGER,
            bedrooms INTEGER,
            stratum INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        with engine.begin() as conn:
            conn.execute(text(create_properties_table_query))
        logger.info("✅ Estructura de tabla 'properties' garantizada.")
    except Exception as db_init_err:
        logger.error(f"❌ Fallo crítico preparando el entorno de la base de datos: {db_init_err}")
        return

    # 📌 3. CONFIGURACIÓN DE PARÁMETROS DE EXTRACCIÓN
    ruta_region = os.getenv("TARGET_CITY", "apartamentos/bogota")
    
    # CORRECCIÓN DE LA URL: Añadimos la barra diagonal '/' para que no se pegue con 'venta'
    if not ruta_region.startswith("/"):
        ruta_region = f"/{ruta_region}"
        
    BASE_URL = f"https://www.fincaraiz.com.co/venta{ruta_region}"
    MAX_PAGES = 10
    
    # =========================================================================
    # FASE A: EXTRAER DATOS ACTUALIZADOS (Scraping)
    # =========================================================================
    try:
        logger.info(f"🕵️‍♂️ Iniciando extracción en FincaRaíz en la URL: {BASE_URL}")
        logger.info(f"🕵️‍♂️ Páginas a rastrear: {MAX_PAGES}...")
        scraper = FincaRaizScraper(base_url=BASE_URL, max_pages=MAX_PAGES)
        await scraper.start_scraping()
        logger.info("✅ Fase de extracción completada y guardada en SQLite.")
        
    except Exception as scraper_err:
        logger.error(f"❌ Error crítico en la fase de scraping: {scraper_err}")
        # Si el scraper falla, decidimos continuar por si ya tenemos datos previos para analizar
    
    # =========================================================================
    # FASE B: NUEVA ANALÍTICA AVANZADA (Tu nuevo Analisis_final.py)
    # =========================================================================
    try:
        ciudad_actual = os.getenv("CITY_LABEL", "Neiva")
        
        if ciudad_actual.lower() == "neiva":
            logger.info("🗺️ Detectado entorno de Neiva. Disparando Analisis_final.py...")
            
            # Ejecuta tu pipeline supremo: Econometría + Distancias QGIS + Robos por Comuna
            ejecutar_pipeline_unificado_neiva()
            
            logger.info("✅ ¡Fase de Inteligencia Geográfica y Econométrica finalizada con éxito!")
            
            # 📌 FASE C: NOTIFICACIÓN AUTOMÁTICA
            logger.info("📧 Disparando notificaciones externas con las nuevas gangas...")
            from automation.notifier import send_weekly_opportunities_alert
            send_weekly_opportunities_alert()
            
        else:
            logger.warning(f"⚠️ El pipeline unificado actualmente está optimizado para Neiva. Ciudad detectada: {ciudad_actual}")
            
    except Exception as analytics_err:
        logger.error(f"❌ Error crítico en la fase de Analisis_final: {analytics_err}")

    logger.info("==================================================================")
    logger.info("🏁 PIPELINE EJECUTADO TOTALMENTE. Saliendo del proceso...")
    logger.info("==================================================================\n")

if __name__ == "__main__":
    # Arrancar el ciclo de eventos asíncronos de forma limpia
    asyncio.run(run_weekly_pipeline())