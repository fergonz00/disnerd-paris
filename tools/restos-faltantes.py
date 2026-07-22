"""Que lugares para comer hay DENTRO de los parques que la app todavia no tiene.

Cruza los restaurantes de OSM contra el contorno real de cada parque, y descarta
los que la app ya lista. Lo que queda es lo que falta cargar.

    python tools/restos-faltantes.py
"""
import json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))
from tierras import dentro                                            # noqa: E402
from proyectar import construir, cargar_contorno                      # noqa: E402
import importlib.util                                                 # noqa: E402

spec = importlib.util.spec_from_file_location('gm', os.path.join(RAIZ, 'tools', 'generar-mapas.py'))
gm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gm)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    osm = json.load(open(os.path.join(RAIZ, 'tools', 'osm-restaurantes.json'), encoding='utf-8'))
    _, _, zonas = gm.datos_app()

    puntos = []
    for e in osm['elements']:
        t = e.get('tags', {})
        if not t.get('name'):
            continue
        c = e.get('center', e)
        if 'lat' in c:
            puntos.append({'n': t['name'], 'lat': c['lat'], 'lon': c['lon'],
                           'tipo': t.get('amenity', ''), 'k': gm.norm(t['name'])})

    for pid, arch, titulo in [('dlp', 'osm-parc-disneyland.json', 'Disneyland Park'),
                              ('daw', 'osm-adventure-world.json', 'Disney Adventure World')]:
        contorno = cargar_contorno(arch)
        # el contorno viene en (lat, lon); dentro() espera (x, y) => (lon, lat)
        poly = [(lo, la) for la, lo in contorno]
        adentro = [p for p in puntos if dentro(poly, p['lon'], p['lat'])]
        ya = {gm.norm(r) for r in zonas.get(pid, [])}
        faltan = [p for p in adentro
                  if not any(p['k'] == y or (y and (y in p['k'] or p['k'] in y)) for y in ya)]

        print(f"\n=== {titulo} ===")
        print(f"  lugares para comer DENTRO del parque segun OSM: {len(adentro)}")
        print(f"  la app ya tiene: {len(zonas.get(pid, []))}   ->  FALTAN {len(faltan)}\n")
        for p in sorted(faltan, key=lambda x: x['n']):
            print(f"    [{p['tipo']:10}] {p['n']}")


if __name__ == '__main__':
    main()
