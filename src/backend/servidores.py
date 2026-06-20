import serial
import serial.tools.list_ports
import threading
import time
import logging
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
 
# ============================================================================
#  Protocolo sobre el cable serial (texto plano, una linea por mensaje):
#      Arduino -> PC (telemetria):   "D:<dist>,L:<lux>,E:<estado>"
#      PC -> Arduino (comandos):     "CD:<min>,<max>"   config distancia
#                                    "CL:<min>,<max>"   config luz
#                                    "CP:<conc>,<desc>" config pomodoro (0/1)
# ============================================================================
 
# ----------------------------------------------------------------------------
#  Configuracion del puerto
#  Windows:  "COM3", "COM4", ...
#  Linux:    "/dev/ttyACM0" (UNO original) o "/dev/ttyUSB0" (clones CH340)
#  macOS:    "/dev/cu.usbmodemXXXX" o "/dev/cu.usbserial-XXXX"
#  Si se deja en None, se intenta autodetectar.
# ----------------------------------------------------------------------------
PUERTO_SERIAL = "COM8"      # ej. "COM3"  -> None = autodetectar
BAUDIOS = 9600
 
# ----------------------------------------------------------------------------
#  Estado global de la conexion (reemplaza la lista de sockets)
# ----------------------------------------------------------------------------
conexion_serial = None
lock_serial = threading.Lock()
hardware_conectado = False
ultimo_estado_conectado = False
 
 
# ----------------------------------------------------------------------------
#  Traduccion dict <-> linea serial
# ----------------------------------------------------------------------------
def _dict_a_linea(data_dict):
    """Convierte un comando (dict) en la linea de texto que entiende el Arduino."""
    tipo = data_dict.get("tipo")
    if tipo == "config_dist":
        return f"CD:{int(data_dict['min'])},{int(data_dict['max'])}\n"
    if tipo == "config_lux":
        return f"CL:{int(data_dict['min'])},{int(data_dict['max'])}\n"
    if tipo == "pomodoro":
        conc = 1 if data_dict.get("en_concentracion") else 0
        desc = 1 if data_dict.get("en_descanso") else 0
        return f"CP:{conc},{desc}\n"
    return None
 
 
def _parse_linea(linea):
    """Convierte 'D:65,L:350,E:1' en (dist, lux, estado). Devuelve None si no es valida."""
    try:
        campos = {}
        for parte in linea.split(","):
            clave, valor = parte.split(":")
            campos[clave.strip()] = int(valor.strip())
        return campos["D"], campos["L"], campos.get("E", 0)
    except (ValueError, KeyError):
        return None
 
 
def detectar_puerto_arduino():
    """Busca un puerto que parezca un Arduino. Devuelve el nombre o None."""
    claves = ("arduino", "ch340", "usb serial", "wch", "ttyacm", "ttyusb", "usbmodem", "usbserial")
    for p in serial.tools.list_ports.comports():
        texto = f"{p.device} {p.description} {p.manufacturer}".lower()
        if any(k in texto for k in claves):
            return p.device
    return None
 
 
# ----------------------------------------------------------------------------
#  Envio de comandos al hardware (misma firma que antes: recibe un dict)
# ----------------------------------------------------------------------------
def transmitir_a_hardware(data_dict):
    """Envia de forma inmediata un comando al Arduino conectado por serial."""
    linea = _dict_a_linea(data_dict)
    if not linea:
        return
    with lock_serial:
        if conexion_serial and conexion_serial.is_open:
            try:
                conexion_serial.write(linea.encode("utf-8"))
            except Exception:
                pass
 
 
# ----------------------------------------------------------------------------
#  Hilo lector del puerto serial (reemplaza a ServidorHardware con sockets)
#  Se mantiene el nombre ServidorHardware para no romper el import en main.py,
#  pero el constructor ahora recibe (puerto, baudios, modelo_datos).
# ----------------------------------------------------------------------------
class ServidorHardware(threading.Thread):
    def __init__(self, puerto, baudios, modelo_datos):
        super().__init__()
        self.puerto = puerto
        self.baudios = baudios
        self.modelo = modelo_datos
        self.running = True
        self.daemon = True
 
    def run(self):
        global conexion_serial, hardware_conectado
 
        while self.running:
            puerto = self.puerto or detectar_puerto_arduino()
            if not puerto:
                print("[-] No se encontro ningun puerto de Arduino. Reintentando...")
                time.sleep(2)
                continue
 
            try:
                ser = serial.Serial(puerto, self.baudios, timeout=1)
            except serial.SerialException as e:
                print(f"[-] No se pudo abrir {puerto}: {e}. Reintentando...")
                time.sleep(2)
                continue
 
            with lock_serial:
                conexion_serial = ser
 
            # El Arduino se reinicia al abrir el puerto: esperar el arranque.
            time.sleep(2)
            hardware_conectado = True
            print(f"[+] Conectado al Arduino por serial en {puerto}")
 
            self._leer_bucle(ser)
 
            # Salio del bucle -> desconexion
            hardware_conectado = False
            with lock_serial:
                conexion_serial = None
            try:
                ser.close()
            except Exception:
                pass
            print(f"[-] Arduino desconectado de {puerto}")
            time.sleep(2)  # reintentar conexion
 
    def _leer_bucle(self, ser):
        while self.running:
            try:
                raw = ser.readline().decode("utf-8", errors="ignore").strip()
            except Exception:
                break          # puerto cerrado o desconectado fisicamente
            if not raw:
                continue        # timeout sin datos
 
            datos = _parse_linea(raw)
            if datos is None:
                continue        # linea incompleta o ruido
 
            dist, lux, estado = datos
            # El Arduino es el dueno de la FSM, asi que usamos el estado que el reporta.
            # (En la version socket se recalculaba aqui; si prefieres eso, descomenta:)
            # estado = 1 if (self.modelo.dist_min <= dist <= self.modelo.dist_max) else 2
            self.modelo.actualizar(dist, lux, estado)
 
 
# ----------------------------------------------------------------------------
#  Sincronizacion en reconexion (igual que antes, pero basada en el flag serial)
# ----------------------------------------------------------------------------
def actualizar_dispositivos_y_sincronizar(modelo_datos):
    global ultimo_estado_conectado
    actualmente_conectado = hardware_conectado
 
    # Al pasar de desconectado -> conectado, mandamos la rafaga de configuracion.
    if actualmente_conectado and not ultimo_estado_conectado:
        print("[*] Dispositivo detectado! Transmitiendo configuracion inicial...")
        transmitir_a_hardware({
            "tipo": "config_dist",
            "min": getattr(modelo_datos, "dist_min", 70),
            "max": getattr(modelo_datos, "dist_max", 80),
        })
        time.sleep(0.1)
        transmitir_a_hardware({
            "tipo": "config_lux",
            "min": getattr(modelo_datos, "lux_min", 500),
            "max": getattr(modelo_datos, "lux_max", 1000),
        })
 
    ultimo_estado_conectado = actualmente_conectado
    return actualmente_conectado
 
 
# ----------------------------------------------------------------------------
#  App web (sin cambios: las rutas y el contrato con el frontend son iguales)
# ----------------------------------------------------------------------------
def crear_app_web(modelo_datos, ruta_frontend):
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
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
        conectado = actualizar_dispositivos_y_sincronizar(modelo_datos)
        dict_datos = modelo_datos.obtener_datos()
        dict_datos["hardware_conectado"] = conectado
        return jsonify(dict_datos)
 
    @app.route('/api/configurar/distancia', methods=['POST'])
    def configurar_distancia():
        datos = request.get_json()
        min_val = datos.get('min')
        max_val = datos.get('max')
        with modelo_datos.lock:
            modelo_datos.dist_min = min_val
            modelo_datos.dist_max = max_val
        transmitir_a_hardware({"tipo": "config_dist", "min": min_val, "max": max_val})
        return jsonify({"status": "success"})
 
    @app.route('/api/configurar/luz', methods=['POST'])
    def configurar_luz():
        datos = request.get_json()
        min_val = datos.get('min')
        max_val = datos.get('max')
        with modelo_datos.lock:
            modelo_datos.lux_min = min_val
            modelo_datos.lux_max = max_val
        transmitir_a_hardware({"tipo": "config_lux", "min": min_val, "max": max_val})
        return jsonify({"status": "success"})
 
    @app.route('/api/configurar/pomodoro', methods=['POST'])
    def configurar_pomodoro():
        datos = request.get_json()
        transmitir_a_hardware({
            "tipo": "pomodoro",
            "en_concentracion": datos.get('en_concentracion'),
            "en_descanso": datos.get('en_descanso'),
        })
        return jsonify({"status": "success"})
 
    return app