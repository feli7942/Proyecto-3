from pathlib import Path
from modelo import TelemetriaDesk
from servidores import ServidorHardware, crear_app_web
 
 
if __name__ == '__main__':
    print("=== Inicializando Asistente de Escritorio (Modo Serial) ===")
 
    # Manejo multiplataforma de rutas (Windows/Linux)
    BASE_DIR = Path(__file__).resolve().parent.parent
    FRONTEND_DIR = BASE_DIR / "frontend"
 
    # Parametros del puerto serial del Arduino
    #   Windows:  "COM3", "COM4", ...
    #   Linux:    "/dev/ttyACM0" (UNO) o "/dev/ttyUSB0" (clones CH340)
    #   macOS:    "/dev/cu.usbmodemXXXX"
    #   None = autodetectar
    PUERTO_SERIAL = None
    BAUDIOS = 9600
    PUERTO_WEB = 5000
 
    # 1. Instanciar el modelo compartido de datos
    modelo_compartido = TelemetriaDesk()
 
    # 2. Inicializar y arrancar el lector del puerto serial (Hardware por USB)
    hilo_serial = ServidorHardware(PUERTO_SERIAL, BAUDIOS, modelo_compartido)
    hilo_serial.start()
 
    # 3. Inicializar y correr el servidor de la aplicacion web (Flask)
    app_web = crear_app_web(modelo_compartido, FRONTEND_DIR)
 
    print(f"[+] Interfaz en ejecucion: http://localhost:{PUERTO_WEB}/")
    print(f"[+] Esperando al Arduino por serial "
          f"({'autodeteccion' if PUERTO_SERIAL is None else PUERTO_SERIAL} @ {BAUDIOS} baudios)")
 
    app_web.run(host='0.0.0.0', port=PUERTO_WEB, debug=False, use_reloader=False)