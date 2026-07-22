"""Proyecta lat/lon a coordenadas SVG para los mapas de DLP y DAW.

Regla de Fer (la misma que en Orlando): el mapa se dibuja como lo ve el viajero
parado en la ENTRADA, con el parque extendiendose hacia arriba. Se ROTA, nunca
se espeja — espejar invierte este/oeste y deja las tierras del lado equivocado.

    python tools/proyectar.py
"""
import json, math, os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEW = 1000          # viewBox cuadrado
PAD = 40             # margen interno

# Eje "entrada -> fondo del parque". Es lo que el viajero tiene enfrente parado
# en la entrada, y es lo que se alinea con el eje vertical de la pantalla.
#
# DLP: se entra por el sur (bajo el Disneyland Hotel) y se camina Main Street
#      hasta el castillo. Ese es el eje visual del parque. Ojo: NO es norte puro,
#      Main Street corre sudeste->noroeste (rumbo 320deg).
#      entrada = Disneyland Railroad Main Street Station · fondo = el castillo.
# DAW: se entra por el norte, desde la esplanada que comparte con DLP.
#      entrada = centro del borde norte del parque (calculado de la geometria
#      OSM, ver abajo) · fondo = centroide del parque.
PARQUES = {
    'dlp': {'archivo': 'osm-parc-disneyland.json', 'titulo': 'Parc Disneyland',
            'entrada': (48.87080, 2.77912), 'fondo': (48.87318, 2.77601)},
    'daw': {'archivo': 'osm-adventure-world.json', 'titulo': 'Disney Adventure World',
            'entrada': None, 'fondo': None},          # se calculan de la geometria
}


# A que parque pertenece cada tierra (los nombres vienen de OSM).
TIERRAS_DE = {
    'Main Street U.S.A.': 'dlp', 'Frontierland': 'dlp', 'Adventureland': 'dlp',
    'Fantasyland': 'dlp', 'Discoveryland': 'dlp',
    'World of Frozen': 'daw', 'Marvel Avengers Campus': 'daw',
    'Worlds of Pixar': 'daw', 'Adventure Way': 'daw',
}

# Control de calidad: donde tiene que caer cada tierra mirando el parque desde la
# entrada. '' = no se controla. Si algo no da, es que la proyeccion esta mal.
ESPERADO = {
    'Main Street U.S.A.': ('centro', 'abajo'),   # se entra por ahi
    'Fantasyland': ('', 'arriba'),               # detras del castillo
    'Frontierland': ('izq', ''),                 # oeste
    'Adventureland': ('izq', ''),                # oeste/sudoeste
    'Discoveryland': ('der', ''),                # este
}


def cargar_contorno(archivo):
    d = json.load(open(os.path.join(RAIZ, 'tools', archivo), encoding='utf-8'))
    nodos = {e['id']: (e['lat'], e['lon']) for e in d['elements'] if e['type'] == 'node'}
    way = [e for e in d['elements'] if e['type'] == 'way'][0]
    return [nodos[n] for n in way['nodes']]


def plano(lat, lon, lat0):
    """Equirectangular local: metros aproximados respecto del origen."""
    return (math.radians(lon) * math.cos(math.radians(lat0)) * 6371000,
            math.radians(lat) * 6371000)


def rumbo(desde, hasta, lat0):
    """Angulo en grados de 'desde' a 'hasta', 0 = norte, sentido horario."""
    x1, y1 = plano(*desde, lat0)
    x2, y2 = plano(*hasta, lat0)
    return (math.degrees(math.atan2(x2 - x1, y2 - y1)) + 360) % 360


def borde_norte(contorno):
    """Centro del borde norte del poligono: por ahi se entra a DAW."""
    latmax = max(p[0] for p in contorno)
    b = [p for p in contorno if p[0] > latmax - 0.0004]
    return (sum(p[0] for p in b) / len(b), sum(p[1] for p in b) / len(b))


def construir(pid):
    cfg = PARQUES[pid]
    contorno = cargar_contorno(cfg['archivo'])
    lat0 = sum(p[0] for p in contorno) / len(contorno)
    lon0 = sum(p[1] for p in contorno) / len(contorno)

    entrada = cfg['entrada'] or borde_norte(contorno)
    fondo = cfg['fondo'] or (lat0, lon0)

    # Rotacion que pone el eje entrada->fondo apuntando ARRIBA.
    # Un punto a rumbo b respecto de la entrada tiene (dx,dy)=(r sin b, r cos b);
    # rotando +b queda en (0, r), o sea derecho hacia arriba. Es una ROTACION
    # pura: preserva izquierda/derecha (no espeja), como pide la regla.
    b = rumbo(entrada, fondo, lat0)
    rot = math.radians(b)

    def proyectar(lat, lon):
        x, y = plano(lat, lon, lat0)
        ox, oy = plano(lat0, lon0, lat0)
        dx, dy = x - ox, y - oy
        rx = dx * math.cos(rot) - dy * math.sin(rot)
        ry = dx * math.sin(rot) + dy * math.cos(rot)
        return rx, ry            # ry crece hacia el "fondo" del parque

    pts = [proyectar(la, lo) for la, lo in contorno]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    esc = (VIEW - 2 * PAD) / max(max(xs) - min(xs), max(ys) - min(ys))
    cx = (min(xs) + max(xs)) / 2
    cy = (min(ys) + max(ys)) / 2

    def svg(lat, lon):
        rx, ry = proyectar(lat, lon)
        # +X a la derecha; el fondo del parque va ARRIBA => invertimos Y
        return (round(VIEW / 2 + (rx - cx) * esc, 1),
                round(VIEW / 2 - (ry - cy) * esc, 1))

    # Hacia donde queda el NORTE despues de rotar (para la brujula del mapa).
    # El norte (rumbo 0) va a parar a (-sin b, cos b); en pantalla la Y se invierte.
    nx, ny = -math.sin(rot), -math.cos(rot)
    flechas = [(0, -1, 'N ↑'), (1, -1, 'N ↗'), (1, 0, 'N →'), (1, 1, 'N ↘'),
               (0, 1, 'N ↓'), (-1, 1, 'N ↙'), (-1, 0, 'N ←'), (-1, -1, 'N ↖')]
    orient = min(flechas, key=lambda f: (f[0] / (math.hypot(*f[:2]) or 1) - nx) ** 2
                 + (f[1] / (math.hypot(*f[:2]) or 1) - ny) ** 2)[2]

    return {'pid': pid, 'titulo': cfg['titulo'], 'rumbo_entrada': round(b, 1),
            'lat0': lat0, 'lon0': lon0, 'svg': svg, 'entrada': entrada,
            'orient': orient,
            'contorno': [svg(la, lo) for la, lo in contorno]}


def path(puntos, dec=1):
    d = f'M{puntos[0][0]},{puntos[0][1]}'
    for p in puntos[1:]:
        d += f'L{p[0]},{p[1]}'
    return d + 'Z'


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    coords = json.load(open(os.path.join(RAIZ, 'tools', 'coords.json'), encoding='utf-8'))
    tierras = json.load(open(os.path.join(RAIZ, 'tools', 'osm-tierras.json'), encoding='utf-8'))
    centros = {e['tags']['name']: (e['lat'], e['lon']) for e in tierras['elements']
               if e.get('tags', {}).get('place') == 'locality'}

    salida = {}
    for pid in PARQUES:
        m = construir(pid)
        print(f"\n=== {m['titulo']} ===")
        print(f"  eje entrada->fondo: rumbo {m['rumbo_entrada']}deg  ->  brujula {m['orient']}")
        print(f"  contorno: {len(m['contorno'])} vertices")

        pins = {}
        for a in [c for c in coords if c['pid'] == pid]:
            pins[a['nombre']] = m['svg'](a['lat'], a['lon'])
        print(f"  pins ubicados: {len(pins)}")

        cs = {n: m['svg'](*ll) for n, ll in centros.items()}
        ent = m['svg'](*m['entrada'])
        print(f"  entrada en SVG: {ent}  (debe quedar ABAJO, y alto)")
        print("  tierras, de arriba (fondo) hacia abajo (entrada):")
        propias = [(n, xy) for n, xy in cs.items() if TIERRAS_DE.get(n) == pid]
        for n, (x, y) in sorted(propias, key=lambda kv: kv[1][1]):
            lado = 'izq' if x < 400 else ('der' if x > 600 else 'centro')
            print(f"     y={y:6.1f} x={x:6.1f} {lado:6}  {n}")
        for n, (x, y), esperado in [(n, xy, ESPERADO.get(n)) for n, xy in propias]:
            if not esperado:
                continue
            lado = 'izq' if x < 400 else ('der' if x > 600 else 'centro')
            vert = 'arriba' if y < 400 else ('abajo' if y > 600 else 'medio')
            ok = (esperado[0] in ('', lado)) and (esperado[1] in ('', vert))
            if not ok:
                print(f"     *** {n}: esperaba {esperado}, dio ({lado}, {vert})")

        salida[pid] = {'titulo': m['titulo'], 'rumbo': m['rumbo_entrada'],
                       'orient': m['orient'],
                       'contorno': m['contorno'], 'pins': pins,
                       'entrada': ent, 'centros_tierra': cs}

    json.dump(salida, open(os.path.join(RAIZ, 'tools', 'mapa-svg.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('\n-> tools/mapa-svg.json')
