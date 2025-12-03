#!/usr/bin/env python
"""Generador de documentación HTML desde archivos Markdown."""

import os
import re
from pathlib import Path
from datetime import datetime

class HTMLDocGenerator:
    """Convierte documentación Markdown a HTML profesional."""
    
    def __init__(self, project_name="Estación Meteorológica"):
        self.project_name = project_name
        self.docs_dir = Path("docs/html")
        self.docs_dir.mkdir(exist_ok=True)
        
    def markdown_to_html(self, markdown_text: str) -> str:
        """Convierte Markdown básico a HTML."""
        html = markdown_text
        
        # Titles
        html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
        
        # Bold and italic
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)
        html = re.sub(r'__(.*?)__', r'<strong>\1</strong>', html)
        html = re.sub(r'_(.*?)_', r'<em>\1</em>', html)
        
        # Code
        html = re.sub(r'`(.*?)`', r'<code>\1</code>', html)
        html = re.sub(r'^```(.*?)\n(.*?)```', r'<pre><code>\2</code></pre>', html, flags=re.MULTILINE | re.DOTALL)
        
        # Links
        html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', html)
        
        # Lists
        html = re.sub(r'^- (.*?)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'^  - (.*?)$', r'  <li style="margin-left: 40px;">\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'(<li>.*?</li>)', r'<ul>\1</ul>', html, flags=re.DOTALL)
        
        # Checkboxes
        html = re.sub(r'- \[x\] ', r'<li style="list-style: none;"><input type="checkbox" checked> ', html)
        html = re.sub(r'- \[ \] ', r'<li style="list-style: none;"><input type="checkbox"> ', html)
        
        # Paragraphs
        html = re.sub(r'\n\n', r'</p><p>', html)
        html = f'<p>{html}</p>'
        
        # Tables (básico)
        html = re.sub(r'\| (.*?) \|', r'<td>\1</td>', html)
        
        return html
    
    def create_index_html(self):
        """Crea página de índice."""
        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.project_name} - Documentación</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <nav class="navbar">
        <div class="container">
            <h1 class="logo">🌤️ {self.project_name}</h1>
            <ul class="nav-menu">
                <li><a href="index.html">Inicio</a></li>
                <li><a href="readme.html">README</a></li>
                <li><a href="documentacion.html">Documentación</a></li>
                <li><a href="estado.html">Estado</a></li>
                <li><a href="changelog.html">Cambios</a></li>
            </ul>
        </div>
    </nav>

    <main class="container">
        <section class="hero">
            <h1>🌤️ Estación Meteorológica</h1>
            <p class="subtitle">Sistema ETL Incremental PostgreSQL → MinIO</p>
            <p class="version">Versión 3.0</p>
        </section>

        <section class="documentation-grid">
            <div class="doc-card">
                <h3>📖 README</h3>
                <p>Guía rápida de instalación e inicio en 4 pasos</p>
                <a href="readme.html" class="btn">Leer →</a>
            </div>
            
            <div class="doc-card">
                <h3>📚 Documentación</h3>
                <p>Referencia técnica completa con ejemplos de código</p>
                <a href="documentacion.html" class="btn">Leer →</a>
            </div>
            
            <div class="doc-card">
                <h3>📈 Estado Actual</h3>
                <p>Estado final del proyecto con funcionalidades implementadas</p>
                <a href="estado.html" class="btn">Leer →</a>
            </div>
            
            <div class="doc-card">
                <h3>📝 Changelog</h3>
                <p>Historial de cambios desde v1.0 a v3.0</p>
                <a href="changelog.html" class="btn">Leer →</a>
            </div>
        </section>

        <section class="features">
            <h2>✨ Características Principales</h2>
            <div class="features-grid">
                <div class="feature">
                    <span class="feature-icon">✅</span>
                    <h4>Extracción Incremental</h4>
                    <p>Solo extrae datos nuevos de PostgreSQL</p>
                </div>
                <div class="feature">
                    <span class="feature-icon">✅</span>
                    <h4>Limpieza Automática</h4>
                    <p>Bronce → Silver en cada ciclo</p>
                </div>
                <div class="feature">
                    <span class="feature-icon">✅</span>
                    <h4>Estrategia REPLACE</h4>
                    <p>Mantiene solo versión más reciente</p>
                </div>
                <div class="feature">
                    <span class="feature-icon">✅</span>
                    <h4>Automático 24/7</h4>
                    <p>Ejecuta cada 5 minutos sin intervención</p>
                </div>
            </div>
        </section>

        <section class="quick-start">
            <h2>🚀 Inicio Rápido</h2>
            <pre><code># 1. Clonar repositorio
git clone https://github.com/andrews0212/Estacion_Meteorologica.git

# 2. Crear entorno virtual
python -m venv venv_meteo
.\\venv_meteo\\Scripts\\Activate

# 3. Instalar dependencias
pip install pandas sqlalchemy psycopg2-binary minio

# 4. Ejecutar
python main.py</code></pre>
        </section>
    </main>

    <footer>
        <p>&copy; 2025 Estación Meteorológica. Versión 3.0 | Última actualización: {datetime.now().strftime('%d de %B de %Y')}</p>
    </footer>
</body>
</html>
"""
        with open(self.docs_dir / "index.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("✅ index.html creado")

    def create_styles_css(self):
        """Crea archivo CSS."""
        css = """* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

:root {{
    --primary-color: #0066cc;
    --secondary-color: #00c853;
    --text-color: #333;
    --light-bg: #f5f5f5;
    --border-color: #ddd;
}}

body {{
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: var(--text-color);
    line-height: 1.6;
    background-color: #fff;
}}

.container {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}}

/* Navbar */
.navbar {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem 0;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    position: sticky;
    top: 0;
    z-index: 100;
}}

.navbar .container {{
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.logo {{
    font-size: 1.8rem;
    font-weight: bold;
}}

.nav-menu {{
    display: flex;
    list-style: none;
    gap: 2rem;
}}

.nav-menu a {{
    color: white;
    text-decoration: none;
    transition: opacity 0.3s;
}}

.nav-menu a:hover {{
    opacity: 0.8;
}}

/* Main Content */
main {{
    padding: 3rem 0;
}}

.hero {{
    text-align: center;
    padding: 3rem 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 10px;
    margin-bottom: 3rem;
}}

.hero h1 {{
    font-size: 3rem;
    margin-bottom: 1rem;
}}

.subtitle {{
    font-size: 1.3rem;
    margin-bottom: 0.5rem;
}}

.version {{
    font-size: 1rem;
    opacity: 0.9;
}}

/* Cards */
.documentation-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 2rem;
    margin-bottom: 3rem;
}}

.doc-card {{
    background: white;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 2rem;
    transition: transform 0.3s, box-shadow 0.3s;
    cursor: pointer;
}}

.doc-card:hover {{
    transform: translateY(-5px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}}

.doc-card h3 {{
    color: var(--primary-color);
    margin-bottom: 1rem;
}}

.doc-card p {{
    color: #666;
    margin-bottom: 1.5rem;
}}

.btn {{
    display: inline-block;
    background: var(--primary-color);
    color: white;
    padding: 0.7rem 1.5rem;
    border-radius: 5px;
    text-decoration: none;
    transition: background 0.3s;
}}

.btn:hover {{
    background: #0052a3;
}}

/* Features */
.features {{
    margin: 3rem 0;
}}

.features h2 {{
    text-align: center;
    margin-bottom: 2rem;
    font-size: 2rem;
}}

.features-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 2rem;
}}

.feature {{
    text-align: center;
    padding: 1.5rem;
}}

.feature-icon {{
    font-size: 2.5rem;
    display: block;
    margin-bottom: 1rem;
}}

.feature h4 {{
    color: var(--primary-color);
    margin-bottom: 0.5rem;
}}

.feature p {{
    color: #666;
    font-size: 0.9rem;
}}

/* Code */
pre {{
    background: var(--light-bg);
    padding: 1.5rem;
    border-radius: 5px;
    overflow-x: auto;
    border-left: 4px solid var(--primary-color);
}}

code {{
    font-family: 'Courier New', monospace;
    background: var(--light-bg);
    padding: 0.2rem 0.4rem;
    border-radius: 3px;
}}

pre code {{
    background: none;
    padding: 0;
}}

/* Headings */
h1, h2, h3, h4, h5, h6 {{
    margin-top: 1.5rem;
    margin-bottom: 1rem;
    color: #222;
}}

h1 {{ font-size: 2.5rem; }}
h2 {{ font-size: 2rem; }}
h3 {{ font-size: 1.5rem; }}

/* Lists */
ul, ol {{
    margin-left: 2rem;
    margin-bottom: 1rem;
}}

li {{
    margin-bottom: 0.5rem;
}}

/* Tables */
table {{
    width: 100%;
    border-collapse: collapse;
    margin: 1.5rem 0;
}}

th {{
    background: var(--light-bg);
    padding: 1rem;
    text-align: left;
    border: 1px solid var(--border-color);
}}

td {{
    padding: 0.8rem;
    border: 1px solid var(--border-color);
}}

/* Footer */
footer {{
    background: var(--light-bg);
    padding: 2rem;
    text-align: center;
    margin-top: 3rem;
    border-top: 1px solid var(--border-color);
}}

/* Responsive */
@media (max-width: 768px) {{
    .hero h1 {{
        font-size: 2rem;
    }}
    
    .nav-menu {{
        flex-direction: column;
        gap: 1rem;
    }}
    
    .documentation-grid {{
        grid-template-columns: 1fr;
    }}
}}
"""
        with open(self.docs_dir / "styles.css", "w", encoding="utf-8") as f:
            f.write(css)
        print("✅ styles.css creado")

    def generate_from_markdown_file(self, md_file: str, html_file: str, title: str):
        """Genera HTML a partir de archivo Markdown."""
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Dividir contenido en secciones
            html_body = self.markdown_to_html(content)
            
            html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - {self.project_name}</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <nav class="navbar">
        <div class="container">
            <h1 class="logo">🌤️ {self.project_name}</h1>
            <ul class="nav-menu">
                <li><a href="index.html">Inicio</a></li>
                <li><a href="readme.html">README</a></li>
                <li><a href="documentacion.html">Documentación</a></li>
                <li><a href="estado.html">Estado</a></li>
                <li><a href="changelog.html">Cambios</a></li>
            </ul>
        </div>
    </nav>

    <main class="container">
        <article class="doc-content">
            {html_body}
        </article>
    </main>

    <footer>
        <p>&copy; 2025 Estación Meteorológica. Versión 3.0</p>
    </footer>
</body>
</html>
"""
            
            with open(self.docs_dir / html_file, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"✅ {html_file} creado")
            
        except FileNotFoundError:
            print(f"⚠️  {md_file} no encontrado")

    def generate_all(self):
        """Genera toda la documentación HTML."""
        print("\n" + "="*60)
        print("Generando documentación HTML...")
        print("="*60 + "\n")
        
        self.create_styles_css()
        self.create_index_html()
        
        docs = [
            ("README.md", "readme.html", "README"),
            ("DOCUMENTACION.md", "documentacion.html", "Documentación Técnica"),
            ("ESTADO_FINAL_LIMPIEZA.md", "estado.html", "Estado Final"),
            ("CHANGELOG.md", "changelog.html", "Changelog"),
        ]
        
        for md_file, html_file, title in docs:
            self.generate_from_markdown_file(md_file, html_file, title)
        
        print("\n" + "="*60)
        print(f"✅ Documentación HTML generada en: {self.docs_dir}")
        print(f"📖 Abre en navegador: {self.docs_dir / 'index.html'}")
        print("="*60 + "\n")


if __name__ == "__main__":
    generator = HTMLDocGenerator()
    generator.generate_all()
