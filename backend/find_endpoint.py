import requests, os, time, json
from dotenv import load_dotenv
load_dotenv()

e = os.getenv('JIRA_EMAIL')
t = os.getenv('JIRA_TOKEN')
wid = os.getenv('JIRA_WORKSPACE_ID')
base = f'https://api.atlassian.com/jsm/assets/workspace/{wid}/v1'
s = requests.Session()
s.auth = (e, t)
s.headers.update({'Accept': 'application/json', 'Content-Type': 'application/json'})

# Obtener tipos del schema 2
r = s.get(f'{base}/objectschema/2/objecttypes/flat', timeout=15)
types = r.json()
print(f"Tipos en schema 2: {len(types)}")
for ot in types:
    print(f"  ID:{ot['id']} {ot['name']}")

print()
print("Probando endpoint por tipo (objecttype/{id}/objects):")
# Probar con el tipo Lineas Moviles (ID:21) que tiene 475 objetos
for type_id in ['21', '20', '9']:
    r2 = s.get(f'{base}/objecttype/{type_id}/objects', params={'page': 0, 'pageSize': 5}, timeout=15)
    print(f"  Tipo {type_id}: status={r2.status_code}")
    if r2.status_code == 200:
        data = r2.json()
        objs = data.get('values', data) if isinstance(data, dict) else data
        print(f"    Objetos: {len(objs) if isinstance(objs, list) else 'dict'}")
        print(f"    Keys respuesta: {list(data.keys()) if isinstance(data, dict) else 'lista'}")
        if isinstance(objs, list) and objs:
            print(f"    Primero: id={objs[0].get('id')} key={objs[0].get('objectKey')}")
    else:
        print(f"    Error: {r2.text[:200]}")
    time.sleep(0.3)
