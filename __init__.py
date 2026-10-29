# =============================================================================
# Dev Levels — baterías de estado para el GitHub Universe badge
#
# 4 pantallas que se recorren con LEFT / RIGHT (con wrap-around):
#   1) SOCIAL BATTERY  — energía social (referencia: app social_battery)
#   2) COFFEE LEVEL    — nivel de cafeína
#   3) REST LEVEL      — nivel de descanso
#   4) OVERVIEW        — las 3 baterías verticales con su % (chat / taza / luna)
#
# En las pantallas 1-3:
#   UP / DOWN      ajustan el nivel en pasos de 10
#   SELECT         cicla la cadencia 0 -> 1 -> ... -> 10 -> 0
#
# La cadencia son las horas en que la batería llega a 0 (drena -10% cada
# cadence*6 min); 0 = sin cadencia. Ajustar el nivel o la cadencia reinicia
# el contador de tiempo de esa batería. Todo persiste con State.save().
# =============================================================================

import os
import sys
import time

# El launcher ejecuta cada app dentro de su propio directorio en /system/apps.
# En el simulador ese directorio puede no existir, por eso el try/except.
APP_DIR = "/system/apps/devlvls"
try:
    os.chdir(APP_DIR)
    sys.path.insert(0, APP_DIR)
except OSError:
    pass

from badgeware import State

# HIRES = pantalla completa de 320x240 (el default es LORES de 160x120 y
# nuestros dibujos no cabrían); VSYNC evita redraws a medias / parpadeo.
badge.mode(HIRES | VSYNC)

# -----------------------------------------------------------------------------
# Paleta
# -----------------------------------------------------------------------------
BACKGROUND = color.rgb(13, 17, 23)   # fondo casi negro (estilo GitHub dark)
FRAME = color.rgb(216, 228, 239)     # borde metálico de las baterías
EMPTY = color.rgb(37, 49, 64)        # celdas vacías
WHITE = color.rgb(250, 252, 255)     # texto principal
MUTED = color.rgb(166, 183, 199)     # texto secundario

# Paleta única para las 3 baterías: un color por banda de mood
# (0-19, 20-39, 40-69, 70-100)
LEVEL_COLORS = (
    color.rgb(255, 115, 129),   # rojo      — nivel bajo
    color.rgb(255, 184, 104),   # naranja
    color.rgb(250, 213, 106),   # amarillo
    color.rgb(110, 160, 215),   # azul      — nivel alto
)

# -----------------------------------------------------------------------------
# Estado persistente
# -----------------------------------------------------------------------------
# Se guarda en el almacén de State bajo la clave "devlvls":
#   social/coffee/rest : nivel actual (0-100, múltiplos de 10)
#   cadence            : horas en que cada batería llega a 0 (0 = sin cadencia)
#   decay_level        : nivel base cuando se reinició el contador de cadencia
#   decay_epoch        : time.time() de ese reinicio (base para el drenaje)
state = {
    "social": 60, "coffee": 60, "rest": 60,
    "cadence": {}, "decay_level": {}, "decay_epoch": {},
}
State.load("devlvls", state)

# Claves de nivel en el orden de las pantallas 1-3; para indexar con screen_index
STATE_KEYS = ("social", "coffee", "rest")

# Validación de lo guardado: niveles válidos, cadencia 0-10 y un contador de
# cadencia coherente (si algo viene corrupto o falta, se resetea).
now = time.time()
for key in STATE_KEYS:
    value = state.get(key)
    if type(value) is not int or value < 0 or value > 100 or value % 10:
        if value is not None:
            print("Dev Levels: invalid saved %s level; resetting to 60" % key)
        state[key] = 60

    cadence = state["cadence"].get(key, 0)
    if type(cadence) is not int or cadence < 0 or cadence > 10:
        cadence = 0
    state["cadence"][key] = cadence

    base = state["decay_level"].get(key)
    if type(base) is not int or base < 0 or base > 100 or base % 10:
        base = state[key]
    state["decay_level"][key] = base

    epoch = state["decay_epoch"].get(key)
    if type(epoch) is not int and type(epoch) is not float:
        epoch = now
    state["decay_epoch"][key] = epoch

# Índice de la pantalla visible: 0=social, 1=coffee, 2=rest, 3=overview.
# Solo vive en RAM: al abrir la app siempre empieza en la pantalla 1.
screen_index = 0


# -----------------------------------------------------------------------------
# Moods: traducen el nivel numérico a (encabezado, mensaje, color)
# -----------------------------------------------------------------------------
def social_mood(level):
    if level == 0:
        return "RECHARGING", "Not up for chatting now", LEVEL_COLORS[0]
    if level < 20:
        return "NEED A BREAK", "I may step away soon", LEVEL_COLORS[0]
    if level < 40:
        return "RUNNING LOW", "Please keep it brief", LEVEL_COLORS[1]
    if level < 70:
        return "GOING STEADY", "I may take a pause", LEVEL_COLORS[2]
    return "READY TO CONNECT", "Chats feel good today", LEVEL_COLORS[3]


def coffee_mood(level):
    if level == 0:
        return "ALL OUT", "No coffee left in the tank", LEVEL_COLORS[0]
    if level < 20:
        return "DESPERATE", "First coffee urgently needed", LEVEL_COLORS[0]
    if level < 40:
        return "WARMING UP", "One cup in, barely functional", LEVEL_COLORS[1]
    if level < 70:
        return "STEADY SIP", "Caffeine levels holding", LEVEL_COLORS[2]
    return "FULLY CAFFEINATED", "Espresso for everyone", LEVEL_COLORS[3]


def rest_mood(level):
    if level == 0:
        return "OUT OF ORDER", "Do not disturb, recharging", LEVEL_COLORS[0]
    if level < 20:
        return "EXHAUSTED", "Naps are non-negotiable", LEVEL_COLORS[0]
    if level < 40:
        return "LOW BATTERY", "Early night planned", LEVEL_COLORS[1]
    if level < 70:
        return "RECOVERING", "Getting there slowly", LEVEL_COLORS[2]
    return "WELL RESTED", "Ready for anything", LEVEL_COLORS[3]


# (título de la pantalla, función de mood)
# El orden define también el orden de las pantallas 1-3.
METRICS = (
    ("SOCIAL BATTERY", social_mood),
    ("COFFEE LEVEL", coffee_mood),
    ("REST LEVEL", rest_mood),
)

# 3 baterías + 1 overview
SCREEN_COUNT = 4


# -----------------------------------------------------------------------------
# Helpers de dibujo
# -----------------------------------------------------------------------------
def center_text(text, y, size=1):
    """Texto centrado horizontalmente en toda la pantalla (320px)."""
    width, _ = screen.measure_text(text, font_size=size)
    screen.text(text, (screen.width - width) // 2, y, size)


def low_blink_on():
    """Fase encendida del parpadeo de batería baja (alterna cada 0.5 s)."""
    # badge.ticks (ms desde boot) en vez de time.time(): en el hardware el
    # reloj de pared puede estar congelado sin NTP y el blink no alternaría
    return (badge.ticks // 500) % 2 == 0


# -----------------------------------------------------------------------------
# Pantallas 1-3: batería horizontal grande
# -----------------------------------------------------------------------------
# Layout (escala x2 del original de social_battery, que era para LORES
# 160x120; aquí vamos en HIRES 320x240):
#
#   y=10                TÍTULO (ziplock, 2x)
#   y=60..150           batería 256x90 + tapa, centrada (x=32)
#   dentro              10 celdas de 20x66 (se llenan según level//10)
#   sobre la batería    etiqueta "NN%" sobre un parche del color de fondo
#   y=155 / y=188       encabezado del mood 2x (color) y mensaje (blanco)
#   y=214               estado de la cadencia (MUTED)
def draw_battery_screen(index):
    title, mood = METRICS[index]
    level = state[STATE_KEYS[index]]
    heading, message, energy = mood(level)

    # Fondo
    screen.pen = BACKGROUND
    screen.rectangle(screen.clip)

    # Título de la pantalla (2x)
    screen.font = font.ziplock
    screen.pen = WHITE
    center_text(title, 10, 2)

    # Cuerpo de la batería: marco exterior + tapa a la derecha + interior oscuro
    x = (screen.width - 272) // 2   # 32: deja 16px de margen por lado
    y = 60
    screen.pen = FRAME
    screen.rectangle(x, y, 256, 90)             # marco
    screen.rectangle(x + 256, y + 26, 16, 38)   # terminal positivo
    screen.pen = BACKGROUND
    screen.rectangle(x + 6, y + 6, 244, 78)     # interior (borde de 6px)

    # 10 celdas de izquierda a derecha; se llenan según level // 10.
    # Con 10% o menos, la celda encendida parpadea rojo/apagado.
    fill = energy
    if level <= 10 and not low_blink_on():
        fill = EMPTY
    for cell in range(10):
        screen.pen = fill if cell < level // 10 else EMPTY
        screen.rectangle(x + 12 + cell * 24, y + 12, 20, 66)

    # Porcentaje: parche del color de fondo para "tapar" las celdas de atrás
    # (fuente 2x para que el número resalte dentro de la batería)
    label = "%d%%" % level
    label_width, label_height = screen.measure_text(label, font_size=2)
    label_x = (screen.width - label_width) // 2
    screen.pen = BACKGROUND
    screen.rectangle(label_x - 6, y + 22, label_width + 12, label_height + 10)
    screen.pen = WHITE
    screen.text(label, label_x, y + 28, 2)

    # Encabezado del mood (color de la banda, 2x) y mensaje descriptivo (blanco)
    screen.font = font.nope
    screen.pen = energy
    center_text(heading, y + 95, 2)
    screen.pen = WHITE
    center_text(message, y + 128)

    # Estado de la cadencia (SELECT la cicla en esta pantalla)
    cadence = state["cadence"][STATE_KEYS[index]]
    if cadence:
        hours = level // 10 * cadence / 10   # horas restantes para llegar a 0
        if hours < 1:
            status = "CADENCE %d/10 - EMPTY IN <1H" % cadence
        else:
            status = "CADENCE %d/10 - EMPTY IN %dH" % (cadence, hours)
    else:
        status = "CADENCE OFF"
    screen.pen = MUTED
    center_text(status, 214)


# -----------------------------------------------------------------------------
# Iconos del overview (dibujados con primitivas, centrados en cx; y = borde
# superior del ícono). Reemplazan a las letras S / C / R.
# -----------------------------------------------------------------------------
def draw_chat_icon(cx, y):
    """Dos burbujas de chat: trasera arriba-izquierda, delantera abajo-derecha."""
    # Burbuja trasera rellena, con cola hacia abajo a la izquierda
    screen.pen = WHITE
    screen.rectangle(cx - 20, y, 26, 16)
    screen.shape(shape.custom([vec2(cx - 16, y + 15),
                               vec2(cx - 16, y + 22),
                               vec2(cx - 9, y + 15)]))
    # Burbuja delantera: primero un parche de fondo (separa visualmente las
    # burbujas) y encima la burbuja blanca con su cola hacia abajo a la derecha
    screen.pen = BACKGROUND
    screen.rectangle(cx - 4, y + 4, 28, 18)
    screen.pen = WHITE
    screen.rectangle(cx - 2, y + 6, 24, 14)
    screen.shape(shape.custom([vec2(cx + 14, y + 19),
                               vec2(cx + 14, y + 26),
                               vec2(cx + 21, y + 19)]))


def draw_coffee_icon(cx, y):
    """Taza de café: cuerpo relleno, asa anillada y platito."""
    screen.pen = WHITE
    screen.rectangle(cx - 13, y, 24, 18)        # cuerpo
    screen.circle(vec2(cx + 14, y + 8), 7)      # asa (disco)
    screen.pen = BACKGROUND
    screen.circle(vec2(cx + 14, y + 8), 4)      # agujero del asa
    screen.pen = WHITE
    screen.rectangle(cx - 17, y + 20, 32, 3)    # platito


def draw_moon_icon(cx, y):
    """Luna creciente: disco blanco recortado por otro del color del fondo."""
    screen.pen = WHITE
    screen.circle(vec2(cx, y + 11), 11)
    screen.pen = BACKGROUND
    screen.circle(vec2(cx + 5, y + 8), 9)       # recorte = creciente


# Un dibujante de ícono por métrica, en el mismo orden que METRICS
ICON_DRAWERS = (draw_chat_icon, draw_coffee_icon, draw_moon_icon)


# -----------------------------------------------------------------------------
# Pantalla 4: overview con las 3 baterías verticales
# -----------------------------------------------------------------------------
# Layout:
#   y=22..176           3 baterías verticales de 66x146, centros en x=60/160/260
#   dentro              10 celdas de 54x12 apiladas de abajo hacia arriba
#   y=188..222          icono de la métrica (chat / taza / luna)
#   centro batería      porcentaje en 1.5x sobre parche de fondo, dentro del marco
def draw_overview():
    screen.pen = BACKGROUND
    screen.rectangle(screen.clip)

    for i in range(3):
        _, mood = METRICS[i]
        level = state[STATE_KEYS[i]]
        _, _, energy = mood(level)  # color según el mood actual de la métrica

        cx = 60 + i * 100   # centro de la columna i
        bx = cx - 33        # borde izquierdo de la batería (66px de ancho)
        screen.pen = FRAME
        screen.rectangle(bx, 30, 66, 146)           # marco
        screen.rectangle(bx + 21, 22, 24, 8)        # terminal superior
        screen.pen = BACKGROUND
        screen.rectangle(bx + 3, 33, 60, 140)       # interior (borde de 3px)

        # 10 celdas apiladas: cell 0 es la de abajo (161 = fondo del interior);
        # la batería se llena de abajo hacia arriba igual que la horizontal.
        # Con 10% o menos, la celda encendida parpadea rojo/apagado.
        fill = energy
        if level <= 10 and not low_blink_on():
            fill = EMPTY
        for cell in range(10):
            screen.pen = fill if cell < level // 10 else EMPTY
            screen.rectangle(bx + 6, 161 - cell * 14, 54, 12)

        # Icono identificador bajo cada batería (chat / taza / luna)
        ICON_DRAWERS[i](cx, 188)

        # Porcentaje centrado dentro de la batería, sobre un parche del color
        # de fondo (fuente 1.5x)
        label = "%d%%" % level
        label_width, label_height = screen.measure_text(label, font_size=1.5)
        label_x = cx - label_width // 2
        label_y = 103 - label_height // 2   # 103 = centro vertical de la batería
        screen.pen = BACKGROUND
        screen.rectangle(label_x - 5, label_y - 4, label_width + 10, label_height + 8)
        screen.pen = WHITE
        screen.text(label, label_x, label_y, 1.5)


# -----------------------------------------------------------------------------
# Cadencia: drenaje automático de las baterías
# -----------------------------------------------------------------------------
# La cadencia (0-10) son las HORAS que tarda la batería en llegar a 0:
# 10 pasos de -10% en cadence*3600 s = un paso cada cadence*360 segundos.
# 0 desactiva el drenaje. Ajustar nivel o cadencia reinicia el contador.
#
# El drenaje se calcula por timestamp (no por ticks), así que aplica aunque
# la app esté cerrada. Si el RTC se pierde (power cycle) y el tiempo guardado
# queda en el futuro, elapsed negativo no drena nada.
def reset_decay(key):
    """Toma el nivel actual como base y arranca de cero su contador de cadencia."""
    state["decay_level"][key] = state[key]
    state["decay_epoch"][key] = time.time()


def decayed_level(key):
    """Nivel de la batería tras aplicar el drenaje vencido de su cadencia."""
    cadence = state["cadence"][key]
    if cadence <= 0:
        return state[key]
    elapsed = time.time() - state["decay_epoch"][key]
    if elapsed <= 0:
        return state[key]
    steps = int(elapsed / (cadence * 360))   # pasos de -10% ya vencidos
    return max(0, state["decay_level"][key] - steps * 10)


# -----------------------------------------------------------------------------
# Bucle principal
# -----------------------------------------------------------------------------
# run() llama update() en cada frame. Las pulsaciones son edge-triggered:
# badge.pressed(BOTON) solo es verdadero el frame en que se presionó.
def update():
    global screen_index

    # LEFT / RIGHT cambian de pantalla con wrap-around (0..3)
    left = badge.pressed(BUTTON_LEFT)
    right = badge.pressed(BUTTON_RIGHT)
    if left != right:
        screen_index = (screen_index + (1 if right else -1)) % SCREEN_COUNT

    # UP / DOWN ajustan el nivel de la pantalla actual en pasos de 10.
    # En el overview (índice 3) no hay nada que ajustar.
    if screen_index < 3:
        up = badge.pressed(BUTTON_UP)
        down = badge.pressed(BUTTON_DOWN)
        if up != down:
            key = STATE_KEYS[screen_index]
            level = state[key]
            new_level = min(100, level + 10) if up else max(0, level - 10)
            if new_level != level:
                state[key] = new_level
                reset_decay(key)    # ajuste manual reinicia el contador
                State.save("devlvls", state)

    # SELECT cicla la cadencia 0 -> 1 -> ... -> 10 -> 0 de la pantalla actual.
    # Cambiar la cadencia también reinicia su contador de tiempo.
    if screen_index < 3:
        if badge.pressed(BUTTON_SELECT):
            key = STATE_KEYS[screen_index]
            state["cadence"][key] = (state["cadence"][key] + 1) % 11
            reset_decay(key)
            State.save("devlvls", state)

    # Aplicar el drenaje vencido de TODAS las baterías (no solo la visible)
    for key in STATE_KEYS:
        target = decayed_level(key)
        if target != state[key]:
            state[key] = target
            State.save("devlvls", state)  # persistir solo si cambió

    # Redibujar la pantalla activa
    if screen_index == 3:
        draw_overview()
    else:
        draw_battery_screen(screen_index)


run(update)
