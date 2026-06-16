import os
from pathlib import Path
import geopandas as gpd
from datetime import datetime
# Herramientas de ReportLab para armar el PDF de forma programática
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generar_pdf_inmobiliario():
    root_dir = Path(__file__).resolve().parent.parent
    shp_path = root_dir / "data" / "MAPA_OPORTUNIDADES_NEIVA.shp"
    pdf_output = root_dir / "outputs" / "reports" / "Informe_Inversion_Neiva.pdf"
    
    # 1. Leer los datos reales del mapa de Neiva
    gdf = gpd.read_file(shp_path)
    top_gangas = gdf.sort_values(by='Score_Fina', ascending=False).head(5)
    
    # 2. Configurar el documento PDF
    doc = SimpleDocTemplate(str(pdf_output), pagesize=letter,
                            rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    
    # 3. Definir Estilos de tipografía y colores corporativos (Azul Inmobiliario)
    styles = getSampleStyleSheet()
    color_primario = colors.HexColor("#1f77b4")
    
    title_style = ParagraphStyle(
        'TituloDoc', parent=styles['Heading1'],
        fontSize=22, textColor=color_primario, spaceAfter=15
    )
    h2_style = ParagraphStyle(
        'SubTituloDoc', parent=styles['Heading2'],
        fontSize=14, textColor=colors.HexColor("#333333"), spaceBefore=12, spaceAfter=8
    )
    body_style = ParagraphStyle(
        'CuerpoDoc', parent=styles['Normal'],
        fontSize=10.5, leading=14, textColor=colors.HexColor("#555555"), spaceAfter=10
    )

    # 4. Construir el contenido del Reporte
    fecha_hoy = datetime.now().strftime('%d de %B de %Y')
    story.append(Paragraph("📊 REPORTES DE INTELIGENCIA DE MERCADO INMUEBLES", title_style))
    story.append(Paragraph(f"<b>Fecha de emisión:</b> {fecha_hoy} | <b>Nodo:</b> Neiva & Palermo conurbano", body_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("1. Resumen Ejecutivo", h2_style))
    story.append(Paragraph(
        f"El presente informe expone los resultados del sistema de analítica geoespacial aplicado al mercado de Neiva. "
        f"Se procesaron un total de <b>{len(gdf)} propiedades activas</b> evaluando econometría y seguridad por comunas.", body_style
    ))
    
    story.append(Paragraph("2. Top 5: Oportunidades de Inversión Seleccionadas", h2_style))
    
    # 5. Generar la Tabla de Datos Dinámica
    tabla_datos = [[ 'Comuna', 'Score', 'Precio', 'Área', 'Estrato', 'ID' ]] # Encabezado
    
    for _, row in top_gangas.iterrows():
        comuna_idx = int(row['comuna_num'])
        comuna_lbl = "Palermo" if comuna_idx == 11 else f"Comuna {comuna_idx}"
        
        # Agregamos la fila con los datos reales que calculó tu pipeline
        tabla_datos.append([
            comuna_lbl,
            f"{row['Score_Fina']:.2f} / 5.0",
            f"${row['price']/1e6:.1f}M COP",
            f"{row['area_m2']:.0f} m²",
            f"Estrato {int(row['stratum'])}",
            str(row['id_prop'])
        ])
    
    # Diseñar la tabla con bordes y colores elegantes
    t = Table(tabla_datos, colWidths=[90, 80, 90, 70, 70, 80])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), color_primario),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f9f9f9")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#dddddd")),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    story.append(t)
    
    # 6. Construir el PDF final
    doc.build(story)
    print(f"✅ ¡PDF corporativo generado dinámicamente en: {pdf_output}!")

if __name__ == "__main__":
    generar_pdf_inmobiliario()