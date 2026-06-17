# src/test/simulador_arduino.py
import socket
import json
import time

# Configuración de red (Apunta al Servidor de Python)
HOST_LOCAL = "127.0.0.1"
PUERTO_TCP = 65432

def iniciar_simulador_con_rutinas():
    print("=== [SIMULADOR] Iniciando Emulación con Rutinas Cotidianas ===")
    
    # Umbrales configurados localmente en la memoria del "Arduino"
    umbrales = {
        "distMin": 70,
        "distMax": 80,
        "luxMin": 4000,
        "luxMax": 5000
    }
    
    # Definición de los escenarios secuenciales (Nombre, Duración en segundos)
    escenarios = [
        {"nombre": "MESA_VACIA", "duracion": 8},
        {"nombre": "POSTURA_CORRECTA", "duracion": 12},
        {"nombre": "MALA_POSTURA_PROGRESIVA", "duracion": 15},
        {"nombre": "ANOMALIA_LUMINOSA_CRITICA", "duracion": 12}
    ]
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        sock.connect((HOST_LOCAL, PUERTO_TCP))
        print(f"[+] Conectado al backend en {HOST_LOCAL}:{PUERTO_TCP}")
        
        indice_escenario = 0
        segundo_actual = 0
        
        # Variables base para simular variaciones físicas suaves
        distancia_base = 150 # cm
        luminosidad_base = 4500 # lx
        
        while True:
            escenario = escenarios[indice_escenario]
            nombre_esc = escenario["nombre"]
            
            # --- RUTINAS DE COMPORTAMIENTO COTIDIANO ---
            if nombre_esc == "MESA_VACIA":
                # Simula que no hay nadie (Distancia muy alta y luz ambiente normal)
                distancia_medida = 160
                luminosidad_medida = 4200
                
            elif nombre_esc == "POSTURA_CORRECTA":
                # Simula que el usuario se sienta en el rango ideal de [70, 80]
                distancia_medida = 75 
                luminosidad_medida = 4600
                
            elif nombre_esc == "MALA_POSTURA_PROGRESIVA":
                # Simula que el usuario empieza en un rango bajo [60, 65] y cae a una medición críticamente baja
                if segundo_actual < 5:
                    distancia_medida = 63  # Rango bajo de advertencia
                else:
                    distancia_medida = 45  # Medición muy baja (Anomalía crítica / Encorvado)
                luminosidad_medida = 4400
                
            elif nombre_esc == "ANOMALIA_LUMINOSA_CRITICA":
                # El usuario vuelve a estar a buena distancia pero la luz cae drásticamente de forma anormal
                distancia_medida = 76
                if segundo_actual < 4:
                    distancia_medida = 76
                    luminosidad_medida = 3800 # Rango bajo de advertencia
                else:
                    luminosidad_medida = 1200 # Medición anormal crítica (Oscuridad / Falla ambiental)

            # Enviar el paquete de telemetría por el socket en formato JSON
            telemetria = {
                "distancia": distancia_medida,
                "luminosidad": luminosidad_medida
            }
            sock.sendall(json.dumps(telemetria).encode('utf-8'))
            
            print(f"[{nombre_esc} - {segundo_actual}s] -> Telemetría enviada: Dist={distancia_medida}cm, Luz={luminosidad_medida}lx")
            
            # Escuchar de forma inmediata si hay respuesta de sincronización del backend
            try:
                respuesta = sock.recv(1024).decode('utf-8')
                if respuesta:
                    nuevos_umbrales = json.loads(respuesta.strip())
                    if nuevos_umbrales["distMin"] != umbrales["distMin"]:
                        print(f"     [<- Hardware Sync] Umbrales actualizados desde Web: DistMin={nuevos_umbrales['distMin']}cm")
                        umbrales.update(nuevos_umbrales)
            except Exception:
                pass
            
            # Control del tiempo y transiciones de los escenarios
            time.sleep(1)
            segundo_actual += 1
            
            if segundo_actual >= escenario["duracion"]:
                segundo_actual = 0
                indice_escenario = (indice_escenario + 1) % len(escenarios)
                print("\n" + "="*70)
                print(f"[*] TRANSICIÓN DE RUTINA -> Cambiando a: {escenarios[indice_escenario]['nombre']}")
                print("="*70)
                
    except ConnectionRefusedError:
        print("[-] Error: El backend (`main.py`) no está corriendo.")
    except KeyboardInterrupt:
        print("\n[-] Simulador por escenarios apagado.")
    finally:
        sock.close()

if __name__ == "__main__":
    iniciar_simulador_con_rutinas()