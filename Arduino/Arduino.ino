/*
 * ============================================================================
 *  Dispositivo inteligente de escritorio - Prototipo en hardware (Arduino UNO)
 *  Proyecto 3 - Modelacion de Hardware/Software con orientacion a objetos
 * ============================================================================
 *
 *  Implementa la maquina de estados de la Figura 3:
 *      DESK_EMPTY  <->  FOCUS_ON  <->  ALERT_ACTIVE
 *
 *  Comunicacion con la app de escritorio:
 *      - Puerto SERIAL (USB).
 *
 *  Protocolo:
 *      Arduino -> PC (telemetria, cada INTERVALO_TELEMETRIA ms):
 *          "D:<distancia_cm>,L:<nivel_luz>,E:<estado>"
 *          ejemplo:  D:65,L:350,E:1
 *
 *      PC -> Arduino (comandos), enviados por servidores_serial.py:
 *          "CD:<min>,<max>"    -> ajusta banda de distancia (cm)
 *          "CL:<min>,<max>"    -> ajusta banda de luz (valor crudo 0-1023)
 *          "CP:<conc>,<desc>"  -> estado del pomodoro (0/1); desc=1 avisa pausa
 *
 *  Librerias necesarias (Gestor de librerias del IDE de Arduino):
 *      - "LiquidCrystal I2C" de Frank de Brabander
 *
 *  Cableado:
 *      LCD I2C : SDA->A4, SCL->A5, VCC->5V, GND->GND
 *      HC-SR04 : Trig->D9, Echo->D10, VCC->5V, GND->GND
 *      Buzzer  : Senal->D8, VCC->5V, GND->GND   (modulo ACTIVO de 3 pines)
 *      LDR     : 5V -[LDR]- A0 -[10K]- GND       (divisor de voltaje)
 * ============================================================================
 */

#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// ---------------------------------------------------------------------------
//  Configuracion del LCD I2C
// ---------------------------------------------------------------------------
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ---------------------------------------------------------------------------
//  Pines
// ---------------------------------------------------------------------------
const uint8_t PIN_TRIG   = 9;    // HC-SR04 Trig
const uint8_t PIN_ECHO   = 10;   // HC-SR04 Echo
const uint8_t PIN_BUZZER = 8;    // Modulo buzzer ACTIVO (senal)
const uint8_t PIN_LDR    = A0;   // Foto-celda (divisor de voltaje)

// ---------------------------------------------------------------------------
//  Parametros configurables (se ajustan por Serial desde la app)
//  Rango ideal de distancia: [distMin, distMax]
//      distMin = limite de "muy cerca"
//      distMax = limite de "muy lejos" (aun presente)
//  Banda aceptable de luz: [luzMin, luzMax]  (valor crudo 0-1023)
//      El rango ideal de distancia se ajusta desde la app (CD:min,max)
// ---------------------------------------------------------------------------
// distMin/distMax = RANGO IDEAL de postura (igual que en el frontend).
//   distanciaCm < distMin  -> muy cerca
//   distanciaCm > distMax  -> muy lejos (pero todavia presente)
int distMin = 70;     // cm. Por debajo = muy cerca
int distMax = 80;     // cm. Por encima = muy lejos
int luzMin  = 300;    // por debajo = poca luz
int luzMax  = 900;    // por encima = demasiada luz

// Presencia: separada del rango ideal. Mas alla de esto = usuario ausente.
const int DIST_PRESENCIA = 150;  // cm

// ---------------------------------------------------------------------------
//  Tiempos (todo no-bloqueante con millis())
// ---------------------------------------------------------------------------
const unsigned long INTERVALO_SENSORES   = 200;   // ms entre lecturas
const unsigned long TIEMPO_ANOMALIA      = 5000;  // ms que debe durar la anomalia
const unsigned long INTERVALO_TELEMETRIA = 500;   // ms entre envios por Serial
const unsigned long PERIODO_BEEP         = 300;   // ms del parpadeo del buzzer

// ---------------------------------------------------------------------------
//  Estados de la FSM
// ---------------------------------------------------------------------------
enum Estado { DESK_EMPTY, FOCUS_ON, ALERT_ACTIVE };
Estado estado = DESK_EMPTY;

// ---------------------------------------------------------------------------
//  Variables de control
// ---------------------------------------------------------------------------
unsigned long tUltimaLectura    = 0;
unsigned long tUltimaTelemetria = 0;
unsigned long tInicioAnomalia   = 0;
unsigned long tUltimoBeep       = 0;

bool anomaliaPresente = false;
bool buzzerOn         = false;
bool alertaForzada    = false;   // alerta disparada por el Pomodoro del software

long distanciaCm = 999;
int  nivelLuz    = 0;

// ===========================================================================
//  SETUP
// ===========================================================================
void setup() {
  Serial.begin(9600);

  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  buzzerSet(false);

  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Iniciando...");
  delay(800);

  cambiarEstado(DESK_EMPTY);   // ejecuta las acciones de entrada del estado inicial
}

// ===========================================================================
//  LOOP
// ===========================================================================
void loop() {
  unsigned long ahora = millis();

  // 1) Lectura periodica de sensores + actualizacion de la FSM
  if (ahora - tUltimaLectura >= INTERVALO_SENSORES) {
    tUltimaLectura = ahora;
    distanciaCm = leerDistancia();
    nivelLuz    = leerLuz();
    actualizarFSM(ahora);
  }

  // 2) Buzzer intermitente mientras hay alerta
  if (estado == ALERT_ACTIVE && (ahora - tUltimoBeep >= PERIODO_BEEP)) {
    tUltimoBeep = ahora;
    buzzerSet(!buzzerOn);
  }

  // 3) Telemetria por Serial
  if (ahora - tUltimaTelemetria >= INTERVALO_TELEMETRIA) {
    tUltimaTelemetria = ahora;
    enviarTelemetria();
  }

  // 4) Comandos entrantes
  procesarSerial();
}

// ===========================================================================
//  Maquina de estados
// ===========================================================================
void actualizarFSM(unsigned long ahora) {
  bool usuarioPresente  = (distanciaCm <= DIST_PRESENCIA);
  bool distFueraDeRango = usuarioPresente && (distanciaCm < distMin || distanciaCm > distMax);
  bool luzMala          = (nivelLuz < luzMin) || (nivelLuz > luzMax);
  bool anomalia         = (distFueraDeRango || luzMala || alertaForzada);

  switch (estado) {

    case DESK_EMPTY:
      // Usuario Presente (Distancia <= DIST_PRESENCIA)
      if (usuarioPresente) cambiarEstado(FOCUS_ON);
      break;

    case FOCUS_ON:
      if (!usuarioPresente) {
        // Usuario Ausente (Distancia > DIST_PRESENCIA)
        cambiarEstado(DESK_EMPTY);
        anomaliaPresente = false;
      } else if (anomalia) {
        // Anomalia Detectada (postura fuera de rango o luz mala por > 5 seg)
        if (!anomaliaPresente) {
          anomaliaPresente = true;
          tInicioAnomalia  = ahora;
        } else if (ahora - tInicioAnomalia >= TIEMPO_ANOMALIA) {
          cambiarEstado(ALERT_ACTIVE);
        }
      } else {
        anomaliaPresente = false;
      }
      mostrarDatosFocus();   // refresca distancia y luz en el LCD
      break;

    case ALERT_ACTIVE:
      if (!usuarioPresente) {
        // Usuario Ausente (Distancia > DIST_PRESENCIA)
        cambiarEstado(DESK_EMPTY);
        anomaliaPresente = false;
        alertaForzada    = false;
      } else if (!anomalia) {
        // Variables Normalizadas (Distancia y Luz OK)
        cambiarEstado(FOCUS_ON);
        anomaliaPresente = false;
      }
      break;
  }
}

// ---------------------------------------------------------------------------
//  Acciones de entrada de cada estado (entry / ...)
// ---------------------------------------------------------------------------
void cambiarEstado(Estado nuevo) {
  estado = nuevo;

  switch (estado) {

    case DESK_EMPTY:
      lcd.clear();
      lcd.noBacklight();           // entry / Apagar retroiluminacion LCD
      buzzerSet(false);            // entry / Silenciar Buzzer
      Serial.println("E:0");       // entry / Enviar estado "E:0" por Serial
      break;

    case FOCUS_ON:
      lcd.backlight();             // entry / Encender retroiluminacion LCD
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Modo Focus: OK"); // entry / Mostrar en LCD
      buzzerSet(false);
      Serial.println("E:1");       // entry / Enviar estado "E:1" por Serial
      break;

    case ALERT_ACTIVE:
      lcd.backlight();
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("   ALERTA!");     // entry / Cambiar texto LCD a "ALERTA!"
      Serial.println("E:2");       // entry / Enviar estado "E:2" por Serial
      tUltimoBeep = millis();
      buzzerSet(true);             // entry / Activar Buzzer intermitente
      break;
  }
}

// ===========================================================================
//  Lectura de sensores
// ===========================================================================

// Distancia en cm con el HC-SR04. Devuelve 999 si no hay eco (muy lejos).
long leerDistancia() {
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);

  long duracion = pulseIn(PIN_ECHO, HIGH, 30000UL);  // timeout ~30 ms (~5 m)
  if (duracion == 0) return 999;
  return duracion / 58;   // conversion estandar de microsegundos a cm
}

// Nivel de luz crudo 0-1023 (mas alto = mas iluminado, segun el divisor).
int leerLuz() {
  return analogRead(PIN_LDR);
}

// ===========================================================================
//  Salidas
// ===========================================================================

// Buzzer ACTIVO: suena con la senal en HIGH.
// Si tu modulo suena al reves (con LOW), cambia HIGH/LOW por !on.
void buzzerSet(bool on) {
  digitalWrite(PIN_BUZZER, on ? HIGH : LOW);
  buzzerOn = on;
}

// Muestra distancia y luz en tiempo real durante FOCUS_ON.
// Se usa setCursor + relleno con espacios para evitar parpadeo.
void mostrarDatosFocus() {
  lcd.setCursor(0, 0);
  lcd.print("Dist:");
  lcd.print(distanciaCm);
  lcd.print("cm      ");

  lcd.setCursor(0, 1);
  lcd.print("Luz:");
  lcd.print(nivelLuz);
  bool luzOk = (nivelLuz >= luzMin && nivelLuz <= luzMax);
  lcd.print(luzOk ? " OK    " : " MALA  ");
}

// ===========================================================================
//  Comunicacion Serial
// ===========================================================================

// Envia "D:<dist>,L:<luz>,E:<estado>"
void enviarTelemetria() {
  Serial.print("D:");
  Serial.print(distanciaCm);
  Serial.print(",L:");
  Serial.print(nivelLuz);
  Serial.print(",E:");
  Serial.println((int)estado);
}

// Lee linea por linea y la interpreta.
void procesarSerial() {
  static char buffer[32];
  static uint8_t idx = 0;

  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (idx > 0) {
        buffer[idx] = '\0';
        interpretarComando(buffer);
        idx = 0;
      }
    } else if (idx < sizeof(buffer) - 1) {
      buffer[idx++] = c;
    }
  }
}

void interpretarComando(char* cmd) {
  // CD:<min>,<max>  -> banda de distancia
  if (strncmp(cmd, "CD:", 3) == 0) {
    char* tok = strtok(cmd + 3, ",");
    if (tok) {
      distMin = atoi(tok);
      tok = strtok(NULL, ",");
      if (tok) distMax = atoi(tok);
    }
  }
  // CL:<min>,<max>  -> banda de luz
  else if (strncmp(cmd, "CL:", 3) == 0) {
    char* tok = strtok(cmd + 3, ",");
    if (tok) {
      luzMin = atoi(tok);
      tok = strtok(NULL, ",");
      if (tok) luzMax = atoi(tok);
    }
  }
  // CP:<conc>,<desc>  -> pomodoro: en descanso (desc=1) avisa la pausa activa
  else if (strncmp(cmd, "CP:", 3) == 0) {
    char* tok = strtok(cmd + 3, ",");   // en_concentracion (no se usa por ahora)
    if (tok) {
      tok = strtok(NULL, ",");          // en_descanso
      if (tok) alertaForzada = (atoi(tok) == 1);
    }
  }
}