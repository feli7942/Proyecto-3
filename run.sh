#!/bin/bash
echo "==================================================="
echo "  Levantando Entorno del Asistente de Escritorio"
echo "==================================================="

# 0. Verificar si Python3 está instalado
if ! command -v python3 &> /dev/null; then
    echo "[-] Error: Python3 no está instalado en este sistema."
    echo "[*] Para instalarlo, ejecute el siguiente comando en su terminal:"
    echo "    sudo apt update && sudo apt install python3 python3-venv python3-pip"
    exit 1
fi

# 1. Verificar si existe venv, si no, crearlo
if [ ! -d "venv" ]; then
    echo "[-] No se detectó entorno virtual. Creando venv..."
    # Verificar si el módulo venv de python está disponible (común en entornos limpios de Linux)
    if ! python3 -m venv venv &> /dev/null; then
        echo "[-] Error: Falta el paquete python3-venv."
        echo "[*] Ejecute: sudo apt install python3-venv"
        exit 1
    fi
fi

# 2. Activar entorno virtual
source venv/bin/activate

# 3. Instalar requerimientos
echo "[*] Verificando e instalando dependencias..."
pip install -r requirements.txt --quiet

# 4. Abrir navegador de forma asíncrona según el sistema de escritorio
echo "[+] Abriendo interfaz web en el navegador..."
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:5000 &
elif command -v gnome-open &> /dev/null; then
    gnome-open http://localhost:5000 &
fi

# 5. Ejecutar backend
echo "[+] Iniciando Backend central..."
python3 src/backend/main.py