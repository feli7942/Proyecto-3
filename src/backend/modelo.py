import threading

class TelemetriaDesk:
    """Clase contenedora del estado actual del Asistente de Escritorio."""
    def __init__(self):
        # Lecturas en tiempo real de los sensores
        self.distancia = 80       # Valor por defecto (cm)
        self.luminosidad = 4500   # Valor por defecto (luxes/K) - Escala ajustada a miles
        self.estado_fsm = 0       # 0: Vacío, 1: Enfoque, 2: Alerta
        
        # Umbrales configurables dinámicamente desde la interfaz web
        self.dist_min = 70
        self.dist_max = 80
        self.lux_min = 4000
        self.lux_max = 5000
        
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
                "estado": self.estado_fsm,
                "distMin": self.dist_min,
                "distMax": self.dist_max,
                "luxMin": self.lux_min,
                "luxMax": self.lux_max
            }