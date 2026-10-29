"""
Prueba directa del endpoint de historial de Jira Assets contra un objeto real,
sin pasar por el sync completo. Ayuda a diagnosticar por que no llega actividad.
"""
import requests, os, json
from dotenv import load_dotenv
load_dotenv()

e = os.getenv('JIRA_EMAIL')
t = os.getenv('JIRA_TOKEN')
wid = os.getenv('JIRA_WORKSPACE_ID')
base = f'https://api.atlassian.com/jsm/assets/workspace/{wid}/v1'
s = requests.Session()
s.auth = (e, t)
s.headers.update({'Accept': 'application/json', 'Content-Type': 'application/json'})

# 1. Traer un objeto real para probar contra su ID
r = s.post(f'{base}/object/aql', json={'qlQuery': 'objectSchemaId=2', 'maxResults': 3, 'startAt': 0, 'includeAttributes': False}, timeout=30)
print('AQL status:', r.status_code)
objs = r.json().get('values', []) if r.status_code == 200 else []
if not objs:
    print('No se pudo traer ni un objeto de prueba. Respuesta:', r.text[:400])
    raise SystemExit(1)

test_ids = [str(o['id']) for o in objs]
print('Probando con IDs:', test_ids)
print()

candidates = [
    '/object/{id}/history',
    '/objecthistory/{id}',
    '/objecthistory/object/{id}',
    '/object/history/{id}',
]

for obj_id in test_ids:
    print(f'=== Objeto {obj_id} ===')
    for path in candidates:
        url = base + path.format(id=obj_id)
        try:
            resp = s.get(url, timeout=15)
            print(f'  {path} -> {resp.status_code}')
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    print('    OK, respuesta:', json.dumps(data, ensure_ascii=False)[:500])
                except Exception:
                    print('    OK pero no es JSON:', resp.text[:200])
            else:
                print('    body:', resp.text[:200])
        except Exception as ex:
            print(f'  {path} -> ERROR {ex}')
    print()
