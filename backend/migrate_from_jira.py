#!/usr/bin/env python3
"""
migrate_from_jira.py - Migración completa de Jira Assets a Ferco Medical Platform
Estrategia: obtener todos los IDs via múltiples queries AQL con filtros de fecha,
luego descargar cada objeto individualmente via GET /object/{id}
"""

import sqlite3, json, os, time, requests, urllib3
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

DB_PATH = r"C:\Users\temporal\Desktop\JIRA\backend\instance\jira_assets.db"
EMAIL   = os.getenv('JIRA_EMAIL')
TOKEN   = os.getenv('JIRA_TOKEN')
WID     = os.getenv('JIRA_WORKSPACE_ID')
BASE    = f"https://api.atlassian.com/jsm/assets/workspace/{WID}/v1"

S = requests.Session()
S.auth = (EMAIL, TOKEN)
S.headers.update({'Accept': 'application/json', 'Content-Type': 'application/json'})
S.verify = os.getenv('JIRA_VERIFY_SSL', 'false').lower() in {'1', 'true', 'yes'}
if not S.verify:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def init_db(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS asset_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jira_type_id VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            description TEXT DEFAULT '',
            icon VARCHAR(255) DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jira_key VARCHAR(50) NOT NULL,
            jira_id VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            type_id INTEGER NOT NULL REFERENCES asset_types(id),
            attributes TEXT DEFAULT '{}',
            parent_id INTEGER REFERENCES assets(id),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            jira_created_at DATETIME,
            jira_updated_at DATETIME
        );
        CREATE TABLE IF NOT EXISTS asset_relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jira_relation_id VARCHAR(255),
            source_asset_id INTEGER NOT NULL REFERENCES assets(id),
            target_asset_id INTEGER NOT NULL REFERENCES assets(id),
            relation_type VARCHAR(100) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS sync_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sync_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(50) DEFAULT 'pending',
            total_assets INTEGER DEFAULT 0,
            total_relations INTEGER DEFAULT 0,
            error_message TEXT,
            duration_seconds REAL
        );
    """)
    conn.commit()


def get_attr_map():
    r = S.get(f"{BASE}/objectschema/2/attributes", timeout=15)
    r.raise_for_status()
    data = r.json()
    vals = data.get('values', data) if isinstance(data, dict) else data
    return {str(a['id']): a['name'] for a in vals}


def get_all_ids_by_date_ranges():
    """
    Obtiene todos los IDs del schema usando queries AQL por rangos de fecha.
    La API limita a 25 por query pero podemos hacer muchas queries con filtros distintos.
    """
    all_ids = set()

    # Rango de fechas: desde el primer objeto hasta hoy, en ventanas de 7 días
    start_date = datetime(2024, 5, 1)
    end_date = datetime(2026, 12, 31)
    window = timedelta(days=7)

    current = start_date
    total_queries = 0

    print("  Obteniendo IDs por rangos de fecha...")
    while current <= end_date:
        next_date = current + window
        date_from = current.strftime('%Y-%m-%d')
        date_to = next_date.strftime('%Y-%m-%d')

        r = S.post(f"{BASE}/object/aql", json={
            'qlQuery': f'objectSchemaId = 2 AND created >= "{date_from}" AND created < "{date_to}"',
            'maxResults': 25,
            'startAt': 0,
            'includeAttributes': False
        }, timeout=30)

        if r.status_code == 200:
            data = r.json()
            batch_ids = [o['id'] for o in data.get('values', [])]
            new_ids = set(batch_ids) - all_ids
            all_ids.update(new_ids)
            total = data.get('total', 0)
            if new_ids:
                print(f"  {date_from} a {date_to}: {len(new_ids)} nuevos IDs (total acum: {len(all_ids)})")

            # Si hay exactamente 25, puede haber más en ese rango — dividir en ventanas más pequeñas
            if total and total >= 25:
                # Subdividir en días individuales
                for day_offset in range(7):
                    day = current + timedelta(days=day_offset)
                    next_day = day + timedelta(days=1)
                    r2 = S.post(f"{BASE}/object/aql", json={
                        'qlQuery': f'objectSchemaId = 2 AND created >= "{day.strftime("%Y-%m-%d")}" AND created < "{next_day.strftime("%Y-%m-%d")}"',
                        'maxResults': 25,
                        'startAt': 0,
                        'includeAttributes': False
                    }, timeout=30)
                    if r2.status_code == 200:
                        day_ids = [o['id'] for o in r2.json().get('values', [])]
                        new_day = set(day_ids) - all_ids
                        all_ids.update(new_day)
                    time.sleep(0.1)

        current = next_date
        total_queries += 1
        time.sleep(0.1)

    print(f"  Total IDs encontrados: {len(all_ids)} (en {total_queries} queries)")
    return list(all_ids)


def get_object_by_id(obj_id):
    """Obtiene un objeto completo por su ID"""
    r = S.get(f"{BASE}/object/{obj_id}", timeout=10)
    if r.status_code == 200:
        return r.json()
    return None


def get_all_objects():
    """Fetch every object using the documented URL query pagination."""
    objects = []
    start_at = 0
    page_size = 100
    while True:
        response = S.post(
            f"{BASE}/object/aql",
            params={
                'startAt': start_at,
                'maxResults': page_size,
                'includeAttributes': 'true',
            },
            json={'qlQuery': 'objectSchemaId = 2'},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        batch = data.get('values', [])
        objects.extend(batch)
        total = data.get('total', len(objects))
        print(f"  Descargados {len(objects)}/{total}", end='\r')
        if not batch or len(objects) >= total:
            print()
            return objects
        start_at += len(batch)
        time.sleep(0.1)


def normalize_attrs(raw_attrs, attr_map):
    result = {}
    refs = {}
    skip = {'Key', 'Created', 'Updated', 'Name'}

    for attr in raw_attrs:
        attr_id = str(attr.get('objectTypeAttributeId', attr.get('id', '')))
        name = attr_map.get(attr_id, attr_id)
        if name in skip:
            continue
        values = attr.get('objectAttributeValues', [])
        if not values:
            continue

        ref_list, plain_list = [], []
        for v in values:
            if v.get('referencedType') and v.get('referencedObject'):
                ref_list.append({
                    'id': str(v['referencedObject'].get('id', '')),
                    'label': v.get('displayValue', '')
                })
            else:
                dv = v.get('displayValue') or v.get('value', '')
                if dv:
                    plain_list.append(str(dv))

        if ref_list:
            refs[name] = ref_list
        elif plain_list:
            result[name] = plain_list[0] if len(plain_list) == 1 else plain_list

    return result, refs


def run():
    print("=" * 60)
    print("  MIGRACION COMPLETA: JIRA -> FERCO MEDICAL PLATFORM")
    print("=" * 60)

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("  BD anterior eliminada")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    print("  BD nueva creada")

    # Atributos
    print("\n[1/4] Obteniendo definiciones de atributos...")
    attr_map = get_attr_map()
    print(f"  OK {len(attr_map)} atributos")

    # Tipos
    print("\n[2/4] Importando tipos de activos...")
    r = S.get(f"{BASE}/objectschema/2/objecttypes/flat", timeout=15)
    r.raise_for_status()
    raw_types = r.json()
    now = datetime.utcnow().isoformat()

    type_id_map = {}
    for ot in raw_types:
        icon = ot.get('icon', {})
        icon_url = icon.get('url48', '') if isinstance(icon, dict) else ''
        conn.execute(
            "INSERT INTO asset_types (jira_type_id, name, description, icon, created_at, updated_at) VALUES (?,?,?,?,?,?)",
            (str(ot['id']), ot['name'], ot.get('description', ''), icon_url, now, now)
        )
    conn.commit()
    for row in conn.execute("SELECT id, jira_type_id FROM asset_types"):
        type_id_map[row['jira_type_id']] = row['id']
    print(f"  OK {len(raw_types)} tipos")

    # Jira expects startAt/maxResults as URL parameters, not JSON fields.
    print("\n[3/4] Descargando todos los activos desde Jira...")
    objects = get_all_objects()
    print(f"  OK {len(objects)} activos descargados")

    # Guardar los objetos ya descargados.
    print(f"\n[4/4] Guardando {len(objects)} activos...")
    jira_id_to_local = {}
    relations_pending = []
    saved = 0
    errors = 0

    for i, obj in enumerate(objects):
        obj_id = str(obj['id'])

        jira_type_id = str(obj.get('objectType', {}).get('id', ''))
        local_type_id = type_id_map.get(jira_type_id)
        if not local_type_id:
            continue

        clean_attrs, refs = normalize_attrs(obj.get('attributes', []), attr_map)

        jira_key = obj.get('objectKey') or f"ACTI-{obj_id}"
        name = obj.get('label') or obj.get('name') or 'Sin nombre'
        jira_created = (obj.get('created', now)[:19] or now).replace('T', ' ')
        jira_updated = (obj.get('updated', now)[:19] or now).replace('T', ' ')

        cur = conn.execute(
            """INSERT OR IGNORE INTO assets
               (jira_key, jira_id, name, type_id, attributes, created_at, updated_at, jira_created_at, jira_updated_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (jira_key, obj_id, name, local_type_id,
             json.dumps(clean_attrs, ensure_ascii=False),
             now, now, jira_created, jira_updated)
        )
        if cur.lastrowid:
            jira_id_to_local[obj_id] = cur.lastrowid
            saved += 1
            for rel_name, ref_list in refs.items():
                for ref in ref_list:
                    relations_pending.append((obj_id, ref['id'], rel_name))

        if (i + 1) % 50 == 0:
            conn.commit()
            print(f"  Procesados {i+1}/{len(objects)} | Guardados: {saved}", end='\r')

    conn.commit()
    print(f"\n  OK {saved} activos guardados ({errors} errores)")

    # Relaciones
    print("\n  Creando relaciones...")
    rel_count = 0
    for src_jira, tgt_jira, rel_type in relations_pending:
        src = jira_id_to_local.get(src_jira)
        tgt = jira_id_to_local.get(tgt_jira)
        if src and tgt:
            conn.execute(
                "INSERT INTO asset_relations (source_asset_id, target_asset_id, relation_type, created_at) VALUES (?,?,?,?)",
                (src, tgt, rel_type, now)
            )
            rel_count += 1
    conn.commit()
    print(f"  OK {rel_count} relaciones")

    # Resumen
    total_assets = conn.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
    total_types  = conn.execute("SELECT COUNT(*) FROM asset_types").fetchone()[0]
    total_rels   = conn.execute("SELECT COUNT(*) FROM asset_relations").fetchone()[0]

    print("\n" + "=" * 60)
    print("  MIGRACION COMPLETADA")
    print("=" * 60)
    print(f"  Tipos     : {total_types}")
    print(f"  Activos   : {total_assets}")
    print(f"  Relaciones: {total_rels}")
    print()
    rows = conn.execute("""
        SELECT at.name, COUNT(a.id) cnt FROM asset_types at
        JOIN assets a ON a.type_id = at.id
        GROUP BY at.name ORDER BY cnt DESC
    """).fetchall()
    for row in rows:
        print(f"    {row[0]:<42} {row[1]:>4}")
    conn.close()
    print()
    print("  Jira ya no es necesario. Todos los datos estan en tu BD.")
    print("=" * 60)


if __name__ == '__main__':
    run()
