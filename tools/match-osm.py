"""Cruza las atracciones de la app contra las coordenadas reales de OSM.

Sale el reporte de cobertura: cuales matchean, cuales no. Las que no matchean
hay que ubicarlas a mano (o corregir el nombre). NO inventar coordenadas.

    python tools/match-osm.py
"""
import json, re, sys, unicodedata, os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# La app usa el nombre en ingles y OSM el frances (o al reves). Son la MISMA
# atraccion, solo cambia el idioma del cartel. Verificado uno por uno.
ALIAS = {
    'Indiana Jones et le Temple du Péril': 'Indiana Jones™ and the Temple of Peril',
    'Star Tours: The Adventures Continue': "Star Tours : L'Aventure Continue",
    'Mickey et son Orchestre PhilharMagique': "Mickey's PhilharMagic",
    'Ratatouille: The Adventure': "Ratatouille : L'Aventure totalement toquée de Rémy",
}


def norm(s):
    """Normaliza un nombre para comparar: sin tildes, sin marcas, sin articulos."""
    s = unicodedata.normalize('NFD', s)
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
    s = s.lower().replace('®', ' ').replace('™', ' ').replace('&', ' and ')
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    s = re.sub(r'\b(the|le|la|les|el|los|un|une|of|de|des|du|and|a|con|presente|presentee?)\b', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def atracciones_app():
    """Lee las fichas del index.html agrupadas por parque y tierra."""
    c = open(os.path.join(RAIZ, 'index.html'), encoding='utf-8').read()
    out = []
    for pid, anchor in [('dlp', 'pantalla-dlp'), ('daw', 'pantalla-studios')]:
        m = re.search(rf'id="{anchor}".*?(?=<div class="pantalla" id=|\Z)', c, re.DOTALL)
        blk = m.group(0)
        tab = re.search(r'<div class="tab-content[^"]*" id="[^"]*atracciones"(.*?)(?=<div class="tab-content|\Z)',
                        blk, re.DOTALL).group(1)
        tierra = None
        for chunk in re.split(r'(<div class="section-label">[^<]+</div>)', tab):
            lm = re.match(r'<div class="section-label">([^<]+)</div>', chunk)
            if lm:
                tierra = lm.group(1).strip()
                continue
            for n in re.findall(r'<span class="nombre">([^<]+)</span>', chunk):
                out.append({'pid': pid, 'tierra': tierra, 'nombre': n.strip()})
    return out


def osm_puntos():
    d = json.load(open(os.path.join(RAIZ, 'tools', 'osm-atracciones.json'), encoding='utf-8'))
    pts = []
    for e in d['elements']:
        t = e.get('tags', {})
        if not t.get('name') or t.get('tourism') == 'theme_park':
            continue
        c = e.get('center', e)
        if 'lat' not in c:
            continue
        pts.append({'nombre': t['name'], 'lat': c['lat'], 'lon': c['lon'], 'k': norm(t['name'])})
    return pts


def match(nombre, pts):
    k = norm(ALIAS.get(nombre, nombre))
    if not k:
        return None
    exactos = [p for p in pts if p['k'] == k]
    if exactos:
        return exactos[0], 'exacto'
    parciales = [p for p in pts if p['k'].startswith(k) or k.startswith(p['k'])
                 or (len(k) > 8 and k in p['k']) or (len(p['k']) > 8 and p['k'] in k)]
    if parciales:
        return min(parciales, key=lambda p: abs(len(p['k']) - len(k))), 'parcial'
    return None


def main():
    app, pts = atracciones_app(), osm_puntos()
    print(f'fichas en la app: {len(app)}   puntos OSM: {len(pts)}\n')
    hits, misses = [], []
    for a in app:
        r = match(a['nombre'], pts)
        if r:
            p, tipo = r
            hits.append({**a, 'lat': p['lat'], 'lon': p['lon'], 'osm': p['nombre'], 'tipo': tipo})
        else:
            misses.append(a)

    for pid in ('dlp', 'daw'):
        print(f'=== {pid.upper()} ===')
        for h in [x for x in hits if x['pid'] == pid]:
            marca = '  ' if h['tipo'] == 'exacto' else '~ '
            extra = '' if h['osm'] == h['nombre'] else f"   (OSM: {h['osm']})"
            print(f"{marca}{h['lat']:.5f},{h['lon']:.5f}  {h['nombre']}{extra}")
        print()

    print(f'>>> matchearon: {len(hits)}/{len(app)}')
    if misses:
        print(f'>>> SIN COORDENADA ({len(misses)}) - ubicar a mano, no inventar:')
        for m in misses:
            print(f"    [{m['pid']}] {m['tierra']}  ->  {m['nombre']}")

    json.dump(hits, open(os.path.join(RAIZ, 'tools', 'coords.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('\ncoordenadas guardadas en tools/coords.json')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
