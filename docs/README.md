Docs para EstacionMeteorologica

Instalación mínima para generar la documentación localmente (Windows PowerShell):

1. Crear y activar un virtualenv (opcional pero recomendado):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Instalar dependencias para la documentación:

```powershell
pip install -r requirements-docs.txt
```

3. Construir la documentación HTML:

```powershell
sphinx-build -b html docs/source docs/build
```

4. Abrir `docs/build/index.html` en el navegador.
