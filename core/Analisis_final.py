# Guardado en c:/Users/ACER/fincaraiz_analytics/core/Analisis_final.py
import pandas as pd
import numpy as np
import geopandas as gpd
from core.Econometria import PipelineEconometricoNeiva
from core.Distancias import CalculadorEntornoUrbanoNeiva

def ejecutar_pipeline_unificado_neiva():
    print("🚀 Iniciando empaquetado de inteligencia urbana para Neiva...")
    
    # 1. Correr los motores
    df_econometrico = PipelineEconometricoNeiva().ejecutar_analisis_econometrico()
    df_espacial = CalculadorEntornoUrbanoNeiva().calcular_nota_entorno_completa()
    
    # 2. Unir los dos mundos
    gdf_base = gpd.GeoDataFrame(df_econometrico, geometry='geometry', crs="EPSG:4326")
    gdf_final = gdf_base.merge(df_espacial, on='id_prop', how='inner')
    
    # 3. Procesar delincuencia
    df_robos = pd.read_csv("c:/Users/ACER/fincaraiz_analytics/data/seguridad_neiva.csv")
    df_robos['comuna_num'] = df_robos['Comuna'].astype(str).str.extract(r'(\d+)').astype(float)
    
    conteo_robos = df_robos['comuna_num'].value_counts().to_frame('total_robos')
    conteo_robos['tramo_peligro'] = pd.qcut(conteo_robos['total_robos'], q=5, labels=[1, 2, 3, 4, 5]).astype(int)
    conteo_robos['castigo_seguridad'] = conteo_robos['tramo_peligro'] * 0.2
    dict_castigos = conteo_robos['castigo_seguridad'].to_dict()
    
    # 4. Calcular ponderaciones finales (60% / 40% - Castigo)
    gdf_final['castigo_robo'] = gdf_final['comuna_num'].map(dict_castigos).fillna(0.2)
    gdf_final['Score_Base'] = (gdf_final['Nota_Regre'] * 0.60) + (gdf_final['Nota_Entor'] * 0.40)
    gdf_final['Score_Final'] = (gdf_final['Score_Base'] - gdf_final['castigo_robo']).clip(1.0, 5.0)
    
    # 5. Guardar el mapa supremo para QGIS
    path_qgis_final = "c:/Users/ACER/fincaraiz_analytics/data/MAPA_OPORTUNIDADES_NEIVA.shp"
    columnas_salida = ['id_prop', 'price', 'stratum', 'area_m2', 'comuna_num', 'Nota_Regre', 'Nota_Entor', 'Score_Final', 'geometry']
    
    gdf_salida = gdf_final[columnas_salida].copy()
    gdf_salida.to_file(path_qgis_final, driver="ESRI Shapefile")
    print(f"🎯 ¡Mapa supremo listo para cargar en QGIS! -> {path_qgis_final}")

if __name__ == "__main__":
    # Permite seguir corriéndolo solo si ejecutas este archivo directamente
    ejecutar_pipeline_unificado_neiva()