import socket
import json
import time
import threading
import sys
import select

HOST_LOCAL = "192.168.1.9"  # Ajusta tu IP local aquí
PUERTO_TCP = 65432

# Estado de simulación global
modo_bucle = "1"  # Por defecto arranca en rutina 1 (Mesa vacía)

def escucha_teclado():
    global modo_bucle
    print("[*] Controles del teclado activos. Presiona [1, 2, 3, 4] + Enter para cambiar de rutina:")
    print("    1: Mesa Vacía")
    print("    2: Postura Correcta")
    print("    3: Mala Postura Crítica")
    print("    4: Anomalía Luminosa Crítica")
    
    while True:
        linea = sys.stdin.readline().strip()
        if linea in ["1", "2", "3", "4"]:
            modo_bucle = linea
            print(f"\n[!] Cambiando manualmente a Rutina Bucle: {modo_bucle}")

def escuchar_comandos_pasivos(sock):
    """Escucha datos concurrentes enviados de forma pasiva desde Python."""
    while True:
        try:
            raw_msg = sock.recv(1024).decode('utf-8')
            if not raw_msg:
                break
            
            evento = json.loads(raw_msg.strip())
            tipo = evento.get("tipo")
            
            if tipo == "pomodoro":
                print(f"\n[<- DOWNSTREAM POMODORO] Conc: {evento['en_concentracion']} | Desc: {evento['en_descanso']}")
            elif tipo in ["config_dist", "config_lux"]:
                print(f"\n[<- DOWNSTREAM CONFIG] Actualización de umbrales: {evento}")
                
        except Exception:
            break

def iniciar_simulador():
    global modo_bucle
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        sock.connect((HOST_LOCAL, PUERTO_TCP))
        print(f"[+] Conectado al servidor TCP en {HOST_LOCAL}:{PUERTO_TCP}")
        
        # Levantar hilos asíncronos de entrada y salida pasiva
        threading.Thread(target=escucha_teclado, daemon=True).start()
        threading.Thread(target=escuchar_comandos_pasivos, args=(sock,), daemon=True).start()
        
        while True:
            # Generar datos basados en el modo seleccionado por el teclado
            if modo_bucle == "1":
                dist, lux = 100, 800  # Vacío
            elif modo_bucle == "2":
                dist, lux = 75, 550   # Óptimo analógico
            elif modo_bucle == "3":
                dist, lux = 42, 650   # Muy cerca
            elif modo_bucle == "4":
                dist, lux = 76, 150   # Oscuridad analógica (ADC bajo)

            # Enviar telemetría regular (disminuimos prints drásticamente aquí)
            telemetria = {"distancia": dist, "luminosidad": lux}
            sock.sendall(json.dumps(telemetria).encode('utf-8'))
            
            time.sleep(1.5)  # Ráfaga pausada para limpiar terminal
            
    except ConnectionRefusedError:
        print("[-] El backend no está corriendo.")
    except KeyboardInterrupt:
        print("\n[-] Simulador cerrado.")
    finally:
        sock.close()

if __name__ == "__main__":
    iniciar_simulador()