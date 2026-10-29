# Script de instalación rápida para Jira Assets Local - Windows
# Ejecutar como: powershell -ExecutionPolicy Bypass -File setup.ps1

Write-Host "================================" -ForegroundColor Green
Write-Host "Jira Assets Local - Setup" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""

# Verificar Python
Write-Host "Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "✓ Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python no encontrado. Descárgalo desde https://www.python.org" -ForegroundColor Red
    exit 1
}

# Verificar Node.js
Write-Host "Verificando Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host "✓ Node.js encontrado: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js no encontrado. Descárgalo desde https://nodejs.org" -ForegroundColor Red
    exit 1
}

# Instalar dependencias de Backend
Write-Host ""
Write-Host "Instalando dependencias del Backend..." -ForegroundColor Yellow
Push-Location backend
pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Backend configurado" -ForegroundColor Green
} else {
    Write-Host "✗ Error instalando dependencias de backend" -ForegroundColor Red
    exit 1
}
Pop-Location

# Instalar dependencias de Frontend
Write-Host ""
Write-Host "Instalando dependencias del Frontend..." -ForegroundColor Yellow
Push-Location frontend
npm install
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Frontend configurado" -ForegroundColor Green
} else {
    Write-Host "✗ Error instalando dependencias de frontend" -ForegroundColor Red
    exit 1
}
Pop-Location

# Crear archivo .env si no existe
Write-Host ""
Write-Host "Configurando variables de entorno..." -ForegroundColor Yellow

$envFile = "backend\.env"
if (!(Test-Path $envFile)) {
    Write-Host "✓ Archivo .env creado en backend/" -ForegroundColor Green
    Write-Host "  Por favor, edita backend\.env con tus credenciales de Jira" -ForegroundColor Cyan
} else {
    Write-Host "ℹ Archivo .env ya existe" -ForegroundColor Blue
}

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "✓ Instalación completada" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos pasos:" -ForegroundColor Yellow
Write-Host "1. Abre backend\.env y configura tus credenciales de Jira" -ForegroundColor White
Write-Host "2. Abre 2 PowerShell:" -ForegroundColor White
Write-Host ""
Write-Host "   Terminal 1 (Backend):" -ForegroundColor Cyan
Write-Host "   cd backend" -ForegroundColor White
Write-Host "   python app.py" -ForegroundColor White
Write-Host ""
Write-Host "   Terminal 2 (Frontend):" -ForegroundColor Cyan
Write-Host "   cd frontend" -ForegroundColor White
Write-Host "   npm run dev" -ForegroundColor White
Write-Host ""
Write-Host "3. Abre http://localhost:3000 en tu navegador" -ForegroundColor White
Write-Host ""
