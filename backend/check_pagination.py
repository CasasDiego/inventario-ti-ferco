import requests, os, time
from dotenv import load_dotenv
load_dotenv()

e = os.getenv('JIRA_EMAIL')
t = os.getenv('JIRA_TOKEN')
wid = os.getenv('JIRA_WORKSPACE_ID')
base = f'https://api.atlassian.com/jsm/assets/workspace/{wid}/v1'
s = requests.Session()
s.auth = (e, t)
s.headers.update({'Accept': 'application/json', 'Content-Type': 'application/json'})

print("Probando paginacion con startAt:")
for start in [0, 25, 50, 100, 200, 500]:
    r = s.post(f'{base}/object/aql', json={
        'qlQuery': 'objectSchemaId=2',
        'maxResults': 5,
        'startAt': start,
        'includeAttributes': False
    }, timeout=30)
    objs = r.json().get('values', [])
    ids = [(o['id'], o.get('objectKey')) for o in objs[:3]]
    print(f"  startAt={start}: {ids}")
    time.sleep(0.3)

print()
print("Probando con page en lugar de startAt:")
for page in [0, 1, 2, 5, 10]:
    r = s.post(f'{base}/object/aql', json={
        'qlQuery': 'objectSchemaId=2',
        'maxResults': 5,
        'page': page,
        'includeAttributes': False
    }, timeout=30)
    objs = r.json().get('values', [])
    ids = [(o['id'], o.get('objectKey')) for o in objs[:3]]
    print(f"  page={page}: {ids}")
    time.sleep(0.3)
