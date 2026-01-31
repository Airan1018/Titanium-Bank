@echo off
title Instalador CoreDoc Titan - Windows
echo ====================================================
echo   INSTALADOR AUTOMATICO PARA WINDOWS 11 (TITAN)
echo ====================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado. Por favor instalo desde python.org
    pause
    exit
)

echo [1/3] Actualizando PIP...
python -m pip install --upgrade pip

echo [2/3] Instalando librerias necesarias...
pip install pandas openpyxl fpdf qrcode requests beautifulsoup4

echo [3/3] Iniciando CoreDoc Titan Ultra v5.7...
python "Tu_Archivo_Python.py"

pause