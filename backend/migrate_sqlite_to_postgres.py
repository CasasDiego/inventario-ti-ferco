#!/usr/bin/env python3
"""
Copia todos los datos de la base SQLite local a una base Postgres (Neon/Supabase).

Uso (desde backend/):
    python migrate_sqlite_to_postgres.py "postgresql://usuario:clave@host/db?sslmode=require"

Opcional: --source "sqlite:///ruta/a/jira_assets.db" (por defecto instance/jira_assets.db)
La base destino debe estar vacía; las tablas se crean automáticamente.
"""

import argparse
import os
import sys

from sqlalchemy import create_engine, func, select, text, update

from models import db

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_SOURCE = f'sqlite:///{os.path.join(BASE_DIR, "instance", "jira_assets.db")}'

# Orden que respeta las claves foráneas
TABLE_ORDER = ['users', 'asset_types', 'assets', 'asset_relations', 'asset_activities', 'sync_logs']


def normalize_url(url):
    if url.startswith('postgres://'):
        url = 'postgresql://' + url[len('postgres://'):]
    return url


def main():
    parser = argparse.ArgumentParser(description='Migrar SQLite -> Postgres')
    parser.add_argument('target', help='URL de la base Postgres destino')
    parser.add_argument('--source', default=DEFAULT_SOURCE, help='URL de la base SQLite origen')
    args = parser.parse_args()

    source = create_engine(args.source)
    target = create_engine(normalize_url(args.target))
    tables = db.metadata.tables

    db.metadata.create_all(target)

    with target.connect() as conn:
        non_empty = [t for t in TABLE_ORDER if conn.execute(select(func.count()).select_from(tables[t])).scalar()]
    if non_empty:
        print(f'La base destino ya tiene datos en: {", ".join(non_empty)}. Abortando para no duplicar.')
        sys.exit(1)

    with source.connect() as src, target.begin() as dst:
        for name in TABLE_ORDER:
            table = tables[name]
            rows = [dict(r._mapping) for r in src.execute(select(table).order_by(table.c.id))]

            if name == 'assets':
                # parent_id apunta a la misma tabla: insertar sin padre y luego enlazar
                parents = {r['id']: r['parent_id'] for r in rows if r['parent_id'] is not None}
                for r in rows:
                    r['parent_id'] = None
                if rows:
                    dst.execute(table.insert(), rows)
                for asset_id, parent_id in parents.items():
                    dst.execute(update(table).where(table.c.id == asset_id).values(parent_id=parent_id))
            elif rows:
                dst.execute(table.insert(), rows)

            # Los ids se copiaron explícitamente; ajustar la secuencia para los próximos INSERT
            dst.execute(text(
                f"SELECT setval(pg_get_serial_sequence('{name}', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM {name}), 0) + 1, false)"
            ))
            print(f'{name}: {len(rows)} filas copiadas')

    # Verificación de conteos
    ok = True
    with source.connect() as src, target.connect() as dst:
        for name in TABLE_ORDER:
            a = src.execute(select(func.count()).select_from(tables[name])).scalar()
            b = dst.execute(select(func.count()).select_from(tables[name])).scalar()
            status = 'OK' if a == b else 'DIFERENTE'
            ok = ok and a == b
            print(f'  {name}: sqlite={a} postgres={b} {status}')

    print('Migración completada.' if ok else 'ATENCIÓN: los conteos no coinciden.')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
