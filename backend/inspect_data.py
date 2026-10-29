import json

with open('jira_assets_export.json', encoding='utf-8') as f:
    data = json.load(f)

print('=== TIPOS DE OBJETOS ===')
types = [t for t in data['object_types'] if t.get('objectSchemaId') == '2']
for t in types:
    print(f"  ID:{t['id']} | {t['name']} | padre:{t.get('parentObjectTypeId','-')} | count:{t.get('objectCount',0)}")

print()
print('=== MUESTRA DE OBJETOS ===')
for obj in data['objects'][:8]:
    print(f"  [{obj['typeName']}] {obj['label']} ({obj['key']})")
    for k, v in obj['attributes'].items():
        print(f"    {k}: {v}")
    print()

print('=== TIPOS CON SUS OBJETOS ===')
from collections import Counter
type_counts = Counter(o['typeName'] for o in data['objects'])
for t, c in type_counts.most_common():
    print(f"  {t}: {c} objetos")
