import os
from dotenv import load_dotenv

load_dotenv()


def _database_url():
    url = os.getenv('DATABASE_URL', '')
    if not url:
        base_dir = os.path.abspath(os.path.dirname(__file__))
        return f'sqlite:///{os.path.join(base_dir, "instance", "jira_assets.db")}'
    # Algunos proveedores (Heroku, Render) entregan "postgres://", que SQLAlchemy 2 ya no acepta
    if url.startswith('postgres://'):
        url = 'postgresql://' + url[len('postgres://'):]
    return url


class Config:
    JIRA_URL = os.getenv('JIRA_URL', 'https://ferco-medical.atlassian.net')
    JIRA_EMAIL = os.getenv('JIRA_EMAIL')
    JIRA_TOKEN = os.getenv('JIRA_TOKEN')
    JIRA_WORKSPACE_ID = os.getenv('JIRA_WORKSPACE_ID', '')

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Postgres gestionado (Neon/Supabase) cierra conexiones inactivas; verificar antes de reutilizarlas
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True, 'pool_recycle': 300}

    SECRET_KEY = os.getenv('SECRET_KEY', 'ferco-medical-change-in-production')
    # En producción (HTTPS) la cookie de sesión solo debe viajar cifrada
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', '0') == '1'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')

    JSON_SORT_KEYS = False
