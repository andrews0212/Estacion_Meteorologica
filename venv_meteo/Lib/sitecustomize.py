# sitecustomize.py - Runs before any imports, fixes PySpark compatibility
import sys
import types

# Fix for PySpark + Python 3.12+ compatibility
# The issue: pyspark.zip's broadcast.py tries to import from typing.io
if sys.version_info >= (3, 12):
    try:
        import typing
        from typing import BinaryIO
        
        # Create fake typing.io module
        io_module = types.ModuleType('io')
        io_module.BinaryIO = BinaryIO
        
        # Inject into typing namespace and sys.modules
        typing.io = io_module
        sys.modules['typing.io'] = io_module
    except Exception as e:
        pass
