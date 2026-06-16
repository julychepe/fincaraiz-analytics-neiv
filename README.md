# 📍 Geo-Econometric Real Estate Intelligence Pipeline - Neiva

Welcome! This repository hosts an end-to-end automated pipeline designed to track, process, and analyze georeferenced real estate data in **Neiva, Huila (Colombia)**. 

The system integrates advanced Web Scraping, relational data warehousing, Spatial Data Science, and econometric modeling to detect pricing anomalies and uncover high-yield property investment opportunities.

---

## 🚀 Key Features

* **Intelligent Extraction:** Automated Web Scraping built with **Playwright** and **BeautifulSoup4**, optimized to bypass anti-bot systems and capture real-time market listings.
* **Geospatial Intelligence:** Spatial layer processing (city districts/comunas, main avenues, safety indices, heatmaps) combining Python (**GeoPandas**, **Shapely**) with **QGIS** cartographic projects.
* **Econometric Modeling:** Advanced statistical analysis powered by **Statsmodels** and **Scikit-Learn** to calculate the theoretical value of properties based on structural and geospatial features.
* **Automation:** An optimized task scheduling workflow designed for execution via local servers or cloud environments.

---

## 📁 Repository Structure

The project follows industry-standard software engineering practices:

* `core/`: Core system engines (`scraper.py`, `database.py`, `Analisis_final.py`).
* `data/`: Relational storage containing the SQLite database (`market_data.db`) and modeling datasets.
* `Datos_espaciales/`: Vector geometries, heatmaps, and `.qpt` print layouts for Neiva.
* `outputs/`: Automated PDF reports, execution logs (`pipeline_execution`), and analytic exports.
* `config/`: Global environment and configuration files.

---

## 🛠️ Tech Stack

* **Language:** Python 3.12
* **Database:** SQLite / SQLAlchemy (ORM)
* **Geospatial:** GeoPandas, Shapely, QGIS
* **Statistics & ML:** Statsmodels, Scikit-Learn, Pandas, NumPy
* **Reporting & Charts:** ReportLab, Matplotlib

---

## 🤝 Credits & Co-Creation

This project was developed individually, utilizing **Gemini (Google AI)** as a development and infrastructure copilot for pipeline architecture design, SQL query optimization, and technical documentation structuring.