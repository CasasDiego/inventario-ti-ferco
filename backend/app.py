#!/usr/bin/env python3
"""
API REST - Ferco Medical Assets Manager
"""

from flask import Flask, jsonify, request, Response, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db, User, AssetType, Asset, AssetRelation, AssetActivity, SyncLog
from export_jira import JiraAssetsExporter
import json
import logging
import csv
import io
from datetime import datetime
from dotenv import load_dotenv
import os
import time
import threading

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

CORS(app, origins=Config.CORS_ORIGINS)

db.init_app(app)

# Detrás del proxy de Render, la IP real del cliente llega en X-Forwarded-For
if os.getenv('TRUST_PROXY', '0') == '1':
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

# La plataforma tiene una única cuenta de acceso.
ADMIN_EMAIL = 'dcasas@ferco-medical.com'

with app.app_context():
    db.create_all()
    admin_password = os.getenv('ADMIN_PASSWORD', '').strip()
    admin = User.query.filter_by(email=ADMIN_EMAIL).first()
    if not admin:
        # En la nube (DATABASE_URL definido) no se crea la cuenta con una contraseña por defecto.
        if not admin_password and os.getenv('DATABASE_URL'):
            logger.error('ADMIN_PASSWORD no está definido: no se creó la cuenta de acceso.')
        else:
            admin = User(email=ADMIN_EMAIL, display_name='Diego Casas')
            admin.set_password(admin_password or 'admin123')
            db.session.add(admin)
            db.session.commit()
    elif admin_password and not admin.check_password(admin_password):
        # ADMIN_PASSWORD manda: cambiarlo en el .env / Render cambia la contraseña al reiniciar.
        admin.set_password(admin_password)
        db.session.commit()
        logger.info('Contraseña de la cuenta actualizada desde ADMIN_PASSWORD.')

# Estado global de sincronización
_sync_status = {'running': False, 'sync_id': None}

# Algunos tipos de Jira tienen el atributo de referencia mal escrito ("Usuario Finall").
# Se unifica al nombre que usa la UI para que cada vínculo exista una sola vez.
RELATION_TYPE_ALIASES = {'Usuario Finall': 'Usuario Final'}


def canonical_relation_type(name: str) -> str:
    name = str(name).strip()
    return RELATION_TYPE_ALIASES.get(name, name)


@app.before_request
def require_login():
    """Protege la API local; autenticación y salud permanecen públicas."""
    public_routes = {'/api/health', '/api/auth/login', '/api/auth/me'}
    if request.path.startswith('/api/') and request.path not in public_routes and 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Inicia sesión para continuar'}), 401


# ---------------------------------------------------------------------------
# Límite de intentos de inicio de sesión (protección contra fuerza bruta).
# - Por IP: 5 fallos en 15 min bloquean esa IP 15 min.
# - Por cuenta: 10 fallos en 15 min (desde cualquier IP) bloquean la cuenta 15 min,
#   para frenar ataques que rotan de IP.
# Se guarda en memoria (gunicorn corre con un solo worker); un reinicio lo limpia.
# ---------------------------------------------------------------------------
LOGIN_WINDOW_SECONDS = 15 * 60
LOGIN_LOCK_SECONDS = 15 * 60
LOGIN_MAX_FAILS_PER_IP = 5
LOGIN_MAX_FAILS_PER_ACCOUNT = 10
_login_fails = {}    # clave -> lista de timestamps de fallos recientes
_login_locked = {}   # clave -> timestamp hasta el que está bloqueada
_login_lock = threading.Lock()


def _login_keys(email):
    return {'ip': f'ip:{request.remote_addr}', 'account': f'account:{email}'}


def _login_locked_seconds(keys):
    now = time.time()
    with _login_lock:
        remaining = max((_login_locked.get(k, 0) - now for k in keys.values()), default=0)
    return int(remaining) if remaining > 0 else 0


def _register_login_failure(keys):
    now = time.time()
    limits = {'ip': LOGIN_MAX_FAILS_PER_IP, 'account': LOGIN_MAX_FAILS_PER_ACCOUNT}
    with _login_lock:
        for kind, key in keys.items():
            recent = [t for t in _login_fails.get(key, []) if now - t < LOGIN_WINDOW_SECONDS] + [now]
            _login_fails[key] = recent
            if len(recent) >= limits[kind]:
                _login_locked[key] = now + LOGIN_LOCK_SECONDS
                _login_fails.pop(key, None)
                logger.warning(f'Inicio de sesión bloqueado ({key}) por demasiados intentos fallidos')


def _clear_login_failures(keys):
    with _login_lock:
        for key in keys.values():
            _login_fails.pop(key, None)


def _too_many_attempts(seconds):
    minutes = max(1, -(-seconds // 60))
    return jsonify({
        'status': 'error',
        'message': f'Demasiados intentos fallidos. Vuelve a intentarlo en {minutes} min.'
    }), 429


@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get('email', '')).strip().lower()
    password = str(data.get('password', ''))
    keys = _login_keys(email)

    locked = _login_locked_seconds(keys)
    if locked:
        return _too_many_attempts(locked)

    user = User.query.filter_by(email=email).first() if email == ADMIN_EMAIL else None
    if not user or not user.check_password(password):
        _register_login_failure(keys)
        time.sleep(0.5)  # frena los intentos automatizados
        locked = _login_locked_seconds(keys)
        if locked:
            return _too_many_attempts(locked)
        return jsonify({'status': 'error', 'message': 'Correo o contraseña incorrectos'}), 401

    _clear_login_failures(keys)
    session.clear()
    session['user_id'] = user.id
    return jsonify({'status': 'success', 'data': user.to_dict()}), 200


@app.route('/api/auth/me', methods=['GET'])
def current_user():
    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None
    if not user or user.email != ADMIN_EMAIL:
        return jsonify({'status': 'error', 'message': 'Sesión no iniciada'}), 401
    return jsonify({'status': 'success', 'data': user.to_dict()}), 200


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'status': 'success'}), 200


# ===========================
# SALUD Y INFO
# ===========================

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database': 'connected',
        'sync_running': _sync_status['running']
    }), 200


@app.route('/api/info', methods=['GET'])
def info():
    total_assets = db.session.query(Asset).count()
    total_types = db.session.query(AssetType).count()
    total_relations = db.session.query(AssetRelation).count()
    return jsonify({
        'name': 'Ferco Medical Assets Manager',
        'version': '1.0.0',
        'database': {
            'total_assets': total_assets,
            'total_types': total_types,
            'total_relations': total_relations
        }
    }), 200


# ===========================
# SINCRONIZACIÓN (async)
# ===========================

def _run_sync(sync_log_id: int):
    """Ejecuta la sincronización en un hilo separado"""
    _sync_status['running'] = True
    _sync_status['sync_id'] = sync_log_id

    with app.app_context():
        sync_log = SyncLog.query.get(sync_log_id)
        start_time = time.time()

        try:
            jira_url = os.getenv('JIRA_URL')
            email = os.getenv('JIRA_EMAIL')
            token = os.getenv('JIRA_TOKEN')
            workspace_id = os.getenv('JIRA_WORKSPACE_ID', '')

            if not all([jira_url, email, token]):
                raise ValueError("Faltan credenciales de Jira en .env")

            exporter = JiraAssetsExporter(jira_url, email, token, workspace_id)

            if not exporter.test_connection():
                raise Exception("No se pudo conectar a Jira Assets")

            # Tipos de objetos (schema 2 = Activos de Ti)
            object_types = exporter.get_object_types(schema_id='2')
            for ot in object_types:
                existing = AssetType.query.filter_by(jira_type_id=str(ot['id'])).first()
                if existing:
                    existing.name = ot.get('name', existing.name)
                else:
                    icon_data = ot.get('icon', {})
                    icon_url = icon_data.get('url48', '') if isinstance(icon_data, dict) else str(icon_data)
                    db.session.add(AssetType(
                        jira_type_id=str(ot['id']),
                        name=ot.get('name', 'Unknown'),
                        description=ot.get('description', ''),
                        icon=icon_url
                    ))
            db.session.commit()
            logger.info(f"✓ {len(object_types)} tipos procesados")

            # Obtener definiciones de atributos por tipo (para nombres legibles)
            attr_names_by_type = {}
            for ot in object_types:
                attr_names_by_type[str(ot['id'])] = exporter.get_attribute_definitions(ot['id'])
                time.sleep(0.05)

            # Objetos via AQL
            raw_objects = exporter.get_all_objects(schema_id='2')
            assets_created = 0
            assets_updated = 0

            for obj in raw_objects:
                type_id = str(obj.get('objectType', {}).get('id', obj.get('typeId', '')))
                asset_type = AssetType.query.filter_by(jira_type_id=type_id).first()
                if not asset_type:
                    continue

                attr_names = attr_names_by_type.get(type_id, {})
                normalized = exporter.normalize_object(obj, attr_names)

                jira_created = None
                jira_updated = None
                try:
                    if obj.get('created'):
                        jira_created = datetime.fromisoformat(obj['created'].replace('Z', '+00:00').replace('+00:00', ''))
                    if obj.get('updated'):
                        jira_updated = datetime.fromisoformat(obj['updated'].replace('Z', '+00:00').replace('+00:00', ''))
                except Exception:
                    pass

                existing = Asset.query.filter_by(jira_id=normalized['id']).first()
                if existing:
                    existing.name = normalized['label']
                    existing.attributes = {**(existing.attributes or {}), **normalized['attributes']}
                    existing.jira_updated_at = jira_updated or datetime.utcnow()
                    assets_updated += 1
                else:
                    db.session.add(Asset(
                        jira_id=normalized['id'],
                        jira_key=normalized['key'],
                        name=normalized['label'],
                        type_id=asset_type.id,
                        attributes=normalized['attributes'],
                        jira_created_at=jira_created or datetime.utcnow(),
                        jira_updated_at=jira_updated or datetime.utcnow()
                    ))
                    assets_created += 1

            db.session.commit()
            logger.info(f"✓ {assets_created} creados, {assets_updated} actualizados")

            # Relaciones (via atributos de referencia en los objetos).
            # Jira es la fuente de verdad: para cada objeto se calcula el conjunto actual de
            # referencias (con el NOMBRE del atributo como relation_type, no su ID numérico) y se
            # reemplazan las relaciones locales salientes de ese objeto, eliminando duplicados y
            # referencias que ya no existen en Jira (p. ej. un equipo reasignado a otro usuario).
            relations_count = 0
            for obj in raw_objects:
                source_id = str(obj.get('id', ''))
                source = Asset.query.filter_by(jira_id=source_id).first()
                if not source:
                    continue

                type_id = str(obj.get('objectType', {}).get('id', obj.get('typeId', '')))
                attr_names = attr_names_by_type.get(type_id, {})
                wanted = set()
                for attr in obj.get('attributes', []):
                    attr_id = str(attr.get('objectTypeAttributeId', ''))
                    rel_type = canonical_relation_type(attr_names.get(attr_id) or attr_id or 'referencia')
                    for val in attr.get('objectAttributeValues', []):
                        if val.get('referencedType') and val.get('referencedObject'):
                            target_jira_id = str(val['referencedObject'].get('id', ''))
                            target = Asset.query.filter_by(jira_id=target_jira_id).first()
                            if target:
                                wanted.add((target.id, rel_type))

                current = {}
                for rel in AssetRelation.query.filter_by(source_asset_id=source.id).all():
                    key = (rel.target_asset_id, rel.relation_type)
                    if key in wanted and key not in current:
                        current[key] = rel
                    else:
                        db.session.delete(rel)
                for target_id, rel_type in wanted - set(current):
                    db.session.add(AssetRelation(
                        source_asset_id=source.id,
                        target_asset_id=target_id,
                        relation_type=rel_type
                    ))
                    relations_count += 1

            db.session.commit()

            # Historial de actividad de cada objeto (creación, cambios de atributos, etc.)
            known_history_ids = {row[0] for row in db.session.query(AssetActivity.jira_history_id).all()}
            activities_count = 0
            objects_with_history = 0
            objects_without_history = 0
            sample_logged = False
            for obj in raw_objects:
                source_id = str(obj.get('id', ''))
                asset = Asset.query.filter_by(jira_id=source_id).first()
                if not asset:
                    continue

                history = exporter.get_object_history(source_id)
                if history:
                    objects_with_history += 1
                    if not sample_logged:
                        logger.info(f"Ejemplo de entrada de historial (objeto {source_id}): {history[0]}")
                        sample_logged = True
                else:
                    objects_without_history += 1

                for entry in history:
                    hist_id = str(entry.get('id', ''))
                    if not hist_id:
                        logger.warning(f"Entrada de historial del objeto {source_id} sin campo 'id' reconocible: {entry}")
                        continue
                    if hist_id in known_history_ids:
                        continue
                    known_history_ids.add(hist_id)

                    entry_created = None
                    try:
                        if entry.get('created'):
                            entry_created = datetime.fromisoformat(entry['created'].replace('Z', '+00:00').replace('+00:00', ''))
                    except Exception:
                        pass

                    actor = entry.get('actor') or {}
                    db.session.add(AssetActivity(
                        asset_id=asset.id,
                        jira_history_id=hist_id,
                        actor_name=actor.get('displayName', '') if isinstance(actor, dict) else str(actor),
                        affected_attribute=entry.get('affectedAttribute', ''),
                        old_value=str(entry.get('oldValue', '') or ''),
                        new_value=str(entry.get('newValue', '') or ''),
                        change_type=entry.get('type'),
                        created_at=entry_created or datetime.utcnow()
                    ))
                    activities_count += 1
                time.sleep(0.05)

            db.session.commit()
            logger.info(f"✓ {activities_count} entradas de actividad nuevas ({objects_with_history} objetos con historial, {objects_without_history} sin historial devuelto)")

            duration = time.time() - start_time
            sync_log.status = 'success'
            sync_log.total_assets = assets_created + assets_updated
            sync_log.total_relations = AssetRelation.query.count()
            sync_log.duration_seconds = duration
            db.session.commit()
            logger.info(f"✓ Sync completado en {duration:.1f}s")

        except Exception as e:
            logger.error(f"Error en sync: {e}")
            sync_log.status = 'error'
            sync_log.error_message = str(e)
            db.session.commit()
        finally:
            _sync_status['running'] = False
            _sync_status['sync_id'] = None


@app.route('/api/sync', methods=['POST'])
def sync_jira():
    if _sync_status['running']:
        return jsonify({
            'status': 'error',
            'message': 'Ya hay una sincronización en curso',
            'sync_id': _sync_status['sync_id']
        }), 409

    sync_log = SyncLog(status='pending')
    db.session.add(sync_log)
    db.session.commit()

    thread = threading.Thread(target=_run_sync, args=(sync_log.id,), daemon=True)
    thread.start()

    return jsonify({
        'status': 'started',
        'sync_id': sync_log.id,
        'message': 'Sincronización iniciada en segundo plano'
    }), 202


@app.route('/api/sync/status', methods=['GET'])
def sync_status():
    """Estado actual de la sincronización"""
    last = SyncLog.query.order_by(SyncLog.id.desc()).first()
    return jsonify({
        'running': _sync_status['running'],
        'sync_id': _sync_status['sync_id'],
        'last_sync': last.to_dict() if last else None
    }), 200


@app.route('/api/sync/logs', methods=['GET'])
def get_sync_logs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    logs = SyncLog.query.order_by(SyncLog.sync_date.desc()).paginate(page=page, per_page=per_page)
    return jsonify({
        'status': 'success',
        'total': logs.total,
        'page': page,
        'per_page': per_page,
        'data': [log.to_dict() for log in logs.items]
    }), 200


# ===========================
# ASSET TYPES
# ===========================

@app.route('/api/asset-types', methods=['GET'])
def get_asset_types():
    types = AssetType.query.all()
    return jsonify({'status': 'success', 'total': len(types), 'data': [t.to_dict() for t in types]}), 200


@app.route('/api/asset-types/<int:type_id>', methods=['GET'])
def get_asset_type(type_id):
    asset_type = AssetType.query.get(type_id)
    if not asset_type:
        return jsonify({'status': 'error', 'message': 'No encontrado'}), 404
    return jsonify({'status': 'success', 'data': asset_type.to_dict()}), 200


# ===========================
# ASSETS
# ===========================

@app.route('/api/assets', methods=['GET'])
def get_assets():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 200)
        type_id = request.args.get('type_id', None, type=int)
        search = request.args.get('search', '', type=str).strip()
        parent_id = request.args.get('parent_id', None)

        query = Asset.query

        if type_id:
            query = query.filter_by(type_id=type_id)

        if search:
            query = query.filter(
                db.or_(
                    Asset.name.ilike(f'%{search}%'),
                    Asset.jira_key.ilike(f'%{search}%'),
                    db.cast(Asset.attributes, db.Text).ilike(f'%{search}%')
                )
            )

        if parent_id == 'null':
            query = query.filter(Asset.parent_id.is_(None))
        elif parent_id is not None:
            try:
                query = query.filter_by(parent_id=int(parent_id))
            except ValueError:
                pass

        paginated = query.order_by(Asset.name).paginate(page=page, per_page=per_page)

        return jsonify({
            'status': 'success',
            'total': paginated.total,
            'page': page,
            'per_page': per_page,
            'pages': paginated.pages,
            'data': [asset.to_dict() for asset in paginated.items]
        }), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/assets/<int:asset_id>', methods=['GET'])
def get_asset(asset_id):
    try:
        asset = Asset.query.get(asset_id)
        if not asset:
            return jsonify({'status': 'error', 'message': 'No encontrado'}), 404

        relations = AssetRelation.query.filter_by(source_asset_id=asset_id).all()
        asset_data = asset.to_dict(include_children=True)

        # Incluir nombre del activo relacionado
        relations_data = []
        for r in relations:
            rd = r.to_dict()
            target = Asset.query.get(r.target_asset_id)
            rd['target_asset_name'] = target.name if target else f'ID {r.target_asset_id}'
            rd['target_asset_type'] = target.asset_type.name if target and target.asset_type else ''
            relations_data.append(rd)

        incoming_data = []
        for r in AssetRelation.query.filter_by(target_asset_id=asset_id).all():
            source = Asset.query.get(r.source_asset_id)
            incoming_data.append({
                **r.to_dict(),
                'source_asset_name': source.name if source else f'ID {r.source_asset_id}',
                'source_asset_type': source.asset_type.name if source and source.asset_type else ''
            })

        asset_data['relations'] = relations_data
        asset_data['incoming_relations'] = incoming_data
        activities = AssetActivity.query.filter_by(asset_id=asset_id).order_by(AssetActivity.created_at.desc()).all()
        asset_data['activities'] = [a.to_dict() for a in activities]

        return jsonify({'status': 'success', 'data': asset_data}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/assets/options', methods=['GET'])
def asset_options():
    """Opciones para campos de referencia (Usuario Final y Fabricante)."""
    kind = request.args.get('kind', '')
    query_text = request.args.get('q', '').strip()
    type_name = {'users': 'Usuario', 'brands': 'Marca'}.get(kind)
    if not type_name:
        return jsonify({'status': 'error', 'message': 'Tipo de opción no válido'}), 400
    query = Asset.query.join(AssetType).filter(AssetType.name == type_name)
    if query_text:
        query = query.filter(Asset.name.ilike(f'%{query_text}%'))
    assets = query.order_by(Asset.name).limit(50).all()
    return jsonify({'status': 'success', 'data': [a.to_dict() for a in assets]}), 200


@app.route('/api/assets', methods=['POST'])
def create_asset():
    try:
        data = request.get_json()
        if not data.get('name') or not data.get('type_id'):
            return jsonify({'status': 'error', 'message': 'Faltan datos requeridos: name, type_id'}), 400

        asset = Asset(
            jira_id=data.get('jira_id', f"LOCAL-{int(time.time())}"),
            jira_key=data.get('jira_key', ''),
            name=data['name'],
            type_id=data['type_id'],
            attributes=data.get('attributes', {}),
            parent_id=data.get('parent_id')
        )
        db.session.add(asset)
        db.session.flush()

        for field_name, target_asset_id in (data.get('references') or {}).items():
            if not target_asset_id:
                continue
            target = Asset.query.get(int(target_asset_id))
            if not target:
                db.session.rollback()
                return jsonify({'status': 'error', 'message': 'Activo relacionado no encontrado'}), 404
            db.session.add(AssetRelation(
                source_asset_id=asset.id,
                target_asset_id=target.id,
                relation_type=field_name
            ))

        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Activo creado', 'data': asset.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/assets/<int:asset_id>', methods=['PUT'])
def update_asset(asset_id):
    try:
        asset = Asset.query.get(asset_id)
        if not asset:
            return jsonify({'status': 'error', 'message': 'No encontrado'}), 404

        data = request.get_json()
        if 'name' in data:
            asset.name = data['name']
        if 'attributes' in data:
            current = dict(asset.attributes or {})
            current.update(data['attributes'])
            asset.attributes = current
        if 'references' in data:
            for field_name, target_asset_id in data['references'].items():
                AssetRelation.query.filter_by(
                    source_asset_id=asset.id,
                    relation_type=field_name
                ).delete(synchronize_session=False)
                if target_asset_id:
                    target = Asset.query.get(int(target_asset_id))
                    if not target:
                        return jsonify({'status': 'error', 'message': 'Activo relacionado no encontrado'}), 404
                    db.session.add(AssetRelation(
                        source_asset_id=asset.id,
                        target_asset_id=target.id,
                        relation_type=field_name
                    ))
        if 'parent_id' in data:
            asset.parent_id = data['parent_id']

        asset.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Activo actualizado', 'data': asset.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/assets/<int:asset_id>', methods=['DELETE'])
def delete_asset(asset_id):
    try:
        asset = Asset.query.get(asset_id)
        if not asset:
            return jsonify({'status': 'error', 'message': 'No encontrado'}), 404
        db.session.delete(asset)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Activo eliminado'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ===========================
# EXPORTACIÓN CSV
# ===========================

@app.route('/api/assets/export/csv', methods=['GET'])
def export_csv():
    """Exporta activos a CSV"""
    try:
        type_id = request.args.get('type_id', None, type=int)
        search = request.args.get('search', '', type=str).strip()

        query = Asset.query
        if type_id:
            query = query.filter_by(type_id=type_id)
        if search:
            query = query.filter(
                db.or_(
                    Asset.name.ilike(f'%{search}%'),
                    Asset.jira_key.ilike(f'%{search}%')
                )
            )

        assets = query.order_by(Asset.name).all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Clave', 'Nombre', 'Tipo', 'Creado', 'Actualizado'])

        for a in assets:
            writer.writerow([
                a.id,
                a.jira_key,
                a.name,
                a.asset_type.name if a.asset_type else '',
                a.created_at.strftime('%Y-%m-%d %H:%M') if a.created_at else '',
                a.updated_at.strftime('%Y-%m-%d %H:%M') if a.updated_at else ''
            ])

        output.seek(0)
        filename = f"ferco_assets_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ===========================
# JERARQUÍA Y BÚSQUEDA
# ===========================

@app.route('/api/assets/tree/hierarchy', methods=['GET'])
def get_assets_hierarchy():
    try:
        root_assets = Asset.query.filter_by(parent_id=None).all()

        def build_tree(asset):
            return {**asset.to_dict(), 'children': [build_tree(c) for c in asset.children]}

        return jsonify({'status': 'success', 'data': [build_tree(a) for a in root_assets]}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/search/suggestions', methods=['GET'])
def search_suggestions():
    """Autocompletado desde la primera letra.

    Busca en nombre, clave (ACTI-xxx) y valores de atributos (DNI, N° de serie, IMEI...).
    Varias palabras se combinan con AND ("cas die" encuentra "CASAS PARISACA DIEGO").
    Orden: nombre que empieza por el texto, palabra del nombre que empieza por el texto,
    clave que empieza por el texto, y luego el resto. `type_id` limita a un tipo de objeto.
    """
    query = request.args.get('q', '', type=str).strip()
    type_id = request.args.get('type_id', None, type=int)
    limit = min(max(request.args.get('limit', 8, type=int), 1), 50)
    if not query:
        return jsonify({'status': 'success', 'data': [], 'total': 0}), 200

    attributes_text = db.cast(Asset.attributes, db.Text)
    base = Asset.query
    if type_id:
        base = base.filter(Asset.type_id == type_id)
    for token in query.split():
        base = base.filter(db.or_(
            Asset.name.ilike(f'%{token}%'),
            Asset.jira_key.ilike(f'%{token}%'),
            attributes_text.ilike(f'%{token}%')
        ))

    name_has_all_tokens = db.and_(*[Asset.name.ilike(f'%{token}%') for token in query.split()])
    rank = db.case(
        (Asset.jira_key.ilike(query), 0),
        (Asset.name.ilike(f'{query}%'), 1),
        (Asset.name.ilike(f'% {query}%'), 2),
        (Asset.jira_key.ilike(f'{query}%'), 3),
        (name_has_all_tokens, 4),
        else_=5
    )
    total = base.count()
    matches = base.order_by(rank, Asset.name).limit(limit).all()

    def matched_field(asset):
        """Si la coincidencia no está en nombre ni clave, indica en qué atributo está."""
        tokens = [t.lower() for t in query.split()]
        visible = f'{asset.name} {asset.jira_key}'.lower()
        if all(t in visible for t in tokens):
            return None
        for name, value in (asset.attributes or {}).items():
            text = ', '.join(map(str, value)) if isinstance(value, list) else str(value or '')
            if any(t in text.lower() for t in tokens) and not text.startswith('data:'):
                # Algunos atributos llegan de Jira con su ID numérico como nombre: no se muestra.
                return {'name': None if str(name).isdigit() else name, 'value': text[:80]}
        return None

    data = [{
        'id': asset.id,
        'jira_key': asset.jira_key,
        'name': asset.name,
        'type_id': asset.type_id,
        'type_name': asset.asset_type.name if asset.asset_type else None,
        'matched_field': matched_field(asset)
    } for asset in matches]
    return jsonify({'status': 'success', 'data': data, 'total': total}), 200


@app.route('/api/search', methods=['GET'])
def search():
    try:
        query = request.args.get('q', '', type=str).strip()
        if len(query) < 2:
            return jsonify({'status': 'error', 'message': 'Mínimo 2 caracteres'}), 400

        results = Asset.query.filter(
            db.or_(
                Asset.name.ilike(f'%{query}%'),
                Asset.jira_key.ilike(f'%{query}%'),
                db.cast(Asset.attributes, db.Text).ilike(f'%{query}%')
            )
        ).limit(50).all()

        return jsonify({'status': 'success', 'total': len(results), 'data': [a.to_dict() for a in results]}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ===========================
# RELACIONES
# ===========================

@app.route('/api/relations', methods=['GET'])
def get_relations():
    try:
        source_id = request.args.get('source_id', None, type=int)
        target_id = request.args.get('target_id', None, type=int)
        query = AssetRelation.query
        if source_id:
            query = query.filter_by(source_asset_id=source_id)
        if target_id:
            query = query.filter_by(target_asset_id=target_id)
        relations = query.all()
        return jsonify({'status': 'success', 'total': len(relations), 'data': [r.to_dict() for r in relations]}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/relations', methods=['POST'])
def create_relation():
    try:
        data = request.get_json()
        if not all(k in data for k in ['source_asset_id', 'target_asset_id', 'relation_type']):
            return jsonify({'status': 'error', 'message': 'Faltan datos requeridos'}), 400

        source = Asset.query.get(data['source_asset_id'])
        target = Asset.query.get(data['target_asset_id'])
        if not source or not target:
            return jsonify({'status': 'error', 'message': 'Activos no encontrados'}), 404

        existing = AssetRelation.query.filter_by(
            source_asset_id=data['source_asset_id'],
            target_asset_id=data['target_asset_id'],
            relation_type=data['relation_type']
        ).first()
        if existing:
            return jsonify({'status': 'error', 'message': 'La relación ya existe'}), 400

        relation = AssetRelation(
            source_asset_id=data['source_asset_id'],
            target_asset_id=data['target_asset_id'],
            relation_type=data['relation_type']
        )
        db.session.add(relation)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Relación creada', 'data': relation.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/relations/<int:relation_id>', methods=['DELETE'])
def delete_relation(relation_id):
    try:
        relation = AssetRelation.query.get(relation_id)
        if not relation:
            return jsonify({'status': 'error', 'message': 'No encontrado'}), 404
        db.session.delete(relation)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Relación eliminada'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ===========================
# ERRORES
# ===========================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'status': 'error', 'message': 'Ruta no encontrada'}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({'status': 'error', 'message': 'Error interno del servidor'}), 500


if __name__ == '__main__':
    logger.info("Iniciando Ferco Medical Assets Manager API...")
    app.run(debug=os.getenv('FLASK_DEBUG', '0') == '1', host='0.0.0.0', port=5000)
