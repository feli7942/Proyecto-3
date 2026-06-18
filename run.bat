@off 
echo ===================================================
echo   Levantando Entorno del Asistente de Escritorio
echo ===================================================

:: 1. Verificar si existe el entorno virtual, si no, crearlo
if not exist venv (
    echo [-] No se detecto entorno virtual. Creando venv...
    python -m venv venv
)

:: 2. Activar entorno virtual
call venv\Scripts\activate

:: 3. Instalar/Actualizar requerimientos en silencio
echo [*] Verificando e instalando dependencias desde requirements.txt...
pip install -r requirements.txt --quiet

:: 4. Abrir el navegador en la app web de forma automática
echo [+] Abriendo interfaz web en el navegador...
start http://localhost:5000

:: 5. Ejecutar la aplicación principal
echo [+] Iniciando Backend central...
python src/backend/main.py

pause