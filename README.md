# Jira Assets Export - Gestor Local de Activos de TI

Una solución completa para exportar, sincronizar y gestionar tus activos de Jira Assets en una aplicación web local.

## 🎯 Características

- ✅ **Sincronización automática** con Jira Assets via API
- ✅ **Base de datos local** (SQLite) para acceso rápido
- ✅ **API REST** completa con Flask
- ✅ **Interfaz web moderna** con React + Vite + Tailwind
- ✅ **Visualización jerárquica** de activos
- ✅ **Búsqueda y filtros** avanzados
- ✅ **Gestión de relaciones** entre activos
- ✅ **Historial de sincronizaciones**

## 🚀 Instalación Rápida

### Requisitos
- Python 3.8+
- Node.js 16+ y npm
- Git

### Paso 1: Clonar/Descargar el proyecto

```bash
cd c:\Users\temporal\Desktop\JIRA
```

### Paso 2: Configurar variables de entorno

Copia las credenciales de Jira al archivo `.env` del backend:

```bash
cd backend
# Edita backend\.env con tus credenciales
```

Tu archivo `.env` debe contener:
```
JIRA_URL=https://ferco-medical.atlassian.net
JIRA_EMAIL=tu-email@ferco-medical.com
JIRA_TOKEN=tu-api-token
DATABASE_URL=sqlite:///jira_assets.db
```

### Paso 3: Instalar dependencias - Backend

```bash
cd backend
pip install -r requirements.txt
```

### Paso 4: Instalar dependencias - Frontend

```bash
cd frontend
npm install
```

## 📦 Ejecutar la aplicación

### Opción A: Terminal separadas (Recomendado para desarrollo)

**Terminal 1 - Backend (API REST)**
```bash
cd backend
python app.py
# La API estará disponible en http://localhost:5000
```

**Terminal 2 - Frontend (Aplicación Web)**
```bash
cd frontend
npm run dev
# La web estará disponible en http://localhost:3000
```

### Opción B: Docker Compose (Producción)

```bash
docker-compose up
```

## 🔄 Sincronizar datos desde Jira

### Opción 1: Via interfaz web
1. Abre http://localhost:3000
2. Ve al Dashboard
3. Haz clic en "Sincronizar Ahora"

### Opción 2: Via API REST
```bash
curl -X POST http://localhost:5000/api/sync \
  -H "Content-Type: application/json"
```

### Opción 3: Script Python directo
```bash
cd backend
python export_jira.py --verbose
```

## 📚 API REST - Endpoints disponibles

### Salud y Info
- `GET /api/health` - Estado de la API
- `GET /api/info` - Información general

### Sincronización
- `POST /api/sync` - Iniciar sincronización
- `GET /api/sync/logs` - Historial de sincronizaciones

### Tipos de Activos
- `GET /api/asset-types` - Listar todos los tipos
- `GET /api/asset-types/<id>` - Detalles de un tipo

### Activos
- `GET /api/assets` - Listar activos (paginado, filtrable)
- `GET /api/assets/<id>` - Detalles de un activo
- `POST /api/assets` - Crear nuevo activo
- `PUT /api/assets/<id>` - Actualizar activo
- `DELETE /api/assets/<id>` - Eliminar activo

### Búsqueda y Jerarquía
- `GET /api/search?q=<query>` - Búsqueda global
- `GET /api/assets/tree/hierarchy` - Árbol jerárquico de activos

### Ejemplos de uso

```bash
# Obtener 10 laptops
curl "http://localhost:5000/api/assets?search=laptop&per_page=10"

# Buscar todos los activos
curl "http://localhost:5000/api/assets?page=1&per_page=50"

# Filtrar por tipo (ID del tipo)
curl "http://localhost:5000/api/assets?type_id=1"

# Búsqueda global
curl "http://localhost:5000/api/search?q=CPU"

# Obtener jerarquía completa
curl "http://localhost:5000/api/assets/tree/hierarchy"
```

## 📂 Estructura del proyecto

```
JIRA/
├── backend/
│   ├── app.py                 # Aplicación Flask principal
│   ├── models.py              # Modelos de SQLAlchemy
│   ├── config.py              # Configuración
│   ├── export_jira.py         # Script de exportación
│   ├── requirements.txt        # Dependencias Python
│   ├── .env                   # Variables de entorno (NO compartir)
│   └── jira_assets.db         # Base de datos SQLite (se crea automáticamente)
│
├── frontend/
│   ├── src/
│   │   ├── components/        # Componentes React reutilizables
│   │   ├── pages/             # Páginas principales
│   │   ├── App.jsx            # Componente principal
│   │   ├── main.jsx           # Entry point
│   │   └── index.css          # Estilos globales
│   ├── public/                # Archivos estáticos
│   ├── index.html             # HTML principal
│   ├── package.json           # Dependencias Node
│   └── vite.config.js         # Configuración Vite
│
└── docker-compose.yml         # Configuración Docker
```

## 🔐 Seguridad

**IMPORTANTE:** Nunca compartas tu archivo `.env` con credenciales en público.

Para producción:
1. Cambia la `SECRET_KEY` en `backend/config.py`
2. Usa variables de entorno del sistema
3. Implementa autenticación en la aplicación
4. Usa HTTPS
5. Configura CORS apropiadamente

## 🐛 Solución de problemas

### Error: "No se pudo conectar a Jira Assets"

1. Verifica que tu email y API token sean correctos
2. Asegúrate de que la URL de Jira es accesible
3. Comprueba que tienes permisos en Jira Assets

```bash
# Test de conexión
cd backend
python export_jira.py --verbose
```

### Error: "Base de datos bloqueada"

SQLite solo permite una escritura a la vez. Si la sincronización falla:

```bash
# Elimina la BD y reinicia
cd backend
rm jira_assets.db
python app.py
```

### Frontend no conecta con Backend

Asegúrate de que:
1. Backend está ejecutándose en `http://localhost:5000`
2. El proxy en `vite.config.js` está configurado correctamente
3. CORS está habilitado en Flask

## 📈 Próximas mejoras

- [ ] Autenticación de usuarios
- [ ] Edición de activos en la interfaz
- [ ] Exportación a Excel/CSV
- [ ] Gráficos de análisis
- [ ] Webhooks para sincronización automática
- [ ] Soporte para PostgreSQL
- [ ] Multilingual support

## 📞 Contacto y Soporte

Para problemas o sugerencias, abre un issue o contacta al equipo de TI.

## 📄 Licencia

Privado - Uso interno únicamente

---

**Última actualización:** 2026-01-14  
**Versión:** 1.0.0
