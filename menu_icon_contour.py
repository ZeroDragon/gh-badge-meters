# Contorno del icono de devlvls para el home screen del badge (MonaOS).
#
# El menu del firmware actual NO soporta icon.png (su app.py no tiene
# load_picture); los iconos son contornos vectoriales en
# /system/apps/menu/icons.py (ojo: el de /system/apps/menu/src/ es solo
# la fuente de referencia, el activo es el de la raiz).
#
# Instalacion tras un reflash:
#   1. Badge en modo disco, abre /system/apps/menu/icons.py
#   2. Agrega al dict ICONS la key:  "devlvls": CONTOURS,
#      pegando el tuple de abajo (y copiando este archivo a la carpeta).
#   3. Expulsa y reinicia.
#
# Formato: contornos de tuplas planas (x1, y1, x2, y2, ...), rango +/-0.46,
# y positiva hacia arriba. Relleno nonzero: contornos anidados con
# orientacion opuesta = agujero (por eso el interior va en orden inverso).

CONTOURS = (
    (0.300, 0.300, -0.440, 0.300, -0.440, -0.300, 0.300, -0.300),
    (-0.390, 0.250, 0.250, 0.250, 0.250, -0.250, -0.390, -0.250),
    (0.440, 0.110, 0.300, 0.110, 0.300, -0.110, 0.440, -0.110),
    (-0.210, 0.180, -0.330, 0.180, -0.330, -0.180, -0.210, -0.180),
    (-0.050, 0.180, -0.170, 0.180, -0.170, -0.180, -0.050, -0.180),
    (0.110, 0.180, -0.010, 0.180, -0.010, -0.180, 0.110, -0.180),
),
