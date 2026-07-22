"""Audita el mapa generado. Portado del audit-mapa.js de Orlando.

Chequea:
  1. cobertura en los DOS sentidos (ficha sin pin / pin sin ficha)
  2. punto-en-poligono: cada atraccion cae DENTRO de su tierra
  3. solapamientos entre tierras
  4. tierras vacias

Leccion de Orlando: si un total no cierra con la intuicion, sospechar del
parser ANTES que de los datos. Por eso el conteo de fichas se imprime siempre.

    python tools/audit-mapa.py
"""
import json, os, sys
from tierras import tierras_de_la_app, dentro

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def subpaths(d):
    """Path con uno o varios 'Mx,yL...Z' -> lista de poligonos."""
    out = []
    for trozo in d.split('M')[1:]:
        cuerpo = trozo.rstrip('Z').replace('L', ' ').split()
        pts = [tuple(float(v) for v in p.split(',')) for p in cuerpo]
        if len(pts) > 2:
            out.append(pts)
    return out


def dentro_multi(d, x, y):
    """Esta el punto dentro de alguno de los pedazos de la tierra?"""
    return any(dentro(p, x, y) for p in subpaths(d))


def puntos_del_path(d):
    """Todos los puntos del path, para calcular el centroide."""
    return [p for sp in subpaths(d) for p in sp]


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    mapa = json.load(open(os.path.join(RAIZ, 'tools', 'mapa-lands.json'), encoding='utf-8'))
    asign = tierras_de_la_app()
    problemas = 0

    for pid, m in mapa.items():
        de = asign[pid]
        pins = m['pins']
        print(f"\n=== {m['titulo']} ===")
        print(f"  fichas en la app: {len(de)}   pins con coordenada: {len(pins)}")

        # 1. cobertura en los dos sentidos
        sin_pin = sorted(set(de) - set(pins))
        sin_ficha = sorted(set(pins) - set(de))
        if sin_pin:
            print(f"  fichas SIN pin ({len(sin_pin)}) - no se dibujan en el mapa:")
            for n in sin_pin:
                print(f"     - {n}   [{de[n]}]")
        if sin_ficha:
            problemas += len(sin_ficha)
            print(f"  *** pins SIN ficha ({len(sin_ficha)}): {sin_ficha}")

        # 2. cada atraccion dentro de su tierra
        polys = {L['name']: L['d'] for L in m['lands']}
        fuera = []
        for atr, xy in pins.items():
            t = de.get(atr)
            if not t or t not in polys:
                continue
            if not dentro_multi(polys[t], xy[0], xy[1]):
                cae_en = [n for n, p in polys.items() if dentro_multi(p, xy[0], xy[1])]
                fuera.append((atr, t, cae_en or ['(ninguna)']))
        if fuera:
            problemas += len(fuera)
            print(f"  *** atracciones FUERA de su tierra ({len(fuera)}):")
            for a, t, c in fuera:
                print(f"     {a}: deberia estar en {t}, cae en {c}")
        else:
            print(f"  punto-en-poligono: las {len(pins)} atracciones caen en su tierra ✓")

        # 3. solapamientos (muestreo del centroide de cada tierra)
        solapes = []
        for L in m['lands']:
            p = puntos_del_path(L['d'])
            cx = sum(q[0] for q in p) / len(p)
            cy = sum(q[1] for q in p) / len(p)
            otras = [o['name'] for o in m['lands']
                     if o['name'] != L['name'] and dentro_multi(o['d'], cx, cy)]
            if otras:
                solapes.append((L['name'], otras))
        if solapes:
            problemas += len(solapes)
            print(f"  *** solapamientos: {solapes}")
        else:
            print(f"  solapamientos: ninguno ✓")

        # 4. tierras vacias / sin pins
        for L in m['lands']:
            n = sum(1 for a, t in de.items() if t == L['name'] and a in pins)
            if n == 0:
                problemas += 1
                print(f"  *** tierra sin ninguna atraccion dibujada: {L['name']}")

        print(f"  tierras: {len(m['lands'])}  ({', '.join(L['name'] for L in m['lands'])})")

    print(f"\n{'PROBLEMAS: ' + str(problemas) if problemas else 'TODO OK ✓'}")
    return 1 if problemas else 0


if __name__ == '__main__':
    sys.exit(main())
