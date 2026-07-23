"""Arma el bloque MAPAS que va dentro de index.html.

Junta: tierras (tierras.py) + intensidad por atraccion + capa de lugares para
comer. Igual que en Orlando, el mapa tiene DOS capas y la intensidad se muestra
con colores.

    python tools/generar-mapas.py   ->  tools/_mapas.js

La INTENSIDAD se deriva de datos que ya estan en la app (la tabla ALTURAS y los
badges que reviso Sofi), no se inventa:
    badge "🎭 Show"      -> blue   (show, sin adrenalina)
    altura >= 120 cm     -> red    (mucha adrenalina)
    altura 100-119 cm    -> yellow (intensidad media)
    resto                -> green  (familia)
Si alguna queda mal clasificada, corregirla en FORZAR (abajo) y volver a correr.
"""
import json, os, re, sys, unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
from tierras import tierras_de_la_app                                  # noqa: E402
from proyectar import construir                                        # noqa: E402

# Correcciones a mano de la intensidad (nombre exacto de la app -> color).
# La altura sola no siempre alcanza: Tower of Terror pide 102 cm pero es de las
# mas fuertes del parque.
FORZAR = {
    'The Twilight Zone Tower of Terror': 'red',
    "Crush's Coaster": 'red',
}

LEYENDA = {'red': 'Mucha adrenalina', 'yellow': 'Intensidad media',
           'green': 'Familia', 'blue': 'Show'}
COLOR = {'red': '#e8958a', 'yellow': '#f0c97a', 'green': '#7ec8a0', 'blue': '#6baed6'}

# Igual que Orlando: la capa de comida se filtra por CON / SIN reserva.
# rr = se reserva (servicio en mesa o buffet) · rl = se entra y listo.
# La clasificacion sale de la web oficial de Disneyland Paris, no se estima.
COLOR_COMIDA = {'rr': '#c9a227', 'rl': '#e8934a'}
RESERVA = {
    'Agrabah Café': 'rr', 'Auberge de Cendrillon': 'rr', 'Captain Jack': 'rr',
    'Silver Spur Steakhouse': 'rr', 'The Lucky Nugget Saloon': 'rr',
    "Walt's — An American Restaurant": 'rr', 'Plaza Gardens Restaurant': 'rr',
    'Royal Banquet': 'rr',
    'Bistrot Chez Rémy': 'rr', 'PYM Kitchen': 'rr', 'The Regal View Restaurant': 'rr',
}


def norm(s):
    s = unicodedata.normalize('NFD', s)
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
    s = s.lower().replace('’', "'").replace('–', '-').replace('—', '-')
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    s = re.sub(r'\b(the|le|la|les|el|los|un|une|of|de|des|du|and|a|an|restaurant|resto)\b', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def datos_app():
    """Alturas, badges y restaurantes por zona, leidos del index.html."""
    c = open(os.path.join(RAIZ, 'index.html'), encoding='utf-8').read()
    alturas = {}
    for _, blk in re.findall(r"(dlp|wds): \{\s*label:.*?attrs: \[(.*?)\],", c, re.DOTALL):
        for nm, cm in (re.findall(r"name: '([^']+)',\s*cm: (\d+)", blk)
                       + re.findall(r'name: "([^"]+)",\s*cm: (\d+)', blk)):
            alturas[nm] = int(cm)

    badges = {}
    for pid, anchor in [('dlp', 'pantalla-dlp'), ('daw', 'pantalla-studios')]:
        blk = re.search(rf'id="{anchor}".*?(?=<div class="pantalla" id=|\Z)', c, re.DOTALL).group(0)
        for card in re.findall(r'<div class="atraccion"[^>]*>.*?(?=<div class="atraccion"|\Z)', blk, re.DOTALL):
            nm = re.search(r'<span class="nombre">([^<]+)</span>', card)
            if nm:
                badges[nm.group(1).strip()] = re.findall(r'<span class="badge[^"]*">([^<]*)</span>', card)

    blk = re.search(r'id="pantalla-restaurants"(.*?)(?=<div class="pantalla" id=|\Z)', c, re.DOTALL).group(1)
    for card in re.findall(r'<div class="atraccion"[^>]*>.*?(?=<div class="atraccion"|\Z)', blk, re.DOTALL):
        nm = re.search(r'<span class="nombre">([^<]+)</span>', card)
        if nm:
            badges[nm.group(1).strip()] = re.findall(r'<span class="badge[^"]*">([^<]*)</span>', card)
    zonas = {}
    for z, cuerpo in re.findall(r'<div class="resto-zona-group" data-zona="([^"]+)"(.*?)(?=<div class="resto-zona-group"|\Z)',
                                blk, re.DOTALL):
        zonas[z] = re.findall(r'<span class="nombre">([^<]+)</span>', cuerpo)
    return alturas, badges, zonas


def intensidad(nombre, alturas, badges):
    if nombre in FORZAR:
        return FORZAR[nombre]
    if any('Show' in b for b in badges.get(nombre, [])):
        return 'blue'
    cm = alturas.get(nombre, 0)
    if cm >= 120:
        return 'red'
    if cm >= 100:
        return 'yellow'
    return 'green'


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    lands = json.load(open(os.path.join(RAIZ, 'tools', 'mapa-lands.json'), encoding='utf-8'))
    osm_r = json.load(open(os.path.join(RAIZ, 'tools', 'osm-restaurantes.json'), encoding='utf-8'))
    alturas, badges, zonas = datos_app()
    badges_rest = badges
    asign = tierras_de_la_app()

    puntos = []
    for e in osm_r['elements']:
        t = e.get('tags', {})
        if not t.get('name'):
            continue
        c = e.get('center', e)
        if 'lat' in c:
            puntos.append({'nombre': t['name'], 'lat': c['lat'], 'lon': c['lon'], 'k': norm(t['name'])})

    salida = {}
    for pid, zona in (('dlp', 'dlp'), ('daw', 'daw')):
        m = construir(pid)
        p = lands[pid]
        de = asign[pid]

        pins = {}
        for n, xy in p['pins'].items():
            bs = badges.get(n, [])
            pins[n] = {'x': xy[0], 'y': xy[1], 'land': de.get(n, ''),
                       'int': intensidad(n, alturas, badges),
                       'must': 1 if any('⭐' in b for b in bs) else 0,
                       'show': 1 if any('Show' in b for b in bs) else 0}

        # lugares para comer
        food, sin_match = {}, []
        for r in zonas.get(zona, []):
            k = norm(r)
            cand = [q for q in puntos if q['k'] == k] or \
                   [q for q in puntos if k and (k in q['k'] or q['k'] in k)]
            if not cand:
                sin_match.append(r)
                continue
            q = min(cand, key=lambda z: abs(len(z['k']) - len(k)))
            x, y = m['svg'](q['lat'], q['lon'])
            bs = badges_rest.get(r, [])
            food[r] = {'x': x, 'y': y, 'osm': q['nombre'],
                       'res': RESERVA.get(r, 'rl'),
                       'fav': 1 if any('⭐' in b for b in bs) else 0,
                       'per': 1 if any('personaje' in b.lower() or 'princesa' in b.lower() for b in bs) else 0}

        print(f"\n=== {p['titulo']} ===")
        cuenta = {}
        for v in pins.values():
            cuenta[v['int']] = cuenta.get(v['int'], 0) + 1
        print(f"  intensidad: " + ', '.join(f"{LEYENDA[k]}={v}" for k, v in sorted(cuenta.items())))
        rr = sum(1 for v in food.values() if v['res'] == 'rr')
        print(f"  lugares para comer: {len(food)}/{len(zonas.get(zona, []))}"
              f"   ({rr} con reserva, {len(food)-rr} sin reserva)")
        for r, v in food.items():
            extra = '' if v['osm'] == r else f"   (OSM: {v['osm']})"
            print(f"     {r}{extra}")
        if sin_match:
            print(f"  !! sin coordenada: {sin_match}")

        salida[pid] = {'titulo': p['titulo'], 'emoji': '🏰' if pid == 'dlp' else '🎬',
                       'orient': p['orient'],
                       'lands': [{'name': L['name'], 'label': L['label'], 'tint': L['tint'],
                                  'd': L['d'], 'lx': L['lx'], 'ly': L['ly']} for L in p['lands']],
                       'pins': pins, 'food': food, 'entrada': p['entrada']}

    js = ('const MAPA_INT = ' + json.dumps(COLOR, ensure_ascii=False, separators=(',', ':')) + ';\n'
          '  const MAPA_INT_TXT = ' + json.dumps(LEYENDA, ensure_ascii=False, separators=(',', ':')) + ';\n'
          '  const MAPA_FOOD_COLOR = ' + json.dumps(COLOR_COMIDA, ensure_ascii=False, separators=(',', ':')) + ';\n'
          '  const MAPAS = ' + json.dumps(salida, ensure_ascii=False, separators=(',', ':')) + ';')
    open(os.path.join(RAIZ, 'tools', '_mapas.js'), 'w', encoding='utf-8').write(js)
    print(f"\n-> tools/_mapas.js  ({len(js)/1024:.0f} KB)")


if __name__ == '__main__':
    main()
