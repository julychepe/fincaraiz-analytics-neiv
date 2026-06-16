import os
import logging
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
import matplotlib.pyplot as plt
from dotenv import load_dotenv

# Configuración estricta de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class MarketAnalyzer:
    def __init__(self, database_url: str = None):
        """Inicializa el motor de base de datos y define las rutas relativas con pathlib"""
        load_dotenv()
        self.database_url = database_url or os.getenv("DATABASE_URL", "sqlite:///data/market_data.db")
        self.engine = create_engine(self.database_url, connect_args={"check_same_thread": False})
        
        # 📌 ASIGNACIÓN CORRECTA: Leer la ciudad del .env como atributo de la clase
        self.ciudad_actual = os.getenv("CITY_LABEL", "Bogotá")
        logger.info(f"⚙️ Analizador de Mercado inicializado para la ciudad: {self.ciudad_actual}")
        
        # Definición de rutas del ecosistema de analítica
        self.root_dir = Path(__file__).resolve().parent.parent
        self.export_dir = self.root_dir / "outputs" / "exports"
        self.report_dir = self.root_dir / "outputs" / "reports"
        
        # Garantizar la existencia de las carpetas de salida
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        # Inicializar el esquema de auditoría histórica
        self._init_history_schema()

    def _init_history_schema(self):
        """Crea la tabla de histórico de precios si no existe en el motor SQLite"""
        query = """
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id TEXT NOT NULL,
            city TEXT DEFAULT 'Bogotá',  -- Columna para separar históricos por ciudad
            zone TEXT,
            old_price REAL,
            new_price REAL,
            change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        try:
            with self.engine.begin() as conn:
                conn.execute(text(query))
        except Exception as e:
            logger.error(f"Error inicializando el esquema histórico: {e}")

    def load_clean_data(self, max_price: float = None, max_area: float = None) -> pd.DataFrame:
        """Carga datos desde SQLAlchemy aplicando filtros por ciudad y mitiga outliers"""
        
        # 📌 CORRECCIÓN 1: Filtrar el query agregando WHERE city = :ciudad
        query = """
            SELECT id, title, price, zone, area_m2, price_per_m2, stratum, bedrooms, bathrooms, updated_at 
            FROM properties
            WHERE city = :ciudad
        """
        try:
            with self.engine.connect() as conn:
                df = pd.read_sql(text(query), con=conn, params={"ciudad": self.ciudad_actual})
            
            if df.empty:
                logger.warning(f"La tabla 'properties' no tiene registros para la ciudad: {self.ciudad_actual}.")
                return pd.DataFrame()

            # Limpieza matemática obligatoria
            df_clean = df.dropna(subset=['price', 'area_m2', 'zone']).copy()
            df_clean = df_clean[(df_clean['price'] > 0) & (df_clean['area_m2'] > 0)]

            # Aplicación dinámica de filtros de acotación de mercado (Outliers)
            if max_price:
                df_clean = df_clean[df_clean['price'] <= max_price]
            if max_area:
                df_clean = df_clean[df_clean['area_m2'] <= max_area]

            # Calcular price_per_m2 si el scraper lo envió nulo
            df_clean['price_per_m2'] = df_clean['price'] / df_clean['area_m2']
            
            return df_clean

        except Exception as e:
            logger.error(f"Error crítico en la extracción y limpieza de datos: {e}")
            return pd.DataFrame()

    def audit_weekly_price_changes(self, df_current: pd.DataFrame):
        """
        Audita de forma inteligente las fluctuaciones semanales filtrando por la ciudad activa.
        """
        if df_current.empty:
            return

        try:
            # 📌 CORRECCIÓN 2: Filtrar los cambios históricos solo de la ciudad activa
            query = """
                SELECT property_id, new_price 
                FROM price_history 
                WHERE city = :ciudad AND id IN (SELECT MAX(id) FROM price_history WHERE city = :ciudad GROUP BY property_id)
            """
            with self.engine.connect() as conn:
                df_history = pd.read_sql(text(query), con=conn, params={"ciudad": self.ciudad_actual})

            changes_detected = False
            
            with self.engine.begin() as conn:
                for _, row in df_current.iterrows():
                    prop_id = row['id']
                    current_price = row['price']
                    zone = row['zone']
                    
                    # Buscar si existe registro previo en el histórico indexado
                    hist_match = df_history[df_history['property_id'] == prop_id]
                    
                    if not hist_match.empty:
                        last_price = hist_match.iloc[0]['new_price']
                        
                        if current_price != last_price:
                            variacion = ((current_price - last_price) / last_price) * 100
                            print(f"🚨 [CAMBIO DE PRECIO] ID: {prop_id:<10} | Zona: {zone:<15} | Precio Antiguo: ${last_price/1e6:.1f}M -> Precio Nuevo: ${current_price/1e6:.1f}M (Variación: {variacion:+.1f}%)")
                            
                            # 📌 CORRECCIÓN 3: Insertar guardando la ciudad correspondiente
                            conn.execute(
                                text("INSERT INTO price_history (property_id, city, zone, old_price, new_price) VALUES (:p_id, :city, :zone, :old, :new)"),
                                {"p_id": prop_id, "city": self.ciudad_actual, "zone": zone, "old": last_price, "new": current_price}
                            )
                            changes_detected = True
                    else:
                        # 📌 CORRECCIÓN 4: Al sembrar el primer registro, se le marca su ciudad real
                        conn.execute(
                            text("INSERT INTO price_history (property_id, city, zone, old_price, new_price) VALUES (:p_id, :city, :zone, :old, :new)"),
                            {"p_id": prop_id, "city": self.ciudad_actual, "zone": zone, "old": current_price, "new": current_price}
                        )

            if not changes_detected:
                print(f"ℹ️ [Tracking Histórico] No se detectaron variaciones de precio esta semana en {self.ciudad_actual}.")

        except Exception as e:
            logger.error(f"Fallo en la ejecución del módulo de tracking histórico: {e}")

    def run_statistical_analysis(self, df: pd.DataFrame):
        """Ejecuta analítica avanzada incorporando robustez estadística (Mediana y Dispersión)"""
        print(f"\n--- [Fase 5] Iniciando Análisis de Mercado Avanzado en {self.ciudad_actual}: Área vs Precio ---")
        print(f"📈 Total de registros procesados tras filtros: {len(df)} inmuebles.")
        
        # Cálculo de correlación de Pearson
        correlacion = df['area_m2'].corr(df['price'])
        print(f"🎯 Correlación matemática Área vs Precio: {correlacion:.2f}")
        
        # Agrupación e inyección de valor agregado (Mediana y Desviación Estándar)
        stats_by_zone = df.groupby('zone').agg(
            total_inmuebles=('id', 'count'),
            area_promedio_m2=('area_m2', 'mean'),
            precio_promedio_millones=('price', lambda x: x.mean() / 1e6),
            valor_m2_promedio=('price_per_m2', 'mean'),
            valor_m2_mediana=('price_per_m2', 'median'),
            valor_m2_desviacion=('price_per_m2', 'std')
        ).reset_index().sort_values(by='valor_m2_mediana', ascending=False)

        # Output formateado de nivel corporativo en Consola
        print("\n💡 RESUMEN ESTADÍSTICO DE COMPORTAMIENTO POR ZONA:")
        print("-" * 125)
        print(f"{'📍 Zona':<22} | {'Cant':<4} | {'Avg m²':<8} | {'Avg Precio':<11} | {'Avg m² COP':<14} | {'Mediana m² COP':<15} | {'Std Dev m²':<12}")
        print("-" * 125)
        for _, row in stats_by_zone.iterrows():
            std_val = f"${row['valor_m2_desviacion']:,.0f}" if pd.notna(row['valor_m2_desviacion']) else "N/A (Sufic.)"
            print(f"{row['zone']:<22} | {row['total_inmuebles']:<4} | {row['area_promedio_m2']:>6.1f}m² | ${row['precio_promedio_millones']:>7.1f}M | ${row['valor_m2_promedio']:,.0f} | ${row['valor_m2_mediana']:,.0f} | {std_val:<12}")
        print("-" * 125)

        # Exportación del reporte maestro de zonas
        csv_path = self.export_dir / "reporte_zonas_avanzado.csv"
        stats_by_zone.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"💾 Reporte macro de zonas exportado exitosamente en: {csv_path}")
        
        self._generate_scatter_plot(df)

    def _generate_scatter_plot(self, df: pd.DataFrame):
        """Genera el Scatter Plot dinámico liberando de forma segura los recursos de memoria"""
        try:
            plt.figure(figsize=(11, 6))
            
            # Gráfica de dispersión limpia utilizando la escala estandarizada en Millones
            plt.scatter(df['area_m2'], df['price'] / 1e6, alpha=0.55, c='#2ca02c', edgecolors='none', s=55)
            
            plt.title(f'Ecosistema Inmobiliario: Relación Área vs Precio ({self.ciudad_actual})', fontsize=13, fontweight='bold')
            plt.xlabel('Área Metros Cuadrados (m²)', fontsize=11)
            plt.ylabel('Precio Comercial (Millones COP)', fontsize=11)
            plt.grid(True, linestyle=':', alpha=0.6)
            
            graph_path = self.report_dir / "scatter_area_precio_optimizada.png"
            plt.savefig(graph_path, dpi=300, bbox_inches='tight')
            print(f"📊 Gráfico de dispersión generado sin sesgos en: {graph_path}")
        except Exception as e:
            logger.error(f"No se pudo renderizar el gráfico estadístico: {e}")
        finally:
            plt.close()

    def detect_market_opportunities(self, df: pd.DataFrame, threshold_pct: float = 0.15):
        """Algoritmo de la Fase 6 para el aislamiento matemático de anomalías ('Gangas')"""
        print(f"\n🕵️‍♂️ Buscando Desviaciones de Mercado en {self.ciudad_actual} (GANGAS <= -{threshold_pct*100}%) ...")
        
        if df.empty:
            return

        try:
            # Calcular la mediana por zona
            zone_medians = df.groupby('zone')['price_per_m2'].transform('median')
            
            # Computar desviación porcentual del inmueble frente a su mercado objetivo
            df_eval = df.copy()
            df_eval['zona_median_m2'] = zone_medians
            df_eval['desviacion'] = (df_eval['price_per_m2'] - df_eval['zona_median_m2']) / df_eval['zona_median_m2']
            
            # Aislamiento de registros que se encuentran severamente subvalorados
            oportunidades = df_eval[df_eval['desviacion'] <= -threshold_pct].sort_values(by='desviacion')
            
            if oportunidades.empty:
                print(f"✅ Mercado Homogéneo: No se detectaron anomalías por debajo del {threshold_pct*100}% esta semana.")
                return

            print(f"🎯 ¡Se detectaron {len(oportunidades)} GANGAS inmobiliarias en la muestra actual de {self.ciudad_actual}!")
            print("-" * 110)
            
            for _, row in oportunidades.iterrows():
                descuento = abs(row['desviacion']) * 100
                print(f"💎 [{descuento:.1f}% BAJO EL MERCADO] | Zona: {row['zone']:<15} | Valor m²: ${row['price_per_m2']/1e6:.2f}M vs Mediana: ${row['zona_median_m2']/1e6:.2f}M")
                print(f"   🏢 Inmueble: {row['title'][:60]} | Precio: ${row['price']/1e6:.1f}M | Área: {row['area_m2']}m² | ID: {row['id']}\n")
            
            # Exportación automatizada para el área de adquisiciones e inversiones
            opp_csv_path = self.export_dir / "oportunidades_inversion.csv"
            oportunidades.to_csv(opp_csv_path, index=False, encoding='utf-8-sig')
            print(f"💾 Listado de oportunidades exportado de forma táctica en: {opp_csv_path}")
            print("-" * 110)

        except Exception as e:
            logger.error(f"Error procesando el algoritmo de detección de oportunidades: {e}")

# Orquestación del Pipeline de Análisis de Datos
if __name__ == "__main__":
    analyzer = MarketAnalyzer()
    df_market = analyzer.load_clean_data(max_price=1200000000, max_area=300)
    
    if not df_market.empty:
        analyzer.audit_weekly_price_changes(df_market)
        analyzer.run_statistical_analysis(df_market)
        analyzer.detect_market_opportunities(df_market, threshold_pct=0.15)