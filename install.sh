#!/bin/bash
# Script de instalacion para Jira Assets Manager

echo "===================================="
echo "Jira Assets Manager - Instalacion"
echo "===================================="
echo ""

echo "[1/3] Backend - Instalando dependencias Python..."
cd "c:/Users/temporal/Desktop/JIRA/backend" || exit 1
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error al instalar backend"
    exit 1
fi

echo "[2/3] Frontend - Instalando dependencias Node.js..."
cd "c:/Users/temporal/Desktop/JIRA/frontend" || exit 1
npm install
if [ $? -ne 0 ]; then
    echo "Error al instalar frontend"
    exit 1
fi

echo ""
echo "===================================="
echo "Instalacion completada!"
echo "===================================="
echo ""
echo "Para iniciar el servidor:"
echo "  - Backend: cd backend && python app.py"
echo "  - Frontend: cd frontend && npm run dev"
echo ""
