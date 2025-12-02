# Sphinx configuration for Estacion_Meteorologica
import os
import sys
from datetime import datetime

# -- Path setup --------------------------------------------------------------
# Add the project root so Sphinx can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# -- Project information -----------------------------------------------------
project = 'EstacionMeteorologica'
author = 'autor'
release = '0.1'

def setup(app):
    pass

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

# If some dependencies (minio, pandas, psycopg2) are not installed when building
# the docs locally, mock them so autodoc can import modules.
autodoc_mock_imports = [
    'minio',
    'pandas',
    'psycopg2',
    'sqlalchemy',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Show type hints in descriptions
autodoc_typehints = 'both'

# Format for dates in generated docs
today = datetime.now().strftime('%Y-%m-%d')
