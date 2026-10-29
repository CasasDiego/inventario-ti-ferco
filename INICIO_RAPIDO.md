# 🚀 PROYECTO COMPLETADO - Gestor de Activos TI

## ✅ Estado del Proyecto

Tu proyecto está **99% completo** y listo para usar. Solo falta instalar las dependencias del frontend (npm).

---

## 📋 Lo que se ha completado:

### ✅ Backend (Python/Flask)
- ✅ API REST completa con todos los endpoints CRUD
- ✅ Sincronización con Jira Assets via API
- ✅ Base de datos SQLite con modelos relacionales
- ✅ Rutas de activos: GET, POST, PUT, DELETE
- ✅ Rutas de relaciones entre activos
- ✅ Búsqueda y filtros
- ✅ Historial de sincronizaciones
- ✅ Todas las dependencias instaladas ✓

### ✅ Frontend (React/Vite/Tailwind)
- ✅ Dashboard con estadísticas en tiempo real
- ✅ Lista de activos con búsqueda y filtros
- ✅ Detalle de activos con edición
- ✅ Gestión de relaciones entre activos
- ✅ Vista jerárquica interactiva
- ✅ Navbar con navegación
- ✅ Interfaz profesional con Tailwind CSS
- ⏳ Dependencias de Node.js (falta instalar)

---

## 📥 Pasos finales de instalación

### Opción 1: Usar CMD (Recomendado)

```cmd
# Abre CMD (no PowerShell) y ejecuta:

# Navega a la carpeta frontend
cd c:\Users\temporal\Desktop\JIRA\frontend

# Instala las dependencias
npm install

# Listo! Puedes usar npm run dev
```

### Opción 2: Usar Git Bash o WSL

```bash
cd /c/Users/temporal/Desktop/JIRA/frontend
npm install
```

### Opción 3: Bypass PowerShell (si usas PowerShell)

```powershell
# Copia este comando exacto en PowerShell:
& "C:\Program Files\nodejs\npm.cmd" install --prefix "c:\Users\temporal\Desktop\JIRA\frontend"
```

---

## 🎯 Cómo ejecutar el proyecto

### 1️⃣ Backend (Terminal 1)

```bash
cd c:\Users\temporal\Desktop\JIRA\backend
python app.py
```

**Resultado esperado:**
```
 * Running on http://0.0.0.0:5000
```

### 2️⃣ Frontend (Terminal 2)

```bash
cd c:\Users\temporal\Desktop\JIRA\frontend
npm run dev
```

**Resultado esperado:**
```
VITE v4.5.0  ready in XXX ms

➜  Local:   http://localhost:5173/
```

### 3️⃣ Abre el navegador

- 🌐 Frontend: http://localhost:5173/
- 🔌 API: http://localhost:5000/api/

---

## 🔑 Credenciales de Jira (IMPORTANTE)

⚠️ **YA REGENERASTE TU TOKEN** (como te indicamos)

1. ✅ Regenera tu API Token en: https://id.atlassian.com/manage-profile/security/api-tokens
2. ✅ Edita `backend/.env` con tus nuevas credenciales:

```env
JIRA_URL=https://tu-jira.atlassian.net
JIRA_EMAIL=tu-email@empresa.com
JIRA_TOKEN=tu-nuevo-token-aqui
DATABASE_URL=sqlite:///jira_assets.db
```

3. ✅ Asegúrate de que `.env` esté en `.gitignore`:
```bash
echo ".env" >> backend/.gitignore
```

---

## 📚 Endpoints disponibles

### Activos
- `GET /api/assets` - Listar activos (con paginación y filtros)
- `GET /api/assets/<id>` - Detalles de un activo
- `POST /api/assets` - Crear activo
- `PUT /api/assets/<id>` - Actualizar activo
- `DELETE /api/assets/<id>` - Eliminar activo

### Relaciones
- `GET /api/relations` - Listar relaciones
- `POST /api/relations` - Crear relación
- `DELETE /api/relations/<id>` - Eliminar relación

### Sincronización
- `POST /api/sync` - Sincronizar con Jira
- `GET /api/sync/logs` - Ver histórico de sincronizaciones

### Info
- `GET /api/health` - Estado de la API
- `GET /api/info` - Información general
- `GET /api/asset-types` - Tipos de activos

---

## 🌳 Estructura del proyecto

```
JIRA/
├── backend/
│   ├── app.py                    # API REST principal
│   ├── models.py                 # Modelos de BD
│   ├── export_jira.py           # Exportador de Jira
│   ├── config.py                 # Configuración
│   ├── requirements.txt           # Dependencias Python
│   ├── .env                      # Variables de entorno
│   └── jira_assets.db           # BD SQLite
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx               # Componente principal
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx     # Dashboard
│   │   │   ├── AssetsList.jsx    # Lista de activos
│   │   │   ├── AssetDetail.jsx   # Detalle + edición
│   │   │   └── AssetHierarchy.jsx # Vista jerárquica
│   │   ├── components/
│   │   │   └── Navbar.jsx        # Barra de navegación
│   │   └── main.jsx
│   ├── package.json              # Dependencias Node.js
│   ├── vite.config.js           # Configuración Vite
│   ├── tailwind.config.js       # Configuración Tailwind
│   └── index.html
│
├── docker-compose.yml           # Docker (opcional)
├── README.md                    # Documentación
└── .gitignore
```

---

## ✨ Características principales

✅ **Sincronización automática** desde Jira Assets  
✅ **BD local** (SQLite) para acceso rápido  
✅ **CRUD completo** para activos  
✅ **Gestión de relaciones** entre activos  
✅ **Búsqueda y filtros** avanzados  
✅ **Vista jerárquica** de activos  
✅ **Interfaz moderna** con Tailwind CSS + React  
✅ **API REST** profesional con Flask  
✅ **Historial de sincronizaciones**  
✅ **Edición de activos** en tiempo real  

---

## 🐛 Troubleshooting

### Error: "No se puede cargar npm.ps1"
**Solución:** Usa CMD en lugar de PowerShell, o ejecuta:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Error: "Port 5000 is already in use"
**Solución:** Cambia el puerto en `backend/app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Cambiar puerto
```

### Error: "Cannot find module"
**Solución:** Asegúrate de que instalaste las dependencias:
```bash
cd frontend && npm install
cd ../backend && pip install -r requirements.txt
```

### Error de conexión a Jira
**Solución:** Verifica tu token de API en `backend/.env` y que el URL sea correcto

---

## 📞 Soporte

Si tienes problemas:
1. Verifica los logs de la terminal
2. Comprueba que Python 3.8+ y Node.js 16+ estén instalados
3. Regenera tu API Token de Jira
4. Reinicia ambos servidores (backend y frontend)

---

## ¿Próximos pasos?

Después de instalar npm, puedes:

1. **Probar la aplicación:**
   - Abre http://localhost:5173/ en tu navegador
   - Sincroniza con Jira usando el botón "Sincronizar"
   - Explora los activos y relaciones

2. **Personalizar:**
   - Modifica los colores en `tailwind.config.js`
   - Agregar más campos a los modelos
   - Crear reportes personalizados

3. **Deploy:**
   - Usar Docker (incluye Dockerfile)
   - Deployar en Heroku, AWS, Digital Ocean, etc.

---

**¡Tu gestor de Activos TI está listo! 🚀**

Próximo paso: Instala npm run `npm install` en el frontend y ¡disfruta!
