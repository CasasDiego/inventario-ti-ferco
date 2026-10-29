# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Ferco Medical Assets Manager — a local web app that syncs IT assets from **Jira Assets (JSM)** into a local SQLite database and exposes them through a Flask REST API and a React SPA. It is not a Jira plugin; it's a standalone app that periodically pulls a snapshot of Jira Assets data and lets users browse/search/edit that local copy.

## Commands

### Backend (Flask, Python)
```bash
cd backend
pip install -r requirements.txt
python app.py                    # runs on http://localhost:5000 (set FLASK_DEBUG=1 for debug mode)
```
There is no test suite or linter configured for the backend.

Standalone scripts (run from `backend/`, require `.env` credentials):
- `python export_jira.py --verbose` — pulls data from Jira Assets and dumps it to `jira_assets_export.json`, independent of the running API. Useful for testing the Jira connection/credentials without touching the local DB.
- `python migrate_from_jira.py` — one-off migration script.
- `python migrate_sqlite_to_postgres.py "<postgres-url>"` — copies the local SQLite DB into an empty Postgres DB (creates tables, preserves ids, resets sequences, verifies row counts).
- `check_jira.py`, `check_pagination.py`, `find_endpoint.py`, `get_attr_map.py`, `inspect_data.py` — ad hoc debugging scripts used while reverse-engineering the Jira Assets API; not part of the app's runtime.

### Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev        # http://localhost:3000, proxies /api/* to localhost:5000 (see vite.config.js)
npm run build
npm run lint        # eslint . --ext .jsx
```

### Docker
```bash
docker-compose up   # backend on :5000, frontend (built + nginx) on :3000
```
Requires `JIRA_URL`, `JIRA_EMAIL`, `JIRA_TOKEN` in the environment/`.env`.

### Environment
`backend/.env` (not committed) must define:
```
JIRA_URL=https://ferco-medical.atlassian.net
JIRA_EMAIL=...
JIRA_TOKEN=...
JIRA_WORKSPACE_ID=       # optional — auto-detected from JIRA_URL if omitted
DATABASE_URL=             # empty = SQLite at instance/jira_assets.db; production = Postgres URL
SECRET_KEY=
SESSION_COOKIE_SECURE=0   # 1 behind HTTPS
ADMIN_PASSWORD=           # only used to seed the admin user if missing
```
See `backend/.env.example`.

### Deployment
Production runs on Postgres (Neon/Supabase) via `DATABASE_URL` + Render (`render.yaml`: Flask web service + static frontend that rewrites `/api/*` to the backend so session cookies stay same-origin). Gunicorn must run with **one worker** (threads are fine) because `_sync_status` is in-process memory. Step-by-step guide in `DEPLOY.md`.

## Architecture

**Two independent processes, no shared code**: `backend/` (Flask API + SQLAlchemy models + Jira sync logic) and `frontend/` (React SPA). They only talk over HTTP; the Vite dev server proxies `/api` to the Flask server.

### Data flow: Jira → local DB → API → UI
1. `backend/export_jira.py` (`JiraAssetsExporter`) is the only code that talks to the real Jira Assets API. It resolves the workspace ID, queries object schemas/types/attribute definitions, and pulls all objects via AQL (`POST /object/aql`) with pagination. `normalize_object()` converts Jira's raw attribute-value structure into a flat `{attr_name: value}` dict using the attribute-definition map (attribute IDs → human-readable names).
2. `backend/app.py`'s `_run_sync()` (triggered by `POST /api/sync`, runs in a background thread, tracked via the in-memory `_sync_status` dict and persisted `SyncLog` rows) drives the exporter, upserts `AssetType` and `Asset` rows by `jira_type_id`/`jira_id`, and separately walks each object's `objectAttributeValues` looking for `referencedObject` links to build `AssetRelation` rows. This is the only place Jira data enters the local DB — everything else in the API reads/writes only the local SQLite copy.
3. `backend/models.py` defines the local schema: `User` (local login only, unrelated to Jira), `AssetType`, `Asset` (self-referential `parent_id` for hierarchy, `attributes` as a JSON blob, unique on `jira_id`), `AssetRelation` (directed source→target links with a free-text `relation_type`), `SyncLog`.
4. `backend/app.py` exposes REST endpoints over that local DB (assets CRUD, search, CSV export, hierarchy tree, relations, sync trigger/status/logs). Session-based auth (`flask.session`) gates every `/api/*` route except `/api/health`, `/api/auth/login`, `/api/auth/me` — see `require_login()`.
5. `frontend/src/App.jsx` checks `/api/auth/me` on load to decide between `Login` and the routed app (`Dashboard`, `AssetsList`, `AssetDetail`, `AssetHierarchy`) under `react-router-dom`. Pages call the API directly with `axios` (no client-side state library) using relative `/api/...` paths, relying on the Vite proxy in dev and same-origin nginx in Docker.

### Key implication for changes
Because `Asset.attributes` is an untyped JSON blob keyed by whatever attribute names Jira exposes (translated through `get_attribute_definitions`), there's no fixed schema for asset fields — UI code that reads specific attribute keys (e.g. "Usuario Final", "Marca" in `/api/assets/options`) is coupled to naming conventions in the live Jira instance's schema 2 ("Activos de Ti"), not to anything enforced in code.

### Per-type field definitions (frontend-only convention)
Since attribute schemas aren't stored anywhere queryable, the frontend hardcodes per-type field lists that mirror the real Jira object type's attributes: `USER_FIELDS`/`EQUIPMENT_FIELDS` in `AssetDetail.jsx` (which fields to show/edit on an existing asset, merged with whatever keys are actually present in `asset.attributes`), and `TYPE_FIELDS` in `CreateAssetModal.jsx` (which fields to render in the "Crear objeto" modal, keyed by `AssetType.name`, currently only defined for `Celular`; other types fall back to a bare `Nombre` field). Adding proper support for a new object type means adding its field list to `TYPE_FIELDS` — and usually to `EQUIPMENT_FIELDS`/`USER_FIELDS` too if it should also render richly on the detail page. Reference-type fields (attributes that point to another asset, e.g. "Usuario Final" → an `Asset` of type `Usuario`, "Fabricante" → type `Marca`) are handled separately via `AssetRelation` rows, not `attributes`, and are rendered with the shared `ReferenceField` component (`components/ReferenceField.jsx`) backed by `GET /api/assets/options?kind=users|brands`. `POST /api/assets` and `PUT /api/assets/<id>` both accept an optional `references: {field_name: target_asset_id}` payload to create/replace these relation rows.
