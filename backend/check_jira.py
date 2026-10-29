import requests, os, time
from dotenv import load_dotenv
from collections import Counter
load_dotenv()

e = os.getenv('JIRA_EMAIL')
t = os.getenv('JIRA_TOKEN')
wid = os.getenv('JIRA_WORKSPACE_ID')
base = f'https://api.atlassian.com/jsm/assets/workspace/{wid}/v1'
s = requests.Session()
s.auth = (e, t)
s.headers.update({'Accept': 'application/json', 'Content-Type': 'application/json'})

all_ids = []
all_keys = []

for page in range(7):  # 7 paginas x 100 = 700 > 625
    r = s.post(f'{base}/object/aql', json={
        'qlQuery': 'objectSchemaId=2',
        'maxResults': 100,
        'startAt': page * 100,
        'includeAttributes': False
    }, timeout=30)
    data = r.json()
    objs = data.get('values', [])
    print(f"Pagina {page}: {len(objs)} objetos | total={data.get('total')} isLast={data.get('isLast')}")
    if not objs:
        break
    for o in objs:
        all_ids.append(str(o.get('id', '')))
        all_keys.append(str(o.get('objectKey', '')))
    if data.get('isLast', False):
        break
    time.sleep(0.1)

print()
print('Total descargados:', len(all_ids))
print('IDs unicos:', len(set(all_ids)))
print('Keys unicas:', len(set(all_keys)))
id_dupes = [(k, c) for k, c in Counter(all_ids).items() if c > 1]
print('IDs duplicados:', len(id_dupes))
if id_dupes:
    print('Ejemplos:', id_dupes[:5])
