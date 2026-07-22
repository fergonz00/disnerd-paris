"""Audita las fotos de la app. Portado del audit-fotos.js de Orlando.

Reporta:
  1. fichas SIN foto
  2. fotos VERTICALES (se renderizan altisimas: width 100% + height auto)
  3. fotos de BAJA RESOLUCION (se ven borrosas en pantallas modernas)
  4. archivos en fotos/ que la app no usa

    python tools/audit-fotos.py
"""
import os, re, sys
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANCHO_MOVIL = 342          # .pantalla en un celular de 390px, menos el padding
ALTO_MOLESTO = 430         # a partir de aca la foto se come media pantalla
ANCHO_MINIMO = 900         # menos que esto se ve borroso a ancho completo

# Excepciones: verificado en el navegador que NO molestan.
OK_VERTICAL = {
    'fotos/ejemplo-fila-virtual.jpg':
        'captura de la app oficial: en horizontal no se leeria',
    # Estas van en .parque-card / .destino-card, que usan object-fit:cover:
    # la foto se RECORTA a un alto fijo, no se estira. Medido: 318x424.
    'fotos/disneyland-paris.jpg': 'portada, se recorta con object-fit:cover',
    'fotos/guia-francia.jpg': 'portada, se recorta con object-fit:cover',
    'fotos/disneyland-park.jpg': 'portada, se recorta con object-fit:cover',
    'fotos/disney-adventure-world.jpg': 'portada, se recorta con object-fit:cover',
    # Va en una columna angosta (300px), no a ancho completo. Medido: 300x400.
    'fotos/brindis-paris.jpg': 'va en columna angosta, rinde 300x400',
}


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    c = open(os.path.join(RAIZ, 'index.html'), encoding='utf-8').read()

    usadas = {}
    for m in re.finditer(r'<img([^>]*)src="(fotos/[^"]+)"([^>]*)>', c):
        attrs = m.group(1) + m.group(3)
        cls = re.search(r'class="([^"]*)"', attrs)
        alt = re.search(r'alt="([^"]*)"', attrs)
        usadas.setdefault(m.group(2), []).append(
            {'cls': cls.group(1) if cls else '', 'alt': alt.group(1) if alt else ''})

    # 1. fichas sin foto
    sin_foto = []
    for f in re.findall(r'<div class="(?:atraccion|lugar-card)"[^>]*>.*?(?=<div class="(?:atraccion|lugar-card)"|\Z)',
                        c, re.DOTALL):
        nm = re.search(r'<span class="nombre">([^<]+)</span>|<h4>([^<]+)</h4>', f)
        if nm and '<img' not in f:
            sin_foto.append((nm.group(1) or nm.group(2)).strip())

    dims = {}
    carpeta = os.path.join(RAIZ, 'fotos')
    for f in sorted(os.listdir(carpeta)):
        try:
            with Image.open(os.path.join(carpeta, f)) as im:
                dims['fotos/' + f] = im.size
        except Exception:
            dims['fotos/' + f] = None

    print(f'fotos en la carpeta: {len(dims)}   usadas por la app: {len(usadas)}\n')

    print(f'=== 1. FICHAS SIN FOTO ({len(sin_foto)}) ===')
    for n in sin_foto:
        print(f'   - {n}')

    print('\n=== 2. VERTICALES (se renderizan altisimas) ===')
    vert = []
    for src, wh in dims.items():
        if not wh or src not in usadas:
            continue
        w, h = wh
        if h <= w:
            continue
        alto = round(ANCHO_MOVIL * h / w)
        vert.append((alto, src, w, h, usadas[src]))
    vert.sort(reverse=True)
    for alto, src, w, h, us in vert:
        nota = OK_VERTICAL.get(src)
        marca = 'OK ' if nota else ('!! ' if alto >= ALTO_MOLESTO else '~  ')
        print(f'  {marca}{alto:>4}px de alto en celular  {h/w:.2f}x  {w}x{h}  {src}')
        for u in us:
            print(f'         class="{u["cls"] or "(ninguna)"}"  {u["alt"][:44]}')
        if nota:
            print(f'         -> se deja: {nota}')

    print('\n=== 3. BAJA RESOLUCION (borrosas a ancho completo) ===')
    baja = [(w, h, src) for src, wh in dims.items() if wh and src in usadas
            for w, h in [wh] if w < ANCHO_MINIMO]
    for w, h, src in sorted(baja):
        print(f'  !! {w}x{h}  {src}   ({usadas[src][0]["alt"][:40]})')
    if not baja:
        print('   ninguna')

    print('\n=== 4. ARCHIVOS QUE LA APP NO USA ===')
    huer = sorted(set(dims) - set(usadas))
    for s in huer:
        print(f'   - {s}')
    if not huer:
        print('   ninguno')


if __name__ == '__main__':
    main()
