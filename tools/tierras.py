"""Genera los poligonos SVG de cada tierra, a partir de datos (no a ojo).

Metodo: Voronoi multi-semilla dentro del contorno real del parque. Las semillas
de cada tierra son su centro OSM + todas sus atracciones. Cada celda del parque
se asigna a la tierra de la semilla mas cercana.

Eso garantiza por construccion las 3 reglas de Fer:
  1. se dibuja como lo ve el viajero desde la entrada (lo resuelve proyectar.py)
  2. las tierras son CONTIGUAS y cubren el parque sin huecos ni solapes
  3. cada atraccion cae DENTRO de su tierra (es su propia semilla)

    python tools/tierras.py
"""
import json, math, os, re, unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N = 260              # celdas por lado
VIEW = 1000.0

# Nombre que usa la app (section-label) -> nombre canonico de la tierra.
CANON = {
    'Main Street, U.S.A.': 'Main Street U.S.A.',
    'Frontierland': 'Frontierland',
    'Adventureland': 'Adventureland',
    'Fantasyland': 'Fantasyland',
    'Discoveryland': 'Discoveryland',
    'World of Frozen': 'World of Frozen',
    'Avengers Campus': 'Marvel Avengers Campus',
    'World of Pixar': 'Worlds of Pixar',
    'Adventure Way': 'Adventure Way',
    'Production Courtyard': 'Production Courtyard',
}
# Etiqueta corta para dibujar dentro de la tierra.
ETIQUETA = {
    'Main Street U.S.A.': 'Main Street', 'Marvel Avengers Campus': 'Avengers Campus',
    'Worlds of Pixar': 'World of Pixar',
}
# Color de cada tierra (paleta de la app: pasteles).
TINTE = {
    'Main Street U.S.A.': '#e8c9a0', 'Frontierland': '#d9a682',
    'Adventureland': '#9fc4a0', 'Fantasyland': '#e2b4cd', 'Discoveryland': '#a8b8dd',
    'World of Frozen': '#a9cfe4', 'Marvel Avengers Campus': '#d99a9a',
    'Worlds of Pixar': '#f0c98a', 'Adventure Way': '#c2b6dc',
    'Production Courtyard': '#c9bfae',
}


def limpiar(s):
    """Saca emojis y espacios del section-label."""
    s = re.sub(r'[^\w\s,.\'À-ɏ-]', '', s, flags=re.UNICODE)
    return re.sub(r'\s+', ' ', s).strip()


def tierras_de_la_app():
    """{pid: {atraccion: tierra_canonica}} leyendo el index.html."""
    c = open(os.path.join(RAIZ, 'index.html'), encoding='utf-8').read()
    out = {}
    for pid, anchor in [('dlp', 'pantalla-dlp'), ('daw', 'pantalla-studios')]:
        blk = re.search(rf'id="{anchor}".*?(?=<div class="pantalla" id=|\Z)', c, re.DOTALL).group(0)
        tab = re.search(r'<div class="tab-content[^"]*" id="[^"]*atracciones"(.*?)(?=<div class="tab-content|\Z)',
                        blk, re.DOTALL).group(1)
        d, tierra = {}, None
        for chunk in re.split(r'(<div class="section-label">[^<]+</div>)', tab):
            m = re.match(r'<div class="section-label">([^<]+)</div>', chunk)
            if m:
                tierra = CANON.get(limpiar(m.group(1)))
                continue
            for n in re.findall(r'<span class="nombre">([^<]+)</span>', chunk):
                if tierra:
                    d[n.strip()] = tierra
        out[pid] = d
    return out


def dentro(poly, x, y):
    """Punto en poligono (ray casting)."""
    n, j, c = len(poly), len(poly) - 1, False
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            c = not c
        j = i
    return c


def contornear(mask, n):
    """Traza los bordes de una mascara booleana y devuelve sus lazos."""
    edges = {}
    for (i, j) in mask:
        for di, dj, a, b in ((0, -1, (i, j), (i + 1, j)),            # arriba
                             (1, 0, (i + 1, j), (i + 1, j + 1)),      # derecha
                             (0, 1, (i + 1, j + 1), (i, j + 1)),      # abajo
                             (-1, 0, (i, j + 1), (i, j))):            # izquierda
            if (i + di, j + dj) not in mask:
                edges.setdefault(a, []).append(b)
    lazos = []
    while edges:
        ini = next(iter(edges))
        lazo, act = [ini], ini
        while True:
            sig = edges.get(act)
            if not sig:
                break
            nxt = sig.pop()
            if not sig:
                del edges[act]
            lazo.append(nxt)
            act = nxt
            if act == ini:
                break
        if len(lazo) > 3:
            lazos.append(lazo)
    return lazos


def _dp(pts, tol):
    """Douglas-Peucker sobre una POLILINEA abierta."""
    if len(pts) < 3:
        return pts
    ax, ay = pts[0]
    bx, by = pts[-1]
    dmax, idx = 0, 0
    for i in range(1, len(pts) - 1):
        px, py = pts[i]
        num = abs((by - ay) * px - (bx - ax) * py + bx * ay - by * ax)
        den = math.hypot(by - ay, bx - ax) or 1e-9
        d = num / den
        if d > dmax:
            dmax, idx = d, i
    if dmax > tol:
        return _dp(pts[:idx + 1], tol)[:-1] + _dp(pts[idx:], tol)
    return [pts[0], pts[-1]]


def simplificar(pts, tol):
    """Douglas-Peucker sobre un LAZO CERRADO.

    Ojo: aplicar DP directo a un lazo lo colapsa a un punto — como el primero y
    el ultimo coinciden, la distancia a esa 'recta' da 0 para todos. Hay que
    partir el lazo en dos arcos por el punto mas lejano y simplificar cada uno.
    """
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts = pts[:-1]
    if len(pts) < 4:
        return pts
    x0, y0 = pts[0]
    k = max(range(len(pts)), key=lambda i: (pts[i][0] - x0) ** 2 + (pts[i][1] - y0) ** 2)
    return _dp(pts[:k + 1], tol)[:-1] + _dp(pts[k:] + [pts[0]], tol)[:-1]


def suavizar(pts, vueltas=2):
    """Chaikin: redondea las esquinas del trazado rectilineo."""
    for _ in range(vueltas):
        out = []
        for i in range(len(pts)):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % len(pts)]
            out.append((x0 * 0.75 + x1 * 0.25, y0 * 0.75 + y1 * 0.25))
            out.append((x0 * 0.25 + x1 * 0.75, y0 * 0.25 + y1 * 0.75))
        pts = out
    return pts


def a_path(pts):
    d = f'M{pts[0][0]:.1f},{pts[0][1]:.1f}'
    for x, y in pts[1:]:
        d += f'L{x:.1f},{y:.1f}'
    return d + 'Z'


def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    mapa = json.load(open(os.path.join(RAIZ, 'tools', 'mapa-svg.json'), encoding='utf-8'))
    asign = tierras_de_la_app()
    salida = {}

    for pid, m in mapa.items():
        print(f"\n=== {m['titulo']} ===")
        poly = [tuple(p) for p in m['contorno']]
        pins = {k: tuple(v) for k, v in m['pins'].items()}
        de = asign[pid]

        # semillas: centro de la tierra + sus atracciones
        semillas = {}
        for nom, xy in m['centros_tierra'].items():
            if nom in [t for t in de.values()]:
                semillas.setdefault(nom, []).append(tuple(xy))
        for atr, xy in pins.items():
            t = de.get(atr)
            if t:
                semillas.setdefault(t, []).append(xy)

        faltan = sorted(set(de.values()) - set(semillas))
        if faltan:
            print(f"  !! tierras sin ninguna semilla: {faltan}")
        for t, s in sorted(semillas.items()):
            print(f"  {t}: {len(s)} semillas")

        # grilla -> tierra mas cercana
        # Se acepta la celda si esta dentro del contorno OSM, o si esta MUY cerca
        # de una atraccion: algunos edificios pisan el perimetro y OSM los deja
        # afuera por precision de mapeo (Flight Force queda a 6,8 de 1000).
        paso = VIEW / N
        celdas = {}
        planas = [(t, x, y) for t, ss in semillas.items() for (x, y) in ss]
        TOL = 16.0
        for i in range(N):
            cx = (i + 0.5) * paso
            for j in range(N):
                cy = (j + 0.5) * paso
                if not dentro(poly, cx, cy) and not any(
                        (sx - cx) ** 2 + (sy - cy) ** 2 < TOL ** 2 for _, sx, sy in planas):
                    continue
                mejor, dm = None, 1e18
                for t, sx, sy in planas:
                    d = (sx - cx) ** 2 + (sy - cy) ** 2
                    if d < dm:
                        dm, mejor = d, t
                celdas[(i, j)] = mejor

        lands = []
        for t in sorted(semillas, key=lambda t: -sum(1 for v in celdas.values() if v == t)):
            mask = {c for c, v in celdas.items() if v == t}
            lazos = contornear(mask, N)
            if not lazos:
                continue
            # Se dibujan TODOS los pedazos grandes, no solo el mayor: descartar
            # los otros dejaba atracciones sin tierra. Los slivers si se tiran.
            lazos.sort(key=len, reverse=True)
            grandes = [l for l in lazos if len(l) >= max(12, len(lazos[0]) * 0.06)]
            tirados = len(lazos) - len(grandes)
            if len(grandes) > 1:
                print(f"  ~ {t}: {len(grandes)} pedazos separados"
                      + (f" (+{tirados} slivers descartados)" if tirados else ""))
            elif tirados:
                print(f"  ~ {t}: {tirados} slivers descartados")
            d = ''
            for lazo in grandes:
                pts = suavizar(simplificar([(x * paso, y * paso) for x, y in lazo], 3.0), 2)
                d += a_path(pts)
            lands.append({'name': t, 'label': ETIQUETA.get(t, t),
                          'tint': TINTE.get(t, '#cccccc'), 'd': d,
                          'partes': len(grandes)})

        # etiqueta al centroide de las celdas de la tierra (mas fiable que el centro OSM)
        for L in lands:
            cs = [c for c, v in celdas.items() if v == L['name']]
            L['lx'] = round(sum(c[0] for c in cs) / len(cs) * paso, 1)
            L['ly'] = round(sum(c[1] for c in cs) / len(cs) * paso, 1)
            L['celdas'] = len(cs)

        print(f"  tierras generadas: {len(lands)}  (cobertura {len(celdas)} celdas)")
        salida[pid] = {'titulo': m['titulo'], 'orient': m['orient'],
                       'lands': lands, 'pins': m['pins'], 'entrada': m['entrada']}

    json.dump(salida, open(os.path.join(RAIZ, 'tools', 'mapa-lands.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('\n-> tools/mapa-lands.json')


if __name__ == '__main__':
    main()
