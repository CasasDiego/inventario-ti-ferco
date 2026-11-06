# Publicar online (gratis): Neon + Render

Arquitectura: **Postgres en Neon** (la base de datos, persiste siempre) + **backend Flask en Render** + **frontend React como sitio estático en Render**. El frontend reenvía `/api/*` al backend, así que todo se ve desde un solo dominio.

## 1. Crear la base Postgres (Neon)
1. Crear cuenta en https://neon.tech y un proyecto nuevo (región más cercana, p. ej. São Paulo / US East).
2. Copiar la **connection string** (`postgresql://usuario:clave@ep-xxx.neon.tech/neondb?sslmode=require`).
   Guárdala bien: es la contraseña de tu base.

> Supabase también sirve: usar la connection string de *Session pooler* (Project Settings → Database).

## 2. Migrar los datos actuales (desde tu PC)
```bash
cd backend
pip install -r requirements.txt
python migrate_sqlite_to_postgres.py "postgresql://...tu-connection-string..."
```
Copia usuarios, tipos, activos, relaciones, actividad y logs, y al final compara los conteos (todos deben decir `OK`). Si la base destino ya tiene datos, se detiene para no duplicar.

## 3. Subir el código a GitHub
Render despliega desde un repositorio. El `.gitignore` ya excluye `.env`, la base local y el export de Jira — **nunca subas `backend/.env`**.
```bash
git init
git add .
git commit -m "Preparar despliegue"
# crear un repo PRIVADO en GitHub y luego:
git remote add origin https://github.com/<usuario>/<repo>.git
git push -u origin main
```

## 4. Desplegar en Render
1. Crear cuenta en https://render.com y conectar GitHub.
2. **New → Blueprint** → elegir el repo. Render lee `render.yaml` y crea los dos servicios.
3. Completar las variables que pide (`sync: false`):
   - `DATABASE_URL` → la connection string de Neon
   - `JIRA_EMAIL`, `JIRA_TOKEN` → los mismos de tu `backend/.env`
   - `ADMIN_PASSWORD` → **obligatorio**. Es la contraseña de la única cuenta (`dcasas@ferco-medical.com`): al arrancar, si no coincide con la guardada, la reemplaza. Cambiarla aquí y reiniciar el servicio cambia la contraseña. Usa una larga y única.
4. Verificar la URL que Render le dio al backend (`ferco-assets-api`). Si **no** es `https://ferco-assets-api.onrender.com`, editar el destino de la regla `/api/*` en `render.yaml`, hacer commit y push.
5. Abrir la URL del frontend (`https://ferco-assets.onrender.com` o similar) e iniciar sesión.

## A tener en cuenta (plan gratuito)
- El backend de Render **se duerme tras ~15 min sin uso**; el primer acceso después tarda ~30–60 s en despertar. Los datos no se pierden (están en Neon).
- Un sync con Jira en curso puede cortarse si el servicio se reinicia; basta con lanzarlo de nuevo.
- Cambia la contraseña del admin si todavía es `admin123`: ahora la app es accesible desde internet.
