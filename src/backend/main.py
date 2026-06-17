import socket
import threading
import time
import os
from pathlib import Path
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS


# =====================================================================
# 1. MODELO DE DATOS (PROGRAMACIÓN ORIENTADA A OBJETOS)
# =====================================================================
class TelemetriaDesk:
    """Clase contenedora del estado actual del Asistente de Escritorio"""
    def __init__(self):
        self.distancia = 80             # Valor por defecto (cm)
        self.luminosidad = 400          # Valor por defecto (luxes)
        self.estado_fsm = 0             # 0: Vacio, 1: Enfoque, 2: Alerta
        self.lock = threading.Lock()    # Evita colisiones entre hilos

    def actualizar(self, distancia, luminosidad, estado):
        with self.lock:
            self.distancia = distancia
            self.luminosidad = luminosidad
            self.estado_fsm = estado

    def obtener_datos(self):
        with self.lock:
            return {
                "distancia": self.distancia,
                "luminosidad": self.luminosidad,
                "estado": self.estado_fsm
            }


# =====================================================================
# 2. SERVIDOR DE HARDWARE (HILO PARA ANTLENA WIFI / SOCKETS)
# =====================================================================
class ServidorHardware(threading.Thread):
    """Hilo encargado de escuchar la conexion TCP"""
    def __init__(self, host, port, modelo_datos):
        super().__init__()
        self.host = host
        self.port = port
        self.modelo = modelo_datos
        self.running = True
        self.daemon = True

    def run(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockpot(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            server_socket.bind((self.host, self.port))
            server_socket.listen(1)
            print(f"[*] Servidor de Sockets activo en {self.host}:{self.port}")

            while self.running:
                self._simular_hardware_offline()

                # Descomentar el bloque inferior cuando conecten el Arduino físico:
                """
                client_socket, addr = server_socket.accept()
                print(f"[+] Arduino conectado desde la IP: {addr}")
                while self.running:
                    trama = client_socket.recv(1024).decode('utf-8')
                    if not trama:
                        break
                    self._parsear_trama(trama)
                client_socket.close()
                """
                time.sleep(0.5)
        except Exception as e:
            print(f"[-] Error critico en el servidor de hardware: {e}") 
        finally: 
            server_socket.close()

    def _parsear_trama(self, trama):
        """Parsea strings tipo: D:75,L:320,E:1\\n"""
        try:
            # Limpiar caracteres raros de red
            partes = trama.strip().split(',')
            dist = int(partes[0].split(':')[1])
            lux = int(partes[1].split(':')[1])
            est = int(partes[2].split(':')[1])
            self.modelo.actualizar(dist, lux, est)
        except Exception:
            print(f"[!] Trama corrupta o incompleta recibida por WiFi: {trama}")

    def _simular_hardware_offline(self):
        """Simulador de respaldo interno para pruebas de software aisladas."""
        import random
        d = random.randint(60, 90)
        l = random.randint(200, 500)
        e = 1 if (70 <= d <= 80) else 2
        self.modelo.actualizar(d, l, e)


# =====================================================================
# 3. CAPA DE BACKEND WEB (FLASK) Y ENLACE AL FRONTEND
# =====================================================================
def crear_app_web(modelo_datos, ruta_frontend):
    app = Flask(__name__)
    CORS(app) # Previene bloqueos CORS locales de los navegadores

    # Ruta raíz: sirve el archivo index.html
    @app.route('/')
    def index():
        return send_from_directory(ruta_frontend, 'index.html')

    # Ruta estática: sirve los estilos css y lógica js automáticamente
    @app.route('/<path:filename>')
    def serve_static(filename):
        return send_from_directory(ruta_frontend, filename)

    # API ENDPOINT: Envía las variables de los sensores al Frontend
    @app.route('/api/telemetria', methods=['GET'])
    def get_telemetria():
        return jsonify(modelo_datos.get_datos())

    return app


# =====================================================================
# 4. ORQUESTADOR PRINCIPAL (MÓDULO DE CONTROL CENTRAL)
# =====================================================================
def obtener_ip_local():
    """Detecta de forma dinámica la IP de red inalámbrica del equipo actual."""
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
    print("=== Inicializando Sistema del Asistente de Escritorio ===")
    
    # Configuración de Rutas multiplataforma (Windows/Linux tolerante)
    BASE_DIR = Path(__file__).resolve().parent.parent
    FRONTEND_DIR = BASE_DIR / "frontend"
    
    # Red local
    IP_LOCAL = obtener_ip_local()
    PUERTO_HARDWARE = 65432  # Puerto TCP libre para el ESP8266
    PUERTO_WEB = 5000       # Puerto HTTP para ver la interfaz en el navegador
    
    # Inicialización de componentes orientados a objetos
    modelo_compartido = TelemetriaDesk()
    
    # Arrancar Hilo de Hardware
    hilo_socket = ServidorHardware(IP_LOCAL, PUERTO_HARDWARE, modelo_compartido)
    hilo_socket.start()
    
    # Arrancar Servidor de Aplicación Web en el hilo principal
    app_web = crear_app_web(modelo_compartido, FRONTEND_DIR)
    
    print(f"[+] Interfaz gráfica disponible en: http://localhost:{PUERTO_WEB}/")
    print(f"[+] Configure el ESP8266 del Arduino para apuntar a la IP: {IP_LOCAL} al puerto: {PUERTO_HARDWARE}")
    
    app_web.run(host='0.0.0.0', port=PUERTO_WEB, debug=False, use_reloader=False)