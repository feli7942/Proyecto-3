/* ════════════════════════════════════════════════════════════════════
   app.js — Pomodoro Dashboard
   All application logic lives here. Structure:
     1. CONFIGURATION  — thresholds, UI states, routines
     2. SENSOR SIMULATION  — replace this section with BLE callbacks
     3. STATE          — runtime variables
     4. DOM HELPERS    — small utility functions
     5. DISTANCE PANEL — render & update
     6. LUMINOSITY PANEL — render & update
     7. POMODORO       — timer logic & render
     8. RUTINA         — exercise countdown & render
     9. MODALS         — open / close / save
    10. INIT           — wire up events, start loops
   ════════════════════════════════════════════════════════════════════ */


/* ╔══════════════════════════════════════════════════════════════════╗
   ║  1. CONFIGURATION                                                ║
   ║                                                                  ║
   ║  All thresholds and UI state definitions live here.              ║
   ║  Change these values without touching any other section.         ║
   ╚══════════════════════════════════════════════════════════════════╝ */

/* ── Distance sensor thresholds ────────────────────────────────────
   Ideal range: [DIST_MIN, DIST_MAX] cm
   Regular (warning) margin: ±DIST_MARGIN cm around the ideal range  */
const CFG_DIST_MIN    = 70;   // cm — default ideal minimum distance
const CFG_DIST_MAX    = 80;   // cm — default ideal maximum distance
const CFG_DIST_MARGIN = 10;   // cm — "regular" tolerance band

/* ── Luminosity sensor thresholds ──────────────────────────────────
   Ideal range: [LUX_MIN, LUX_MAX] (arbitrary lux units displayed as "K")
   Regular margin: ±LUX_MARGIN around the ideal range                */
const CFG_LUX_MIN    = 500;  // K — default ideal minimum luminosity
const CFG_LUX_MAX    = 1000;  // K — default ideal maximum luminosity
const CFG_LUX_MARGIN = 5;   // K — "regular" tolerance band

/* ── Pomodoro default intervals ─────────────────────────────────────
   Times are in MINUTES.                                               */
const CFG_POMO_WORK_MIN       = 25;  // minutes — concentration interval
const CFG_POMO_SHORT_BREAK    = 5;   // minutes — short break
const CFG_POMO_LONG_BREAK     = 30;  // minutes — long break (informational)

/* ── Distance UI states ─────────────────────────────────────────────
   Each state defines the label shown and the colors applied.
   States: "ideal" | "regular" | "muy-cerca" | "muy-lejos"            */
const DIST_STATES = {
  "ideal":     { label: "Ideal",     textColor: "#66eeb7", glow1: "#338D13", glow2: "#51E8AD", rulerColor: "#66EEB7" },
  "regular":   { label: "Regular",   textColor: "#fbbf19", glow1: "#E28711", glow2: "#EABD3F", rulerColor: "#FBBF19" },
  "muy-cerca": { label: "Muy cerca", textColor: "#d8461c", glow1: "#972B13", glow2: "#CE692C", rulerColor: "#AF3B1A" },
  "muy-lejos": { label: "Muy lejos", textColor: "#339bdd", glow1: "#339BDD", glow2: "#92FFE6", rulerColor: "#339BDD" },
};

/* ── Luminosity UI states ───────────────────────────────────────────
   States: "ideal" | "regular" | "mal" | "muy"                        */
const LUX_STATES = {
  "ideal":   { label: "Ideal",         textColor: "#66eeb7", glow1: "#338D13", glow2: "#51E8AD", lightStop1: "#318A36", lightStop1Opacity: 0.62, lightStop2: "#3FB261", hasSmallStand: false },
  "regular": { label: "Regular",       textColor: "#fbbf19", glow1: "#C0831D", glow2: "#FBBF19", lightStop1: "#EABD3F", lightStop1Opacity: 0.4,  lightStop2: "#DDAC25", hasSmallStand: false },
  "mal":     { label: "Mal iluminado", textColor: "#d8461c", glow1: "#AB431D", glow2: "#D8461C", lightStop1: "#D8461C", lightStop1Opacity: 0.3,  lightStop2: "#D8461C", hasSmallStand: true  },
  "muy":     { label: "Muy iluminado", textColor: "#339bdd", glow1: "#28707E", glow2: "#339BDD", lightStop1: "#339BDD", lightStop1Opacity: 0.3,  lightStop2: "#339BDD", hasSmallStand: false },
};

/* ── Active-pause routines ──────────────────────────────────────────
   Each routine contains an ordered list of exercises.
   duration is in SECONDS.                                             */
const ROUTINES = [
  {
    name: "Rutina 1",
    exercises: [
      { title: "Ejercicio 1: Estiramiento de cabeza",  subtitle: "Inclinación a la izquierda",             duration: 15, label: "15 seg" },
      { title: "Ejercicio 2: Rotación de hombros",    subtitle: "Hacia en frente",                         duration: 20, label: "20 seg" },
      { title: "Ejercicio 3: Flexiones de muñeca",    subtitle: "Mano izquierda",                          duration: 15, label: "15 seg" },
      { title: "Ejercicio 4: Sentadillas",             subtitle: "Mantén la espalda recta",                duration: 15, label: "15 seg" },
      { title: "Ejercicio 5: Respiración profunda",   subtitle: "Inhala por la nariz, exhala por la boca", duration: 5,  label: "5 seg"  },
    ],
  },
  {
    name: "Rutina 2",
    exercises: [
      { title: "Ejercicio 1: Rotación de ojos",       subtitle: "Círculos lentos",                        duration: 10, label: "10 seg" },
      { title: "Ejercicio 2: Mirada al infinito",     subtitle: "Enfoca un punto lejano",                  duration: 20, label: "20 seg" },
      { title: "Ejercicio 3: Masaje de sienes",       subtitle: "Movimientos circulares",                  duration: 15, label: "15 seg" },
      { title: "Ejercicio 4: Inclinación de cuello",  subtitle: "Cuello hacia la derecha",                 duration: 10, label: "10 seg" },
      { title: "Ejercicio 5: Inclinación de cuello",  subtitle: "Cuello hacia la izquierda",               duration: 10, label: "10 seg" },
    ],
  },
  {
    name: "Rutina 3",
    exercises: [
      { title: "Ejercicio 1: Rotación de muñecas",   subtitle: "Ambas manos",                             duration: 15, label: "15 seg" },
      { title: "Ejercicio 2: Apertura de pecho",     subtitle: "Manos entrelazadas atrás",                duration: 20, label: "20 seg" },
      { title: "Ejercicio 3: Estiramiento de brazo", subtitle: "Brazo izquierdo al frente",               duration: 15, label: "15 seg" },
      { title: "Ejercicio 4: Estiramiento de brazo", subtitle: "Brazo derecho al frente",                 duration: 15, label: "15 seg" },
      { title: "Ejercicio 5: Respiración diafragmática", subtitle: "Inhala profundo, exhala lento",       duration: 10, label: "10 seg" },
    ],
  },
  {
    name: "Rutina 4",
    exercises: [
      { title: "Ejercicio 1: Elevación de talones",  subtitle: "De pie, sube y baja",                     duration: 20, label: "20 seg" },
      { title: "Ejercicio 2: Rodilla al pecho",      subtitle: "Pierna izquierda",                        duration: 15, label: "15 seg" },
      { title: "Ejercicio 3: Rodilla al pecho",      subtitle: "Pierna derecha",                          duration: 15, label: "15 seg" },
      { title: "Ejercicio 4: Marcha en el lugar",    subtitle: "Levanta las rodillas alto",               duration: 20, label: "20 seg" },
      { title: "Ejercicio 5: Relajación total",      subtitle: "Sacude suavemente el cuerpo",             duration: 10, label: "10 seg" },
    ],
  },
];


/* ╔══════════════════════════════════════════════════════════════════╗
   ║  2. BACKEND RED INTEGRATION                                      ║
   ╚══════════════════════════════════════════════════════════════════╝ */

// Dirección del servidor local Flask
const BACKEND_URL = 'http://localhost:5000';

/**
 * Consulta periódicamente la telemetría del Arduino procesada por Python.
 */
function fetchHardwareTelemetria() {
  fetch(`${BACKEND_URL}/api/telemetria`)
    .then(response => {
      if (!response.ok) throw new Error("Error en respuesta de red");
      return response.json();
    })
    .then(data => {
      const rootStyle = document.body.style;
      const badge = document.getElementById('status-badge');
      const statusText = document.getElementById('status-text');

      // Control de bloqueo, iluminación de fondo y Cápsula de Figma por desconexión
      if (!data.hardware_conectado) {
        rootStyle.background = "#121212"; 
        rootStyle.pointerEvents = "none"; 
        rootStyle.opacity = "0.4";
        
        // Sincronizar Cápsula Figma a estado Desconectado (Rojo)
        if (badge) {
          badge.className = "badge-desconectado";
          statusText.textContent = "Desconectado";
        }
        return; 
      } else {
        rootStyle.background = "#1C1C1C"; // Color de fondo del Canvas oficial de Figma
        rootStyle.pointerEvents = "auto"; 
        rootStyle.opacity = "1";
        
        // Sincronizar Cápsula Figma a estado Conectado (Azul)
        if (badge) {
          badge.className = "badge-conectado";
          statusText.textContent = "Conectado";
        }
      }

      state.distCm = data.distancia;
      state.luxK   = data.luminosidad;
      
      renderDistance();
      renderLux();

      if (data.estado === 2) {
         console.warn("[ALERTA] Asistente reporta anomalía en postura o iluminación.");
      }
    })
    .catch(error => {
      console.error("[-] No se pudo conectar con el Asistente de Escritorio:", error.message);
    });
}

/* ╔══════════════════════════════════════════════════════════════════╗
   ║  3. RUNTIME STATE                                                ║
   ╚══════════════════════════════════════════════════════════════════╝ */

const state = {
  // Current sensor readings (updated by onDistanceReading / onLuxReading)
  distCm: CFG_DIST_MIN + 5,
  luxK:   (CFG_LUX_MIN + CFG_LUX_MAX) / 2,

  // User-configurable thresholds (initialised from CFG constants)
  distMin: CFG_DIST_MIN,
  distMax: CFG_DIST_MAX,
  luxMin:  CFG_LUX_MIN,
  luxMax:  CFG_LUX_MAX,

  // Pomodoro
  workMin:    CFG_POMO_WORK_MIN,
  shortBreak: CFG_POMO_SHORT_BREAK,
  longBreak:  CFG_POMO_LONG_BREAK,
  seconds:    CFG_POMO_WORK_MIN * 60,
  isBreak:    false,
  running:    false,
  pomoInterval: null,

  // Rutina
  routineIndex: 0,
  activeExIndex: null,  // null = no exercise running
  exSeconds: 0,
  exInterval: null,

  // Modal: pending routine selection (committed on save)
  pendingRoutineIndex: 0,
};


/* ╔══════════════════════════════════════════════════════════════════╗
   ║  4. DOM HELPERS                                                  ║
   ╚══════════════════════════════════════════════════════════════════╝ */

const $ = id => document.getElementById(id);

function formatTime(totalSeconds) {
  const m   = Math.floor(totalSeconds / 60);
  const sec = totalSeconds % 60;
  return String(m).padStart(2, '0') + ':' + String(sec).padStart(2, '0');
}

function scaleCanvas() {
  const canvas = $('canvas');
  const scale  = Math.min(window.innerWidth / 1918, window.innerHeight / 1078);
  canvas.style.transform = 'scale(' + scale + ')';
}


/* ╔══════════════════════════════════════════════════════════════════╗
   ║  5. DISTANCE PANEL                                               ║
   ╚══════════════════════════════════════════════════════════════════╝ */

/* Classification: maps a raw distance value to one of the four UI states */
function classifyDistance(cm, min, max, margin) {
  if (cm >= min && cm <= max)              return "ideal";
  if (cm >= min - margin && cm < min)      return "regular";
  if (cm > max  && cm <= max + margin)     return "regular";
  if (cm < min - margin)                   return "muy-cerca";
  return "muy-lejos";
}

/* Called every time a new distance reading arrives */
function onDistanceReading(cm) {
  state.distCm = cm;
  renderDistance();
}

function renderDistance() {
  const { distCm, distMin, distMax } = state;
  const key  = classifyDistance(distCm, distMin, distMax, CFG_DIST_MARGIN);
  const s    = DIST_STATES[key];

  $('dist-value').textContent  = distCm + 'cm';
  $('dist-value').style.color  = s.textColor;
  $('dist-label').textContent  = s.label;
  $('dist-label').style.color  = s.textColor;
  $('dist-ruler').style.stroke = s.rulerColor;

  // Update glow colours via CSS custom properties on the panel
  const panel = $('panel-distance');
  panel.style.setProperty('--glow1', s.glow1);
  panel.style.setProperty('--glow2', s.glow2);
}


/* ╔══════════════════════════════════════════════════════════════════╗
   ║  6. LUMINOSITY PANEL                                             ║
   ╚══════════════════════════════════════════════════════════════════╝ */

function classifyLux(lux, min, max, margin) {
  if (lux >= min && lux <= max)            return "ideal";
  if (lux >= min - margin && lux < min)    return "regular";
  if (lux > max  && lux <= max + margin)   return "regular";
  if (lux < min - margin)                  return "mal";
  return "muy";
}

function onLuxReading(lux) {
  state.luxK = lux;
  renderLux();
}

function renderLux() {
  const { luxK, luxMin, luxMax } = state;
  const key = classifyLux(luxK, luxMin, luxMax, CFG_LUX_MARGIN);
  const s   = LUX_STATES[key];

  $('lux-value').textContent = luxK + 'K';
  $('lux-value').style.color = s.textColor;
  $('lux-label').textContent  = s.label;
  $('lux-label').style.color  = s.textColor;

  // Lamp illustration gradient stops
  $('lux-stop1').setAttribute('stop-color', s.lightStop1);
  $('lux-stop1').setAttribute('stop-opacity', s.lightStop1Opacity);
  $('lux-stop2').setAttribute('stop-color', s.lightStop2);

  // "mal" state shows a smaller stand; all others show the full stand
  $('lux-lamp').style.display       = s.hasSmallStand ? 'none' : 'block';
  $('lux-lamp-small').style.display = s.hasSmallStand ? 'block' : 'none';

  const panel = $('panel-luminosity');
  panel.style.setProperty('--glow1', s.glow1);
  panel.style.setProperty('--glow2', s.glow2);
}


/* ╔══════════════════════════════════════════════════════════════════╗
   ║  7. POMODORO TIMER                                               ║
   ╚══════════════════════════════════════════════════════════════════╝ */

function startPomodoroTick() {
  stopPomodoroTick();
  state.pomoInterval = setInterval(() => {
    state.seconds--;
    if (state.seconds <= 0) {
      // Flip break/work and auto-start next cycle
      state.isBreak = !state.isBreak;
      state.seconds = (state.isBreak ? state.shortBreak : state.workMin) * 60;
      if (state.isBreak) startBreakRoutine();
      else               stopBreakRoutine();
    }
    renderPomodoro();
  }, 1000);
}

function stopPomodoroTick() {
  clearInterval(state.pomoInterval);
  state.pomoInterval = null;
}

function renderPomodoro() {
  const color = state.isBreak ? '#66eeb7' : '#fbbf19';
  const label = state.isBreak ? 'Descanso' : 'Concentracion';

  $('pomo-mode-label').textContent = label;
  $('pomo-mode-label').style.color = color;
  $('pomo-time').textContent        = formatTime(state.seconds);

  // Glow color
  const outer = state.isBreak ? '#338D13' : '#E28711';
  const inner = state.isBreak ? '#66EEB7' : '#EABD3F';
  $('pg-outer').setAttribute('fill', outer);
  $('pg-inner').setAttribute('fill', inner);

  // Play / pause icons
  $('icon-play').style.display  = state.running ? 'none'  : 'inline';
  $('icon-pause').style.display = state.running ? 'inline' : 'none';

  // Footer stats
  $('pomo-work-min').textContent  = state.workMin;
  $('pomo-break-min').textContent = state.shortBreak;

  fetch(`${BACKEND_URL}/api/configurar/pomodoro`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      en_concentracion: state.running && !state.isBreak,
      en_descanso: state.running && state.isBreak
    })
  }).catch(err => console.error("Error enviando estado Pomodoro:", err));
}


/* ╔══════════════════════════════════════════════════════════════════╗
   ║  8. RUTINA / EXERCISE COUNTDOWN                                  ║
   ╚══════════════════════════════════════════════════════════════════╝ */

function buildExerciseList() {
  const list     = $('exercise-list');
  const routine  = ROUTINES[state.routineIndex];
  list.innerHTML = '';
  $('rutina-name').textContent = routine.name;

  routine.exercises.forEach((ex, i) => {
    const row = document.createElement('div');
    row.className  = 'exercise-row exercise-row--idle';
    row.id         = 'ex-row-' + i;
    row.innerHTML  =
      '<div class="ex-info">' +
        '<p class="ex-title">'    + ex.title    + '</p>' +
        '<p class="ex-subtitle">' + ex.subtitle + '</p>' +
      '</div>' +
      '<div class="ex-label" id="ex-label-' + i + '">' + ex.label + '</div>';
    list.appendChild(row);
  });

  // Populate routine modal list
  buildRutinaModalList();
}

function updateExerciseHighlight() {
  const routine = ROUTINES[state.routineIndex];
  routine.exercises.forEach((ex, i) => {
    const row   = $('ex-row-' + i);
    const label = $('ex-label-' + i);
    if (!row) return;
    const active = state.activeExIndex === i;
    row.className = 'exercise-row ' + (active ? 'exercise-row--active' : 'exercise-row--idle');
    label.textContent = active ? state.exSeconds + 's' : ex.label;
  });
}

function startBreakRoutine() {
  stopBreakRoutine();
  const exercises = ROUTINES[state.routineIndex].exercises;
  state.activeExIndex = 0;
  state.exSeconds     = exercises[0].duration;
  updateExerciseHighlight();

  state.exInterval = setInterval(() => {
    if (!state.running) return; // paused: skip ticks
    state.exSeconds--;
    if (state.exSeconds <= 0) {
      const next = state.activeExIndex + 1;
      if (next < exercises.length) {
        state.activeExIndex = next;
        state.exSeconds     = exercises[next].duration;
      } else {
        state.activeExIndex = null;
        stopBreakRoutine();
      }
    }
    updateExerciseHighlight();
  }, 1000);
}

function stopBreakRoutine() {
  clearInterval(state.exInterval);
  state.exInterval    = null;
  state.activeExIndex = null;
  state.exSeconds     = 0;
  updateExerciseHighlight();
}


/* ╔══════════════════════════════════════════════════════════════════╗
   ║  9. MODALS                                                       ║
   ╚══════════════════════════════════════════════════════════════════╝ */

function openModal(id) { $(id).style.display = 'flex'; }
function closeModal(id) { $(id).style.display = 'none'; }

// Distance modal
function openDistModal() {
  $('dist-min-input').value    = state.distMin;
  $('dist-max-input').value    = state.distMax;
  $('dist-current-range').textContent = state.distMin + 'cm – ' + state.distMax + 'cm';
  openModal('modal-dist');
}

function saveDistModal() {
  const minVal = parseInt($('dist-min-input').value, 10);
  const maxVal = parseInt($('dist-max-input').value, 10);

  if (isNaN(minVal) || isNaN(maxVal) || minVal >= maxVal) {
    alert('Por favor, ingresa un rango de distancia válido (Mínimo menor que Máximo).');
    return;
  }

  // Sincronizar las propiedades reales de configuración del objeto state
  state.distMin = minVal; 
  state.distMax = maxVal;

  fetch(`${BACKEND_URL}/api/configurar/distancia`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ min: minVal, max: maxVal })
  })
  .then(res => res.json())
  .then(data => console.log("[+] Límites de distancia actualizados en hardware."))
  .catch(err => console.error("Error sincronizando umbrales de distancia:", err));

  // SOLUCIÓN: Cambiar a 'modal-dist' que es el ID que existe realmente en la línea 416
  closeModal('modal-dist'); 
  renderDistance();        
}

// Luminosity modal
function openLuxModal() {
  $('lux-min-input').value    = state.luxMin;
  $('lux-max-input').value    = state.luxMax;
  $('lux-current-range').textContent = state.luxMin + 'K – ' + state.luxMax + 'K';
  openModal('modal-lux');
}

function saveLuxModal() {
  const minVal = parseInt($('lux-min-input').value, 10);
  const maxVal = parseInt($('lux-max-input').value, 10); // CORREGIDO: Leer el input máximo del HTML

  if (isNaN(minVal) || isNaN(maxVal) || minVal >= maxVal) {
    alert('Por favor, ingresa un rango de luminosidad válido (Mínimo menor que Máximo).');
    return;
  }

  // CORREGIDO: Actualizar ambas propiedades en el estado global
  state.luxMin = minVal;
  state.luxMax = maxVal;

  // Enviar rango completo al Backend en Python
  fetch(`${BACKEND_URL}/api/configurar/luz`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ min: minVal, max: maxVal }) // CORREGIDO: Mandar min y max
  })
  .then(res => res.json())
  .then(data => console.log("[+] Rango de iluminación actualizado en hardware."))
  .catch(err => console.error("Error sincronizando umbral de luz:", err));

  closeModal('modal-lux'); 
  renderLux();         
}

// Pomodoro intervals modal
function openPomoModal() {
  $('pomo-work-input').value  = state.workMin;
  $('pomo-short-input').value = state.shortBreak;
  $('pomo-long-input').value  = state.longBreak;
  openModal('modal-pomo');
}
function savePomoModal() {
  const w = Math.max(1, parseInt($('pomo-work-input').value)  || state.workMin);
  const s = Math.max(1, parseInt($('pomo-short-input').value) || state.shortBreak);
  const l = Math.max(1, parseInt($('pomo-long-input').value)  || state.longBreak);
  state.workMin    = w;
  state.shortBreak = s;
  state.longBreak  = l;
  state.isBreak    = false;
  state.running    = false;
  state.seconds    = w * 60;
  stopPomodoroTick();
  stopBreakRoutine();
  closeModal('modal-pomo');
  renderPomodoro();
}

// Routine-select modal
function buildRutinaModalList() {
  const list = $('rutina-list');
  list.innerHTML = '';
  state.pendingRoutineIndex = state.routineIndex;

  ROUTINES.forEach((routine, i) => {
    const btn = document.createElement('button');
    btn.className = 'rutina-option ' +
                    (i === state.pendingRoutineIndex ? 'rutina-option--active' : 'rutina-option--idle');
    btn.id = 'ropt-' + i;
    btn.innerHTML = '<p>' + routine.name + '</p>';
    btn.addEventListener('click', () => {
      state.pendingRoutineIndex = i;
      document.querySelectorAll('.rutina-option').forEach((b, j) => {
        b.className = 'rutina-option ' + (j === i ? 'rutina-option--active' : 'rutina-option--idle');
      });
    });
    list.appendChild(btn);
  });
}
function openRutinaModal() {
  buildRutinaModalList();
  openModal('modal-rutina');
}
function saveRutinaModal() {
  state.routineIndex = state.pendingRoutineIndex;
  stopBreakRoutine();
  buildExerciseList();
  closeModal('modal-rutina');
}


/* ╔══════════════════════════════════════════════════════════════════╗
   ║  10. INIT — wire everything up on DOMContentLoaded              ║
   ╚══════════════════════════════════════════════════════════════════╝ */

document.addEventListener('DOMContentLoaded', () => {

  // Scale canvas to viewport and keep it scaled on resize
  scaleCanvas();
  window.addEventListener('resize', scaleCanvas);

  // ── Sensor panels ──────────────────────────────────────────────
  renderDistance();
  renderLux();

  // ── Pomodoro controls ───────────────────────────────────────────
  renderPomodoro();

  $('btn-play-pause').addEventListener('click', () => {
    state.running = !state.running;
    if (state.running) startPomodoroTick();
    else               stopPomodoroTick();
    renderPomodoro();
  });

  $('btn-restart-cycle').addEventListener('click', () => {
    stopPomodoroTick();
    state.running = false;
    state.seconds = (state.isBreak ? state.shortBreak : state.workMin) * 60;
    renderPomodoro();
  });

  $('btn-restart-all').addEventListener('click', () => {
    stopPomodoroTick();
    stopBreakRoutine();
    state.running = false;
    state.isBreak = false;
    state.seconds = state.workMin * 60;
    renderPomodoro();
  });

  // ── Rutina panel ────────────────────────────────────────────────
  buildExerciseList();

  // ── Modal openers ───────────────────────────────────────────────
  $('btn-open-dist-modal').addEventListener('click',   openDistModal);
  $('btn-open-lux-modal').addEventListener('click',    openLuxModal);
  $('btn-open-pomo-modal').addEventListener('click',   openPomoModal);
  $('btn-open-rutina-modal').addEventListener('click', openRutinaModal);

  // ── Modal savers ────────────────────────────────────────────────
  $('btn-save-dist').addEventListener('click',   saveDistModal);
  $('btn-save-lux').addEventListener('click',    saveLuxModal);
  $('btn-save-pomo').addEventListener('click',   savePomoModal);
  $('btn-save-rutina').addEventListener('click', saveRutinaModal);

  // ── Generic close buttons (data-close attribute) ─────────────────
  document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.getAttribute('data-close');
      if (target) closeModal(target);
    });
  });

  // ── Close modals when clicking the dark backdrop ─────────────────
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', e => {
      if (e.target === overlay) closeModal(overlay.id);
    });
  });

  // Iniciar bucle de actualización en tiempo real consumiendo la API de Python
  setInterval(fetchHardwareTelemetria, 500);
});
