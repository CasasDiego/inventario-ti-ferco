#!/usr/bin/env python3
"""
Sincronización rápida con Jira: actualiza nombres, atributos y vínculos (Usuario Final,
Fabricante, licencias...) de los activos existentes, SIN descargar el historial de cada objeto
(que es lo que hace lenta la sincronización completa del botón "Sincronizar con Jira").

No crea activos nuevos ni tipos: para eso usar la sincronización completa.

Uso (desde backend/, con las credenciales de Jira en .env):
    python quick_sync.py                      # base configurada en .env (local)
    python quick_sync.py "postgresql://..."   # otra base, p. ej. la de Neon en producción
"""
import os
import sys
import time

if len(sys.argv) > 1:
    os.environ['DATABASE_URL'] = sys.argv[1]

from app import app, db, refresh_relations, merge_jira_attributes  # noqa: E402  (DATABASE_URL antes)
from models import Asset, AssetRelation  # noqa: E402
from export_jira import JiraAssetsExporter  # noqa: E402
from config import Config  # noqa: E402

with app.app_context():
    exporter = JiraAssetsExporter(Config.JIRA_URL, Config.JIRA_EMAIL, Config.JIRA_TOKEN, Config.JIRA_WORKSPACE_ID)
    attr_names_by_type = {}
    for ot in exporter.get_object_types():
        attr_names_by_type[str(ot['id'])] = exporter.get_attribute_definitions(ot['id'])
        time.sleep(0.05)
    missing = [t for t, names in attr_names_by_type.items() if not names]
    if missing:
        sys.exit(f'No se pudieron leer los nombres de atributos de {len(missing)} tipos; no se cambia nada.')
    raw_objects = exporter.get_all_objects(schema_id='2')
    print(f'{len(raw_objects)} objetos leídos de Jira')

    assets = {a.jira_id: a for a in Asset.query.all()}
    updated = 0
    for obj in raw_objects:
        asset = assets.get(str(obj.get('id', '')))
        if not asset:
            continue
        type_id = str(obj.get('objectType', {}).get('id', obj.get('typeId', '')))
        normalized = exporter.normalize_object(obj, attr_names_by_type.get(type_id, {}))
        asset.name = normalized['label']
        asset.attributes = merge_jira_attributes(asset.attributes, normalized['attributes'])
        updated += 1
    db.session.commit()

    before = AssetRelation.query.count()
    added, removed = refresh_relations(raw_objects, attr_names_by_type)
    print(f'Activos actualizados: {updated}')
    print(f'Vínculos: {added} nuevos, {removed} eliminados. Antes {before}, ahora {AssetRelation.query.count()}.')
