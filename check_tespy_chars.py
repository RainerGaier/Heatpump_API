#!/usr/bin/env python
"""Check available TESPy characteristic components."""

import tespy
import os
import json

# Find characteristics file
tespy_path = os.path.dirname(tespy.__file__)
char_path = os.path.join(tespy_path, 'data', 'char_lines.json')
print(f'Characteristics file: {char_path}')
print(f'File exists: {os.path.exists(char_path)}')

if os.path.exists(char_path):
    with open(char_path) as f:
        data = json.load(f)

    print('\nAvailable components:')
    for comp in sorted(data.keys()):
        print(f'  - {comp}')

    print(f'\nTotal: {len(data)} components')

    if 'heat exchanger' in data:
        print('\n"heat exchanger" FOUND')
        print('Parameters:', list(data['heat exchanger'].keys()))
    else:
        print('\n"heat exchanger" NOT FOUND')
        print('Similar names:', [k for k in data.keys() if 'heat' in k.lower() or 'exchanger' in k.lower()])
else:
    print('\nCharacteristics file not found!')
    print('Checking alternate location...')

    # Try alternate location
    import tespy
    tespy_path = os.path.dirname(tespy.__file__)
    print(f'TESPy install path: {tespy_path}')

    # List files in tespy data directory
    data_path = os.path.join(tespy_path, 'data')
    if os.path.exists(data_path):
        print(f'\nFiles in {data_path}:')
        for f in os.listdir(data_path):
            print(f'  - {f}')
