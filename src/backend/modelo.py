import threading


class TelemetriaDesk:
    """Clase contenedora del estado actual del Asistente de Escritorio."""
    def __init__(self):
        self.distancia = 80       # Valor por defecto (cm)
        self.luminosidad = 400    # Valor por defecto (luxes)
        self.estado_fsm = 0       # 0: Vacío, 1: Enfoque, 2: Alerta
        self.lock = threading.Lock() # Exclusor mutuo para hilos

    def actualizar(self, distancia, luminosidad, estado):
        """Escribe de manera segura los datos provenientes del hardware."""
        with self.lock:
            self.distancia = distancia
            self.luminosidad = luminosidad
            self.estado_fsm = estado

    def obtener_datos(self):
        """Retorna una copia de los datos actuales para la API web."""
        with self.lock:
            return {
                "distancia": self.distancia,
                "luminosidad": self.luminosidad,
                "estado": self.estado_fsm
            }
