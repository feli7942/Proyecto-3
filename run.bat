@style off
echo ===================================================
echo   Levantando Entorno del Asistente de Escritorio
echo ===================================================

:: 0. Verificación de Python en el sistema
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [-] Error: Python no se encuentra instalado o no esta en el PATH.
    echo [*] Intentando instalar Python de forma automatizada via winget...
    
    where winget >nul 2>nul
    if %errorlevel% eq 0 (
        winget install --id Python.Python.3.11 --exact --silent
        echo [+] Instalacion completada de forma silenciosa. Por favor, reinicie este script.
        pause
        exit
    ) else (
        echo [-] No se detecto winget. Abriendo la tienda de Microsoft para instalar Python...
        start ms-windows-store://search?query=Python
        echo [!] Instale Python desde la tienda y vuelva a ejecutar este archivo.
        pause
        exit
    )
)

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