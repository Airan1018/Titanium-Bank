#!/bin/bash
echo "===================================================="
echo "   INSTALADOR AUTOMATICO PARA LINUX / UBUNTU"
echo "===================================================="

# Actualizar repositorios e instalar pip si no existe
sudo apt update
sudo apt install -y python3-pip python3-tk

echo "[1/2] Instalando librerias de Python..."
pip3 install pandas openpyxl fpdf qrcode requests beautifulsoup4

echo "[2/2] Configurando permisos de ejecucion..."
chmod +x "Tu_Archivo_Python.py"

echo "Iniciando CoreDoc Titan..."
python3 "Tu_Archivo_Python.py"