import requests, json, os
from dotenv import load_dotenv
load_dotenv()

e = os.getenv('JIRA_EMAIL')
t = os.getenv('JIRA_TOKEN')
wid = os.getenv('JIRA_WORKSPACE_ID')
base = f'https://api.atlassian.com/jsm/assets/workspace/{wid}/v1'
session = requests.Session()
session.auth = (e, t)
session.headers.update({'Accept': 'application/json'})

with open('jira_assets_export.json', encoding='utf-8') as f:
    data = json.load(f)

types = [t2 for t2 in data['object_types'] if t2.get('objectSchemaId') == '2']

print('=== MAPEO DE ATRIBUTOS POR TIPO ===')
attr_map = {}
for ot in types:
    r = session.get(f"{base}/objecttypeattribute/{ot['id']}", timeout=10)
    if r.status_code == 200:
        attrs = r.json()
        print(f"\n[{ot['name']}] (ID:{ot['id']})")
        for a in attrs:
            attr_map[str(a['id'])] = a.get('name', '')
            print(f"  attr_id:{a['id']} -> '{a.get('name','')}' (tipo:{a.get('type','')})")

with open('attr_map.json', 'w', encoding='utf-8') as f:
    json.dump(attr_map, f, indent=2, ensure_ascii=False)
print('\n\nMapeo guardado en attr_map.json')
