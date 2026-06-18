#!/bin/bash
echo "==================================================="
echo "  Levantando Entorno del Asistente de Escritorio"
echo "==================================================="

# 1. Verificar si existe venv, si no, crearlo
if [ ! -d "venv" ]; then
    echo "[-] No se detectó entorno virtual. Creando venv..."
    python3 -m venv venv
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