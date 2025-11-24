import os
import sys
import pathlib
import django
from django.db import connection

# Ensure project root is on sys.path so Django can import the `sistema` package
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema.settings')
django.setup()

tables = [
    'amigofiel_usuariocomum',
    'amigofiel_usuarioempresarial',
    'amigofiel_usuarioong',
]

with connection.cursor() as cursor:
    for t in tables:
        # try exact name and lower-case fallback
        cursor.execute(
            "SELECT column_name, is_nullable FROM information_schema.columns WHERE table_name = %s",
            [t]
        )
        rows = cursor.fetchall()
        if not rows:
            # try lowercase
            cursor.execute(
                "SELECT column_name, is_nullable FROM information_schema.columns WHERE table_name = %s",
                [t.lower()]
            )
            rows = cursor.fetchall()
        print('\nTable:', t)
        if not rows:
            print('  (table not found)')
            continue
        found = False
        for col, nullable in rows:
            if col.lower() == 'cep':
                print(f"  column 'cep' found; is_nullable={nullable}")
                found = True
                break
        if not found:
            print('  column cep not present')

# Also list columns for context
with connection.cursor() as cursor:
    for t in tables:
        cursor.execute("SELECT column_name, is_nullable, data_type FROM information_schema.columns WHERE table_name = %s ORDER BY ordinal_position", [t])
        rows = cursor.fetchall()
        print('\nSchema for', t)
        if not rows:
            print('  (table not found)')
            continue
        for col, nullable, dtype in rows:
            print(f"  {col:30} {dtype:15} nullable={nullable}")
