import socket
import threading
import json
from flask import Flask, jsonify, send_from_directory, request 
from flask_cors import CORS

# Lista global para rastrear conexiones TCP activas con hardware o simuladores
dispositivos_conectados = []
lock_dispositivos = threading.Lock()

def transmitir_a_hardware(data_dict):
    """Envía de forma pasiva e inmediata un comando a todos los Arduinos conectados."""
    payload = (json.dumps(data_dict) + "\n").encode('utf-8')
    with lock_dispositivos:
        for sock in dispositivos_conectados[:]:
            try:
                sock.sendall(payload)
            except Exception:
                dispositivos_conectados.remove(sock)

class ServidorHardware(threading.Thread):
    def __init__(self, host, port, modelo_datos):
        super().__init__()
        self.host = host
        self.port = port
        self.modelo = modelo_datos
        self.running = True
        self.daemon = True

    def run(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            print(f"[*] Servidor de Sockets activo en {self.host}:{self.port}")
            
            while self.running:
                try:
                    server_socket.settimeout(1.0)
                    client_socket, addr = server_socket.accept()
                    with lock_dispositivos:
                        dispositivos_conectados.append(client_socket)
                    
                    hilo = threading.Thread(target=self._atender_dispositivo, args=(client_socket, addr))
                    hilo.daemon = True
                    hilo.start()
                except socket.timeout:
                    continue
        except Exception as e:
            print(f"[-] Error en el servidor de hardware: {e}")
        finally:
            server_socket.close()

    def _atender_dispositivo(self, client_socket, addr):
        print(f"[+] Conexión establecida desde hardware/test en la IP: {addr}")
        while self.running:
            try:
                raw_data = client_socket.recv(1024).decode('utf-8')
                if not raw_data:
                    break
                
                datos = json.loads(raw_data.strip())
                dist = int(datos.get("distancia", 80))
                lux = int(datos.get("luminosidad", 500)) # Ahora escala 0-1023
                
                # FSM básica
                estado = 1 if (70 <= dist <= 80) else 2
                self.modelo.actualizar(dist, lux, estado)
                
            except json.JSONDecodeError:
                pass
            except Exception:
                break
        print(f"[-] Dispositivo desconectado de la IP: {addr}")
        with lock_dispositivos:
            if client_socket in dispositivos_conectados:
                dispositivos_conectados.remove(client_socket)
        client_socket.close()


def crear_app_web(modelo_datos, ruta_frontend):
    import logging
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    app = Flask(__name__)
    CORS(app)

    @app.route('/')
    def index(): return send_from_directory(ruta_frontend, 'index.html')

    @app.route('/<path:filename>')
    def serve_static(filename): return send_from_directory(ruta_frontend, filename)

    @app.route('/api/telemetria', methods=['GET'])
    def get_telemetria(): return jsonify(modelo_datos.obtener_datos())
    
    @app.route('/api/configurar/distancia', methods=['POST'])
    def configurar_distancia():
        datos = request.get_json()
        transmitir_a_hardware({"tipo": "config_dist", "min": datos.get('min'), "max": datos.get('max')})
        return jsonify({"status": "success"})

    @app.route('/api/configurar/luz', methods=['POST'])
    def configurar_luz():
        datos = request.get_json()
        transmitir_a_hardware({"tipo": "config_lux", "min": datos.get('min'), "max": datos.get('max')})
        return jsonify({"status": "success"})

    @app.route('/api/configurar/pomodoro', methods=['POST'])
    def configurar_pomodoro():
        datos = request.get_json()
        transmitir_a_hardware({
            "tipo": "pomodoro",
            "en_concentracion": datos.get('en_concentracion'),
            "en_descanso": datos.get('en_descanso')
        })
        return jsonify({"status": "success"})

    return app