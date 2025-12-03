import json
import sys
import io

# Configurar salida con UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Leer el notebook de salida de limpieza
with open('notebooks/templates/limpieza_output.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Mostrar outputs
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code' and 'outputs' in cell:
        for output in cell['outputs']:
            if output.get('output_type') == 'stream' and output.get('name') == 'stdout':
                print(''.join(output['text']), end='')
