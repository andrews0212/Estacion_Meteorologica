"""Configuración Sphinx para documentación."""
import os
import sys

# Añadir ruta del proyecto
sys.path.insert(0, os.path.abspath('..'))

# Configuración del proyecto
project = 'Estación Meteorológica ETL'
copyright = '2025, Andrews0212'
author = 'Andrews0212'
release = '3.0'

# Extensiones Sphinx
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
]

# Configuración autodoc
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'show-inheritance': True,
}

# Fuente y compilación
source_suffix = '.rst'
master_doc = 'index'
language = 'es'
exclude_patterns = ['_build']

# Tema HTML
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'vcs_pageview_mode': '',
    'style_nav_header_background': '#2980B9',
}

html_static_path = ['_static']
html_logo = None
html_favicon = None

# Opciones LaTeX
latex_elements = {}

# Opciones PDF
latex_documents = [
    (master_doc, 'Estacion_Meteorologica.tex', 
     'Estación Meteorológica ETL Documentation',
     'Andrews0212', 'manual'),
]

# Opciones man
man_pages = [
    (master_doc, 'estacion_meteorologica', 
     'Estación Meteorológica ETL Documentation',
     [author], 1)
]

# Opciones texinfo
texinfo_documents = [
    (master_doc, 'Estacion_Meteorologica',
     'Estación Meteorológica ETL Documentation',
     author, 'Estacion_Meteorologica', 
     'Sistema ETL incremental',
     'Miscellaneous'),
]
