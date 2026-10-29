@echo off
echo ====================================
echo Jira Assets Manager - Instalacion
echo ====================================
echo.

echo [1/3] Backend - Instalando dependencias Python...
cd /d "c:\Users\temporal\Desktop\JIRA\backend"
pip install -r requirements.txt
if errorlevel 1 (
    echo Error al instalar backend
    pause
    exit /b 1
)

echo [2/3] Frontend - Instalando dependencias Node.js...
cd /d "c:\Users\temporal\Desktop\JIRA\frontend"
call npm install
if errorlevel 1 (
    echo Error al instalar frontend
    pause
    exit /b 1
)

echo.
echo ====================================
echo Instalacion completada!
echo ====================================
echo.
echo Para iniciar el servidor:
echo   - Backend: cd backend && python app.py
echo   - Frontend: cd frontend && npm run dev
echo.
pause
