# Documentación Sphinx

## Uso Rápido

Genera y visualiza con un comando:

```powershell
.\docs.ps1 all
```

## Comandos disponibles

```powershell
.\docs.ps1 build      # Genera documentación HTML
.\docs.ps1 open       # Abre documentación en navegador
.\docs.ps1 serve      # Inicia servidor HTTP (puerto 8000)
.\docs.ps1 clean      # Elimina archivos generados
.\docs.ps1 all        # Build + Open en una línea
```

## Acceso directo

Una vez generada, abre:
```
docs/build/html/index.html
```

## Contenido

- Introducción y descripción general
- Documentación técnica completa
- API reference con código fuente
- Historial de cambios
- Estado del proyecto

---

**Nota**: Ejecuta `make docs` después de cambios en el código para actualizar la documentación.
