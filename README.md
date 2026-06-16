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

---

## 🚀 Future Roadmap & Improvements

Looking to scale this pipeline? Here are some features planned for future releases:
* **Cloud Deployment:** Migrating the local pipeline to AWS (Lambda/RDS) or Google Cloud Platform.
* **Interactive Dashboard:** Building a **Streamlit** or **Dash** web interface to visualize real-time real estate heatmaps.
* **Advanced Machine Learning:** Implementing XGBoost or Random Forest models to improve price prediction accuracy over standard econometric models.

---

## 🤝 Contributing & Feedback

Contributions, issues, and feature requests are more than welcome! 
If you have ideas on how to improve the web scraper, optimize the spatial queries, or refine the statistical models, feel free to:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/AmazingImprovement`).
3. Open a **Pull Request** or submit an **Issue**.

---

## 📩 Contact & Collaboration

If you are a real estate investor, a data enthusiast, or a recruiter interested in data-driven geospatial pipelines, let's connect! You can reach me through:

* **LinkedIn:** https://www.linkedin.com/in/julian-david-ortiz-uma%C3%B1a-765009158/
* **Email:** j.david.9504@gmail.com
