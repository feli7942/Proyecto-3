import socket
import threading
import time
import random
from flask import Flask, jsonify, send_from_directory, request 
from flask_cors import CORS


class ServidorHardware(threading.Thread):
    """Hilo encargado de escuchar la conexión TCP inalámbrica del ESP8266."""
    def __init__(self, host, port, modelo_datos):
        super().__init__()
        self.host = host
        self.port = port
        self.modelo = modelo_datos
        self.running = True
        self.daemon = True # Cierre limpio al apagar main.py

    def run(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind((self.host, self.port))
            server_socket.listen(1)
            print(f"[*] Servidor de Sockets activo en {self.host}:{self.port}")
            
            while self.running:
                # Simulador activo en ausencia de hardware real
                self._simular_hardware_offline()
                
                # TODO: Descomentar este bloque al integrar el Arduino físico
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
            print(f"[-] Error en el servidor de hardware: {e}")
        finally:
            server_socket.close()

    def _parsear_trama(self, trama):
        """Parsea tramas enviadas por WiFi, ej: D:75,L:320,E:1\\n"""
        try:
            partes = trama.strip().split(',')
            dist = int(partes[0].split(':')[1])
            lux = int(partes[1].split(':')[1])
            est = int(partes[2].split(':')[1])
            self.modelo.actualizar(dist, lux, est)
        except Exception:
            print(f"[!] Trama WiFi corrupta o incompleta: {trama}")

    def _simular_hardware_offline(self):
        """Simulador de respaldo para pruebas de GUI aisladas."""
        d = random.randint(60, 90)
        l = random.randint(2500, 7500)

        e = 1 if (70 <= d <= 80) else 2
        self.modelo.actualizar(d, l, e)


def crear_app_web(modelo_datos, ruta_frontend):
    """Fábrica de la aplicación web Flask y sus Endpoints."""
    import logging
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    # =====================================================================

    app = Flask(__name__)
    CORS(app)

    @app.route('/')
    def index():
        return send_from_directory(ruta_frontend, 'index.html')

    @app.route('/<path:filename>')
    def serve_static(filename):
        return send_from_directory(ruta_frontend, filename)

    @app.route('/api/telemetria', methods=['GET'])
    def get_telemetria():
        return jsonify(modelo_datos.obtener_datos())
    
    @app.route('/api/configurar/distancia', methods=['POST'])
    def configurar_distancia():
        datos = request.get_json()
        min_dist = datos.get('min')
        max_dist = datos.get('max')
        
        print(f"[*] Nueva configuración de distancia recibida: Min={min_dist}cm, Max={max_dist}cm")
        return jsonify({"status": "success", "message": "Umbrales de distancia configurados"})

    @app.route('/api/configurar/luz', methods=['POST'])
    def configurar_luz():
        datos = request.get_json()
        min_luz = datos.get('min')
        max_luz = datos.get('max')

        print(f"[*] Nueva configuración de luz recibida: Min={min_luz} lx, Max={max_luz} lx")
        return jsonify({"status": "success", "message": "Umbral de luz configurado"})

    return app
