import os
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import geopandas as gpd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class CalculadorEntornoUrbanoNeiva:
    def __init__(self):
        load_dotenv()
        self.root_dir = Path("c:/Users/ACER/fincaraiz_analytics")
        
        # Ruta absoluta blindada para evitar el error de SQLite
        db_path = self.root_dir / "data" / "market_data.db"
        self.database_url = f"sqlite:///{db_path.as_posix()}"
        
        self.engine = create_engine(self.database_url)
        self.ciudad_actual = os.getenv("CITY_LABEL", "Neiva")

    def calcular_nota_entorno_completa(self):
        print(f"\n--- [Fase Espacial] Generando Entregable de Puntos para QGIS ({self.ciudad_actual}) ---")
        
        # 1. Cargar las propiedades desde SQLite
        query = "SELECT id, price, stratum, area_m2, latitude, longitude FROM properties WHERE city = :ciudad"
        with self.engine.connect() as conn:
            df = pd.read_sql(text(query), con=conn, params={"ciudad": self.ciudad_actual})
        
        df_clean = df.dropna(subset=['latitude', 'longitude', 'price', 'area_m2', 'stratum']).copy()
        df_clean = df_clean[(df_clean['latitude'] != 0) & (df_clean['longitude'] != 0)]
        df_clean['id_prop'] = df_clean['id'].astype(str)

        # Convertir a GeoDataFrame (Nacen en WGS84 para conservar la geometría original)
        gdf_propiedades = gpd.GeoDataFrame(
            df_clean, geometry=gpd.points_from_xy(df_clean['longitude'], df_clean['latitude']), crs="EPSG:4326"
        )
        
        # Proyectamos temporalmente a METROS para hacer la matemática de distancias de forma correcta
        gdf_propiedades_metros = gdf_propiedades.to_crs(epsg=9377)

        # 2. Cargar las 3 capas de QGIS (Asegúrate de que los nombres coincidan con tu carpeta)
        data_dir = self.root_dir / "data"
        
        try:
            gdf_vias = gpd.read_file(data_dir / "vias_principales.shp").to_crs(epsg=9377)
            gdf_cc = gpd.read_file(data_dir / "centros_comerciales.shp").to_crs(epsg=9377)
            
            # 💡 NOTA: Cambia "hospitales.shp" por el nombre exacto que tenga tu archivo en la carpeta data
            gdf_hospitales = gpd.read_file(data_dir / "hospital1.shp").to_crs(epsg=9377)
        except Exception as e:
            logger.error(f"❌ Error al cargar las capas de QGIS de la carpeta data: {e}")
            print("👉 Revisa que los archivos .shp de vías, centros comerciales y hospitales estén bien nombrados allí.")
            return

        # 3. Medición de distancias brutas en metros
        print("📏 Computando distancias métricas...")
        gdf_propiedades['dist_via'] = gdf_propiedades_metros.geometry.apply(lambda x: gdf_vias.distance(x).min())
        gdf_propiedades['dist_cc'] = gdf_propiedades_metros.geometry.apply(lambda x: gdf_cc.distance(x).min())
        gdf_propiedades['dist_hosp'] = gdf_propiedades_metros.geometry.apply(lambda x: gdf_hospitales.distance(x).min())

        # 4. Cálculo de Umbrales por Percentiles Locales
        p10_vias = gdf_propiedades['dist_via'].quantile(0.10)
        p85_vias = gdf_propiedades['dist_via'].quantile(0.85)
        p85_cc = gdf_propiedades['dist_cc'].quantile(0.85)
        p85_hosp = gdf_propiedades['dist_hosp'].quantile(0.85)

        # Algoritmo de asignación de estrellas (1 a 5)
        def evaluar_entorno(row):
            if row['dist_via'] < p10_vias:
                nota = 2  # Ruido
            elif row['dist_via'] > p85_vias:
                nota = 3  # Desconexión
            else:
                nota = 5  # Equilibrio vial
            
            if nota == 5:
                if row['dist_cc'] > p85_cc or row['dist_hosp'] > p85_hosp:
                    nota -= 1  # Castigo por lejanía de servicios (Baja a 4)
            
            if nota == 2 and (row['dist_cc'] > p85_cc or row['dist_hosp'] > p85_hosp):
                nota = 1  # Peor escenario: Ruido + Lejos de todo
                
            return nota

        gdf_propiedades['Nota_Entor'] = gdf_propiedades.apply(evaluar_entorno, axis=1)

        # =========================================================================
        # 5. GENERACIÓN DEL ENTREGABLE SHAPEFILE PARA QGIS
        # =========================================================================
        # Volvemos a dejar el GeoDataFrame original en WGS84 para que QGIS lo pinte sobre tu mapa sin descuadres
        path_entregable = data_dir / "propiedades_con_entorno.shp"
        
        # Filtramos las columnas clave (Nombres cortos de max 10 caracteres obligatorios para Shapefile)
        columnas_finales = ['id_prop', 'price', 'stratum', 'area_m2', 'dist_via', 'dist_cc', 'dist_hosp', 'Nota_Entor', 'geometry']
        
        gdf_entregable = gdf_propiedades[columnas_finales].copy()
        
        # Exportar archivo físico
        gdf_entregable.to_file(path_entregable, driver="ESRI Shapefile")
        
        print(f"\n💾 ¡Entregable cartográfico exportado con éxito!")
        print(f"📍 Capa lista para QGIS en: {path_entregable}")
        print(f"📋 Total puntos exportados: {len(gdf_entregable)}")
        print("\nMuestra de la tabla de atributos que verás en QGIS:")
        print(gdf_entregable[['id_prop', 'price', 'Nota_Entor']].head(5))
# 🚨 LA LÍNEA CRÍTICA: Retornar los datos (Alineado con los prints de arriba)
        columnas_salida = ['id_prop', 'dist_via', 'dist_cc', 'dist_hosp', 'Nota_Entor']
        return pd.DataFrame(gdf_propiedades[columnas_salida])

# --- EL BLOQUE DE PRUEBA INDEPENDIENTE ---
# (Este va pegado a la pared izquierda, sin espacios, porque está fuera de la clase)
if __name__ == "__main__":
    calculador = CalculadorEntornoUrbanoNeiva()
    calculador.calcular_nota_entorno_completa()