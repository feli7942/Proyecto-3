import socket
from pathlib import Path
from modelo import TelemetriaDesk
from servidores import ServidorHardware, crear_app_web


def obtener_ip_local():
    """Detecta dinámicamente la IP de la interfaz de red activa."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


if __name__ == '__main__':
    print("=== Inicializando Asistente de Escritorio (Modo Modular) ===")
    
    # Manejo multiplataforma de rutas (Windows/Linux)
    BASE_DIR = Path(__file__).resolve().parent.parent
    FRONTEND_DIR = BASE_DIR / "frontend"
    
    # Parámetros de Red
    IP_LECTURA = obtener_ip_local()
    PUERTO_HARDWARE = 65432
    PUERTO_WEB = 5000
    
    # 1. Instanciar el modelo compartido de datos
    modelo_compartido = TelemetriaDesk()
    
    # 2. Inicializar y arrancar el servidor de sockets (Hardware WiFi)
    hilo_socket = ServidorHardware(IP_LECTURA, PUERTO_HARDWARE, modelo_compartido)
    hilo_socket.start()
    
    # 3. Inicializar y correr el servidor de la aplicación web (Flask)
    app_web = crear_app_web(modelo_compartido, FRONTEND_DIR)
    
    print(f"[+] Interfaz en ejecución: http://localhost:{PUERTO_WEB}/")
    print(f"[+] Servidor TCP listo para recibir al ESP8266 en {IP_LECTURA}:{PUERTO_HARDWARE}")
    
    app_web.run(host='0.0.0.0', port=PUERTO_WEB, debug=False, use_reloader=False)
