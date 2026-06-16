import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/market_data.db")

def inspect_database():
    engine = create_engine(DATABASE_URL)
    
    # 1. Leer absolutamente todo lo que se guardó
    df = pd.read_sql("SELECT * FROM properties", con=engine)
    
    print("\n========================================================")
    print("🔍 DIAGNÓSTICO DE TU BASE DE DATOS ACTUALIZADA")
    print("========================================================\n")
    
    if df.empty:
        print("⚠️ La base de datos está vacía. Recuerda borrar la DB vieja y correr python main.py primero.")
        return

    print(f"📈 Total de registros encontrados: {len(df)} inmuebles.")
    print("-" * 50)
    
    # 2. Ver cuántos datos reales tenemos por columna
    print("📊 CONTEO DE DATOS NO NULOS POR COLUMNA:")
    print("-" * 50)
    for col in df.columns:
        no_nulos = df[col].notna().sum()
        porcentaje = (no_nulos / len(df)) * 100
        print(f"🔹 {col:<20} | Presente en: {no_nulos:<3} / {len(df)} inmuebles ({porcentaje:.1f}%)")
    
    # 3. Mostrar una muestra real enriquecida
    print("\n👀 MUESTRA DE DATOS ENRIQUECIDOS (Primeros 3 filas):")
    print("-" * 120)
    # Agregamos las nuevas columnas a la vista previa para verificar el pipeline
    columnas_vista = ['id', 'price', 'zone', 'area_m2', 'price_per_m2', 'stratum', 'bedrooms', 'bathrooms', 'latitude', 'longitude']
    # Asegurar que solo imprimimos las columnas si existen en el DataFrame
    columnas_vista = [c for c in columnas_vista if c in df.columns]
    print(df[columnas_vista].head(3).to_string(index=False))
    print("=" * 120)

if __name__ == "__main__":
    inspect_database()