from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class User(db.Model):
    """Usuario local de acceso a la plataforma."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {'id': self.id, 'email': self.email, 'display_name': self.display_name}

class AssetType(db.Model):
    """Tipos de Activos (Activos de Hardware, Software, etc.)"""
    __tablename__ = 'asset_types'
    
    id = db.Column(db.Integer, primary_key=True)
    jira_type_id = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text)
    icon = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    assets = db.relationship('Asset', backref='asset_type', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'jira_type_id': self.jira_type_id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class Asset(db.Model):
    """Activos (elementos específicos como laptops, CPUs, etc.)"""
    __tablename__ = 'assets'
    
    id = db.Column(db.Integer, primary_key=True)
    jira_key = db.Column(db.String(50), nullable=False, index=True)
    jira_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    type_id = db.Column(db.Integer, db.ForeignKey('asset_types.id'), nullable=False, index=True)
    
    # Atributos adicionales almacenados como JSON
    attributes = db.Column(db.JSON, default={})
    
    # Trazabilidad
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    jira_created_at = db.Column(db.DateTime)
    jira_updated_at = db.Column(db.DateTime)
    
    # Relaciones
    parent_id = db.Column(db.Integer, db.ForeignKey('assets.id'), index=True)
    parent = db.relationship('Asset', remote_side=[id], backref='children', foreign_keys=[parent_id])
    
    # Relaciones customizadas
    relationships = db.relationship(
        'AssetRelation',
        foreign_keys='AssetRelation.source_asset_id',
        backref='source_asset',
        lazy=True,
        cascade='all, delete-orphan'
    )
    
    def to_dict(self, include_children=False):
        data = {
            'id': self.id,
            'jira_key': self.jira_key,
            'jira_id': self.jira_id,
            'name': self.name,
            'type_id': self.type_id,
            'type_name': self.asset_type.name if self.asset_type else None,
            'attributes': self.attributes or {},
            'parent_id': self.parent_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'jira_created_at': self.jira_created_at.isoformat() if self.jira_created_at else None,
            'jira_updated_at': self.jira_updated_at.isoformat() if self.jira_updated_at else None,
        }
        
        if include_children and self.children:
            data['children'] = [child.to_dict(include_children=True) for child in self.children]
        
        return data


class AssetActivity(db.Model):
    """Historial de actividad de un Activo, importado desde Jira Assets."""
    __tablename__ = 'asset_activities'

    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False, index=True)
    jira_history_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    actor_name = db.Column(db.String(255))
    affected_attribute = db.Column(db.String(255))
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    change_type = db.Column(db.Integer)  # 0=creación, 2=modificación, 4=cambio de referencia (según Jira Assets)
    created_at = db.Column(db.DateTime, index=True)

    asset = db.relationship('Asset', backref=db.backref('activities', lazy=True, cascade='all, delete-orphan'))

    def to_dict(self):
        return {
            'id': self.id,
            'asset_id': self.asset_id,
            'actor_name': self.actor_name,
            'affected_attribute': self.affected_attribute,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'change_type': self.change_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class AssetRelation(db.Model):
    """Relaciones entre Activos"""
    __tablename__ = 'asset_relations'
    
    id = db.Column(db.Integer, primary_key=True)
    jira_relation_id = db.Column(db.String(255))
    source_asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False, index=True)
    target_asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False, index=True)
    relation_type = db.Column(db.String(100), nullable=False)  # "conectado_a", "contiene", etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    target_asset = db.relationship('Asset', foreign_keys=[target_asset_id], backref='linked_to')
    
    def to_dict(self):
        return {
            'id': self.id,
            'source_asset_id': self.source_asset_id,
            'target_asset_id': self.target_asset_id,
            'relation_type': self.relation_type,
            'created_at': self.created_at.isoformat()
        }


class SyncLog(db.Model):
    """Registro de sincronizaciones con Jira"""
    __tablename__ = 'sync_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    sync_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    status = db.Column(db.String(50), default='pending')  # pending, success, error
    total_assets = db.Column(db.Integer, default=0)
    total_relations = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    duration_seconds = db.Column(db.Float)
    
    def to_dict(self):
        return {
            'id': self.id,
            'sync_date': self.sync_date.isoformat(),
            'status': self.status,
            'total_assets': self.total_assets,
            'total_relations': self.total_relations,
            'error_message': self.error_message,
            'duration_seconds': self.duration_seconds
        }
