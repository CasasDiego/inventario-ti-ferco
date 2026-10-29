@echo off
REM Script para ejecutar Jira Assets Local en Windows
REM Este script abre dos ventanas de terminal, una para el backend y otra para el frontend

echo.
echo ================================
echo Jira Assets Local - Iniciando
echo ================================
echo.

REM Verificar si estamos en el directorio correcto
if not exist "backend\app.py" (
    echo Error: Asegúrate de ejecutar este script desde la raíz del proyecto
    pause
    exit /b 1
)

REM Abrir Backend en nueva ventana
echo Iniciando Backend (http://localhost:5000)...
start "Jira Assets - Backend" cmd /k "cd backend && python app.py"

REM Esperar un poco para que el backend inicie
timeout /t 3

REM Abrir Frontend en nueva ventana
echo Iniciando Frontend (http://localhost:3000)...
start "Jira Assets - Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Esperando a que los servidores inicien...
timeout /t 5

echo.
echo ================================
echo ✓ Aplicación iniciada
echo ================================
echo.
echo Backend: http://localhost:5000
echo Frontend: http://localhost:3000
echo.
echo Abre tu navegador en http://localhost:3000
echo.
pause
