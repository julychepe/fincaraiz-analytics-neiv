import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import pandas as pd
import geopandas as gpd  # 🚨 Importante para leer el Shapefile final
from dotenv import load_dotenv

load_dotenv()

def send_weekly_opportunities_alert():
    """Busca el Shapefile final de Neiva, extrae las mejores oportunidades y las envía por correo"""
    root_dir = Path(__file__).resolve().parent.parent
    
    # 🚨 APUNTAMOS AL NUEVO ENTREGABLE SUPREMO (Leemos el archivo que genera tu Analisis_final)
    shp_path = root_dir / "data" / "MAPA_OPORTUNIDADES_NEIVA.shp"
    
    if not shp_path.exists():
        print("ℹ️ No se detectó el mapa de oportunidades de Neiva para enviar esta semana.")
        return

    # 1. Leer el mapa y convertirlo a DataFrame común para procesar el texto
    gdf = gpd.read_file(shp_path)
    if gdf.empty:
        print("ℹ️ El mapa de oportunidades está vacío. No se envía alerta.")
        return

    # 🚨 FILTRADO INTELIGENTE: Ordenamos por el Score_Fina (recuerda que QGIS lo recortó a 10 letras)
    # Traemos los inmuebles con mayor puntaje (de 5 estrellas hacia abajo)
    top_gangas = gdf.sort_values(by='Score_Fina', ascending=False).head(5)

    # 2. Construir el cuerpo del mensaje en HTML elegante
    html_content = """
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #1f77b4;">🎯 Alerta de Inteligencia Urbana: Top Oportunidades Neiva</h2>
        <p>El pipeline geo-econométrico ha identificado las propiedades con mejor balance entre precio, entorno y seguridad:</p>
        <table border="1" cellpadding="8" style="border-collapse: collapse; border-color: #ddd; width: 100%;">
            <tr style="background-color: #f2f2f2;">
                <th>Comuna</th>
                <th>Puntaje de Inversión</th>
                <th>Precio Actual</th>
                <th>Área</th>
                <th>Estrato</th>
                <th>ID Inmueble</th>
            </tr>
    """
    
    for _, row in top_gangas.iterrows():
        # Clasificamos visualmente el color de las estrellas
        score = row['Score_Fina']
        color_score = "#2ca02c" if score >= 4.0 else "#ff7f0e"
        
        # Mapeamos la comuna de forma amigable (ej: Comuna 11 es Palermo)
        comuna_label = "Palermo (Conurbano)" if int(row['comuna_num']) == 11 else f"Comuna {int(row['comuna_num'])}"
        
        html_content += f"""
            <tr>
                <td><b>{comuna_label}</b></td>
                <td style="color: {color_score}; font-weight: bold;">{score:.2f} / 5.0 ⭐</td>
                <td>${row['price']/1e6:.1f}M COP</td>
                <td>{row['area_m2']:.0f}m²</td>
                <td>Estrato {int(row['stratum'])}</td>
                <td><code>{row['id_prop']}</code></td>
            </tr>
        """
        
    html_content += """
        </table>
        <br>
        <p><i>Nota: El mapa completo con las variables de entorno (vías, hospitales y delincuencia) está listo en tu QGIS. Abre la capa <code>MAPA_OPORTUNIDADES_NEIVA.shp</code> para ver la distribución espacial.</i></p>
    </body>
    </html>
    """

    # 3. Configuración de envío SMTP (Permanece igual y seguro)
    sender_email = os.getenv("SMTP_SENDER")
    sender_password = os.getenv("SMTP_PASSWORD")
    receiver_email = os.getenv("SMTP_RECEIVER")
    
    if not all([sender_email, sender_password, receiver_email]):
        print("⚠️ Variables SMTP no configuradas en el archivo .env. Saltando envío de correo.")
        return

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"💎 ¡GANGAS GEOLOCALIZADAS NEIVA! - {len(top_gangas)} Inmuebles Destacados"
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("📧 Correo de alerta enviado exitosamente a tu bandeja de entrada.")
    except Exception as e:
        print(f"❌ No se pudo enviar la alerta por correo electrónico: {e}")

if __name__ == "__main__":
    send_weekly_opportunities_alert()