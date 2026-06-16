import os
# --- PARCHE DE ESTABILIDAD EN WINDOWS ---
os.environ["MKL_DEBUG"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import logging
from pathlib import Path
import pandas as pd
import numpy as np
import geopandas as gpd
from sqlalchemy import create_engine, text
import statsmodels.formula.api as smf
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class PipelineEconometricoNeiva:
    def __init__(self):
        load_dotenv()
        self.root_dir = Path("c:/Users/ACER/fincaraiz_analytics")
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///data/market_data.db")
        self.engine = create_engine(self.database_url)
        self.ciudad_actual = os.getenv("CITY_LABEL", "Neiva")
        
        # Crear directorios de salida si no existen
        self.output_dir = self.root_dir / "outputs" / "reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def ejecutar_analisis_econometrico(self):
        print(f"\n--- [Fase 1: Geografía] Cargando y Cruzando {self.ciudad_actual} ---")
        
        query = """
            SELECT id, price, stratum, area_m2, latitude, longitude 
            FROM properties
            WHERE city = :ciudad
        """
        with self.engine.connect() as conn:
            df = pd.read_sql(text(query), con=conn, params={"ciudad": self.ciudad_actual})
        
        if df.empty:
            logger.error("❌ No se encontraron propiedades en la base de datos.")
            return

        # Limpieza base de coordenadas
        df_clean = df.dropna(subset=['latitude', 'longitude', 'price', 'area_m2', 'stratum']).copy()
        df_clean = df_clean[(df_clean['latitude'] != 0) & (df_clean['longitude'] != 0)]
        df_clean = df_clean[(df_clean['price'] > 0) & (df_clean['area_m2'] > 0)]
        df_clean['id_prop'] = df_clean['id'].astype(str)
        
        # Convertir a GeoDataFrame
        gdf_propiedades = gpd.GeoDataFrame(
            df_clean, 
            geometry=gpd.points_from_xy(df_clean['longitude'], df_clean['latitude']), 
            crs="EPSG:4326"
        )
        
        # Cargar comunas usando la columna que ya comprobaste ('name')
        path_comunas = self.root_dir / "data" / "comunas_neiva.shp"
        gdf_comunas = gpd.read_file(path_comunas).to_crs(epsg=4326)
        columna_num_qgis = 'name' 

        # Intersección Espacial Directa
        gdf_resultado = gpd.sjoin(gdf_propiedades, gdf_comunas[['geometry', columna_num_qgis]], how="left", predicate="within")
        
        # En lugar de borrar los que caen fuera (Palermo/Conurbano), les asignamos la comuna 11
        gdf_resultado['comuna_num'] = gdf_resultado[columna_num_qgis].fillna(11).astype(int)
        
        # Nos aseguramos de que no haya duplicados reales por ID de propiedad
        df_modelo = gdf_resultado.drop_duplicates(subset=['id_prop'], keep='first').copy()
        
        logger.info(f"📍 Inmuebles totales procesados en el modelo (incluyendo Palermo): {len(df_modelo)}")

        # Clasificación de Macro-Zonas (Ajustada para capturar correctamente la comuna 11)
        def _crear_macro_zonas(num):
            if num in [1, 2, 5]: return 'Norte_Oriente_Alto'
            elif num in [3, 4, 7]: return 'Centro_Mixto'
            elif num in [6, 8, 9, 10]: return 'Sur_Occidente_Expansion'
            else: return 'Palermo_Conurbano' # La comuna 11 (y cualquier otra externa) entra aquí

        
        df_modelo['macro_zona'] = df_modelo['comuna_num'].apply(_crear_macro_zonas)

        # =========================================================================
        print(f"\n--- [Fase 2: Econometría] Estimando Modelo OLS Hedónico ---")
        
        # Transformaciones matemáticas obligatorias para elasticidades estables
        df_modelo['log_precio'] = np.log(df_modelo['price'])
        df_modelo['log_area'] = np.log(df_modelo['area_m2'])
        
        try:
            # Planteamos el modelo controlando variables continuas y categóricas C()
            formula_ols = "log_precio ~ log_area + C(macro_zona) + C(stratum)"
            modelo_ajustado = smf.ols(formula=formula_ols, data=df_modelo).fit()
            
            # Extraemos los residuos estudentizados de la regresión
            df_modelo['residuo_est'] = modelo_ajustado.get_influence().resid_studentized_internal
            
            # Clasificamos los inmuebles del 1 al 5 según sus desvíos (Oportunidades de inversión)
            # Un residuo muy negativo significa que el inmueble cuesta mucho menos de lo que su m2, zona y estrato predicen.
            bins_residuos = [-np.inf, -2.0, -1.0, 1.0, 2.0, np.inf]
            labels_notas = [5, 4, 3, 2, 1]  # Nota 5 = Ganga del mercado / Nota 1 = Sobreprecio absurdo
            df_modelo['Nota_Regresion'] = pd.cut(df_modelo['residuo_est'], bins=bins_residuos, labels=labels_notas).astype(int)
            
            print("✅ Modelo Hedónico convergido con éxito.")
            print(f"📊 Coeficiente del Área (Elasticidad): {modelo_ajustado.params['log_area']:.4f}")
            print(f"📈 Grado de Ajuste R-squared del mercado: {modelo_ajustado.rsquared:.4f}")
            
            # Guardar reporte estadístico completo en TXT
            reporte_path = self.output_dir / "reporte_econometrico_neiva.txt"
            with open(reporte_path, "w", encoding="utf-8") as f:
                f.write(str(modelo_ajustado.summary()))
            print(f"💾 Reporte OLS detallado guardado en: {reporte_path}")

            # -------------------------------------------------------------------------
            # 💾 EXPORTAR DE NUEVO A QGIS PERO AHORA CON LAS NOTAS DE LA REGRESIÓN
            # -------------------------------------------------------------------------
            columnas_qgis = ['id_prop', 'price', 'stratum', 'area_m2', 'comuna_num', 'macro_zona', 'Nota_Regre', 'geometry']
            df_modelo['Nota_Regre'] = df_modelo['Nota_Regresion'] # Nombre corto para compatibilidad de campos Shapefile
            
            gdf_final = gpd.GeoDataFrame(df_modelo, geometry='geometry', crs="EPSG:4326")
            path_salida_shp = self.root_dir / "data" / "propiedades_econometricas.shp"
            gdf_final[columnas_qgis].to_file(path_salida_shp, driver="ESRI Shapefile")
            print(f"📍 Mapa enriquecido exportado para QGIS en: {path_salida_shp}")
            
            return df_modelo

        except Exception as e:
            logger.error(f"❌ Error crítico en el cálculo econométrico: {e}")
            return pd.DataFrame()

if __name__ == "__main__":
    pipeline = PipelineEconometricoNeiva()
    df_finalizado = pipeline.ejecutar_analisis_econometrico()