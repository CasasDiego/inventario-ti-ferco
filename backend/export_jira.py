#!/usr/bin/env python3
"""
Exportador de Jira Assets para Ferco Medical
Usa los endpoints correctos: AQL via POST, objectschema, objecttypes/flat
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List
import logging
import sys
import argparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class JiraAssetsExporter:
    def __init__(self, jira_url: str, email: str, api_token: str, workspace_id: str = '', verbose: bool = False):
        self.jira_url = jira_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.verbose = verbose

        self.workspace_id = workspace_id or self._fetch_workspace_id()
        if not self.workspace_id:
            raise ValueError("No se pudo obtener el Workspace ID. Configura JIRA_WORKSPACE_ID en .env")

        self.api_base = f"https://api.atlassian.com/jsm/assets/workspace/{self.workspace_id}/v1"

        self.session = requests.Session()
        self.session.auth = (email, api_token)
        self.session.headers.update({'Accept': 'application/json', 'Content-Type': 'application/json'})

        if verbose:
            logger.setLevel(logging.DEBUG)

    def _fetch_workspace_id(self) -> str:
        """Obtiene el workspace ID desde la API de JSM"""
        try:
            r = self.session.get(
                f"{self.jira_url}/rest/servicedeskapi/assets/workspace",
                timeout=10
            )
            if r.status_code == 200:
                values = r.json().get('values', [])
                if values:
                    wid = values[0]['workspaceId']
                    logger.info(f"✓ Workspace ID detectado: {wid}")
                    return wid
            logger.error(f"No se pudo obtener workspace: {r.status_code} {r.text[:200]}")
            return ''
        except Exception as e:
            logger.error(f"Error al obtener workspace ID: {e}")
            return ''

    def test_connection(self) -> bool:
        try:
            r = self.session.get(f"{self.api_base}/objectschema/list", timeout=10)
            if r.status_code == 200:
                schemas = r.json().get('values', [])
                logger.info(f"✓ Conexión exitosa — {len(schemas)} schema(s) encontrado(s)")
                for s in schemas:
                    logger.info(f"   Schema: {s['name']} (ID:{s['id']}) — {s.get('objectCount',0)} objetos")
                return True
            logger.error(f"✗ Error: {r.status_code} {r.text[:200]}")
            return False
        except Exception as e:
            logger.error(f"✗ Error de conexión: {e}")
            return False

    def get_schemas(self) -> List[Dict]:
        """Obtiene todos los schemas de Assets"""
        r = self.session.get(f"{self.api_base}/objectschema/list", timeout=10)
        r.raise_for_status()
        return r.json().get('values', [])

    def get_object_types(self, schema_id: str = None) -> List[Dict]:
        """Obtiene todos los tipos de objetos de un schema"""
        all_types = []
        schemas = self.get_schemas() if not schema_id else [{'id': schema_id}]

        for schema in schemas:
            sid = schema['id']
            r = self.session.get(f"{self.api_base}/objectschema/{sid}/objecttypes/flat", timeout=10)
            if r.status_code == 200:
                types = r.json()
                all_types.extend(types)
                logger.info(f"✓ Schema {sid}: {len(types)} tipos de objetos")
            else:
                logger.warning(f"No se pudieron obtener tipos del schema {sid}: {r.status_code}")

        return all_types

    def get_attribute_definitions(self, object_type_id: str) -> Dict:
        """Obtiene las definiciones de atributos de un tipo de objeto (para mapear IDs a nombres)"""
        try:
            r = self.session.get(f"{self.api_base}/objecttypeattribute/{object_type_id}", timeout=10)
            if r.status_code == 200:
                attrs = r.json()
                return {str(a['id']): a.get('name', f'attr_{a["id"]}') for a in attrs}
        except Exception:
            pass
        return {}

    def get_all_objects(self, schema_id: str = '2') -> List[Dict]:
        """
        Obtiene TODOS los objetos usando AQL via POST con paginación.
        schema_id='2' es el schema 'Activos de Ti' de Ferco Medical.
        """
        all_objects = []
        page = 0
        page_size = 100

        logger.info(f"Obteniendo objetos del schema {schema_id} via AQL...")

        while True:
            payload = {
                'qlQuery': f'objectSchemaId = {schema_id}',
                'includeAttributes': True
            }
            # startAt/maxResults son ignorados si van en el body: esta API los requiere como query params.
            params = {
                'maxResults': page_size,
                'startAt': page * page_size,
            }

            r = self.session.post(f"{self.api_base}/object/aql", params=params, json=payload, timeout=30)

            if r.status_code != 200:
                logger.error(f"Error AQL página {page}: {r.status_code} {r.text[:300]}")
                break

            data = r.json()
            objects = data.get('values', [])

            if not objects:
                break

            all_objects.extend(objects)
            total = data.get('total', len(all_objects))
            logger.info(f"  Página {page + 1}: {len(objects)} objetos (total: {len(all_objects)}/{total})")

            if len(all_objects) >= total or data.get('isLast', False):
                break

            page += 1
            time.sleep(0.1)

        logger.info(f"✓ Total objetos obtenidos: {len(all_objects)}")
        return all_objects

    def get_object_relations(self, object_id: str) -> List[Dict]:
        """Obtiene las relaciones de un objeto"""
        try:
            r = self.session.get(f"{self.api_base}/objectconnectedtickets/{object_id}/tickets", timeout=10)
            # También intentar relaciones directas
            r2 = self.session.get(f"{self.api_base}/object/{object_id}/referenceobjects", timeout=10)
            relations = []
            if r2.status_code == 200:
                relations = r2.json() if isinstance(r2.json(), list) else []
            return relations
        except Exception as e:
            if self.verbose:
                logger.debug(f"Error relaciones {object_id}: {e}")
            return []

    def get_object_history(self, object_id: str) -> List[Dict]:
        """Obtiene el historial de actividad (creación, cambios de atributos, etc.) de un objeto."""
        url = f"{self.api_base}/object/{object_id}/history"
        for attempt in range(2):
            try:
                r = self.session.get(url, params={'asc': 'true'}, timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    return data if isinstance(data, list) else data.get('values', [])
                if r.status_code == 429 and attempt == 0:
                    wait = float(r.headers.get('Retry-After', 2))
                    logger.warning(f"Rate limit al pedir historial de {object_id}, esperando {wait}s y reintentando")
                    time.sleep(wait)
                    continue
                logger.warning(f"Historial {object_id} falló: {r.status_code} {r.text[:200]}")
                return []
            except Exception as e:
                logger.warning(f"Error historial {object_id}: {e}")
                return []
        return []

    def normalize_object(self, obj: Dict, attr_names: Dict = None) -> Dict:
        """
        Convierte un objeto de Jira Assets a un formato limpio con atributos legibles.
        """
        attrs_raw = obj.get('attributes', [])
        attrs_clean = {}

        for attr in attrs_raw:
            attr_id = str(attr.get('objectTypeAttributeId', attr.get('id', '')))
            name = (attr_names or {}).get(attr_id, attr_id)
            values = attr.get('objectAttributeValues', [])
            if values:
                display = [v.get('displayValue') or v.get('value', '') for v in values]
                attrs_clean[name] = display[0] if len(display) == 1 else display

        return {
            'id': str(obj.get('id', '')),
            'key': obj.get('objectKey', obj.get('key', '')),
            'label': obj.get('label', obj.get('name', 'Sin nombre')),
            'typeId': str(obj.get('objectType', {}).get('id', obj.get('typeId', ''))),
            'typeName': obj.get('objectType', {}).get('name', ''),
            'created': obj.get('created', ''),
            'updated': obj.get('updated', ''),
            'attributes': attrs_clean,
            '_raw': obj
        }

    def export_to_json(self, filename: str = 'jira_assets_export.json') -> str:
        logger.info("Iniciando exportación completa...")

        schemas = self.get_schemas()
        object_types = self.get_object_types()

        # Obtener definiciones de atributos por tipo
        attr_names_by_type = {}
        for ot in object_types:
            attr_names_by_type[str(ot['id'])] = self.get_attribute_definitions(ot['id'])
            time.sleep(0.05)

        # Obtener todos los objetos del schema principal (ID 2 = Activos de Ti)
        raw_objects = self.get_all_objects(schema_id='2')

        # Normalizar objetos
        objects = []
        for obj in raw_objects:
            type_id = str(obj.get('objectType', {}).get('id', ''))
            attr_names = attr_names_by_type.get(type_id, {})
            objects.append(self.normalize_object(obj, attr_names))

        export_data = {
            'exported_at': datetime.utcnow().isoformat(),
            'jira_url': self.jira_url,
            'workspace_id': self.workspace_id,
            'schemas': schemas,
            'object_types': object_types,
            'objects': objects,
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"✓ Exportado a {filename}")
        logger.info(f"  Schemas: {len(schemas)}")
        logger.info(f"  Tipos de objetos: {len(object_types)}")
        logger.info(f"  Objetos: {len(objects)}")
        return filename


def main():
    parser = argparse.ArgumentParser(description='Exporta Jira Assets de Ferco Medical')
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--output', '-o', default='jira_assets_export.json')
    args = parser.parse_args()

    import os
    from dotenv import load_dotenv
    load_dotenv()

    jira_url = os.getenv('JIRA_URL')
    email = os.getenv('JIRA_EMAIL')
    token = os.getenv('JIRA_TOKEN')
    workspace_id = os.getenv('JIRA_WORKSPACE_ID', '')

    if not all([jira_url, email, token]):
        logger.error("Faltan credenciales en .env")
        sys.exit(1)

    try:
        exporter = JiraAssetsExporter(jira_url, email, token, workspace_id, verbose=args.verbose)
        if not exporter.test_connection():
            sys.exit(1)
        exporter.export_to_json(args.output)
        logger.info("✓ Exportación completada")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
