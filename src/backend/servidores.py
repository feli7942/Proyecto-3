import socket
import threading
import time
import json
from flask import Flask, jsonify, send_from_directory, request 
from flask_cors import CORS


class ServidorHardware(threading.Thread):
    """Hilo encargado de escuchar la conexión TCP inalámbrica del ESP8266 o Simulador."""
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
            server_socket.listen(5)
            print(f"[*] Servidor de Sockets activo en {self.host}:{self.port}")
            
            while self.running:
                # El servidor se queda esperando conexiones de red reales o del simulador
                try:
                    server_socket.settimeout(1.0) # Evita quedarse congelado eternamente al cerrar
                    client_socket, addr = server_socket.accept()
                    
                    # Lanzar un hilo independiente por cada cliente conectado para no bloquear el loop
                    hilo_cliente = threading.Thread(target=self._atender_dispositivo, args=(client_socket, addr))
                    hilo_cliente.daemon = True
                    hilo_cliente.start()
                except socket.timeout:
                    continue
        except Exception as e:
            print(f"[-] Error en el servidor de hardware: {e}")
        finally:
            server_socket.close()

    def _atender_dispositivo(self, client_socket, addr):
        """Atiende la conexión continua de un dispositivo (simulador o Arduino)."""
        print(f"[+] Conexión establecida desde hardware/test en la IP: {addr}")
        client_socket.settimeout(5.0)
        
        while self.running:
            try:
                # 1. Recibir ráfaga JSON de telemetría
                raw_data = client_socket.recv(1024).decode('utf-8')
                if not raw_data:
                    break
                
                # Parsear JSON entrante
                datos = json.loads(raw_data.strip())
                dist = int(datos.get("distancia", 80))
                lux = int(datos.get("luminosidad", 4500))
                
                # Clasificar estado dinámico para la FSM según límites actuales
                estado = 1 if (70 <= dist <= 80) else 2
                
                # Inyectar datos en el modelo global para que Flask se los dé a app.js
                self.modelo.actualizar(dist, lux, estado)
                
                # 2. Leer umbrales actuales y responder de inmediato (Sincronización Downstream)
                # Nota: Si tu modelo.py aún no tiene estos atributos, puedes inicializarlos ahí o pasarlos directo
                limites_actuales = {
                    "distMin": getattr(self.modelo, 'dist_min', 70),
                    "distMax": getattr(self.modelo, 'dist_max', 80),
                    "luxMin": getattr(self.modelo, 'lux_min', 4000),
                    "luxMax": getattr(self.modelo, 'lux_max', 5000)
                }
                
                # Enviar respuesta de sincronización
                client_socket.sendall((json.dumps(limites_actuales) + "\n").encode('utf-8'))
                
            except json.JSONDecodeError:
                print(f"[!] Error de parseo en ráfaga JSON: {raw_data}")
            except (socket.timeout, ConnectionResetError):
                break
            except Exception as e:
                print(f"[-] Excepción en hilo de dispositivo: {e}")
                break
                
        print(f"[-] Dispositivo desconectado de la IP: {addr}")
        client_socket.close()


def crear_app_web(modelo_datos, ruta_frontend):
    """Fábrica de la aplicación web Flask y sus Endpoints."""
    import logging
    logging.getLogger('werkzeug').setLevel(logging.ERROR)

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
        
        # Guardar en las variables dinámicas del modelo para el downstream del socket
        modelo_datos.dist_min = min_dist
        modelo_datos.dist_max = max_dist
        
        print(f"[*] Nueva configuración de distancia recibida: Min={min_dist}cm, Max={max_dist}cm")
        return jsonify({"status": "success", "message": "Umbrales de distancia configurados"})

    @app.route('/api/configurar/luz', methods=['POST'])
    def configurar_luz():
        datos = request.get_json()
        min_luz = datos.get('min')
        max_luz = datos.get('max')

        # Guardar en las variables dinámicas del modelo para el downstream del socket
        modelo_datos.lux_min = min_luz
        modelo_datos.lux_max = max_luz

        print(f"[*] Nueva configuración de luz recibida: Min={min_luz} lx, Max={max_luz} lx")
        return jsonify({"status": "success", "message": "Umbral de luz configurado"})

    return app