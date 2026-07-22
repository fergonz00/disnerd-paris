"""Achica las fotos al tamano que la app realmente muestra.

La app dibuja las fotos a 700px de ancho como maximo (.pantalla mide 700px).
Con el doble para pantallas retina alcanza y sobra con 1600px. Habia fotos de
8256px y 12 MB: el viajero se bajaba 12 MB para ver una imagen de 700px, y esta
en Francia con roaming.

Que hace:
  - respeta la orientacion EXIF antes de tocar nada (si no, algunas fotos de
    celular salen rotadas)
  - achica solo si el lado mas largo pasa de 1600px; NUNCA agranda
  - reencoda a JPEG calidad 85, progresivo (se ve completa antes al cargar)
  - deja el archivo original si el resultado no mejora

Los originales quedan en el historial de git, asi que esto es reversible.

    python tools/optimizar-fotos.py           # muestra que haria, no toca nada
    python tools/optimizar-fotos.py --aplicar # lo hace
"""
import io, os, sys
from PIL import Image, ImageOps

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA = os.path.join(RAIZ, 'fotos')
LADO_MAX = 1600
CALIDAD = 85


def procesar(ruta):
    """Devuelve (bytes nuevos, w, h) o None si no conviene tocarla."""
    with Image.open(ruta) as im:
        im = ImageOps.exif_transpose(im)          # aplica la rotacion del EXIF
        if im.mode not in ('RGB', 'L'):
            im = im.convert('RGB')
        w, h = im.size
        if max(w, h) > LADO_MAX:
            k = LADO_MAX / max(w, h)
            im = im.resize((round(w * k), round(h * k)), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, 'JPEG', quality=CALIDAD, optimize=True, progressive=True)
        return buf.getvalue(), im.size[0], im.size[1]


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    aplicar = '--aplicar' in sys.argv
    archivos = sorted(f for f in os.listdir(CARPETA) if f.lower().endswith(('.jpg', '.jpeg', '.png')))

    antes_tot = despues_tot = 0
    cambiadas, saltadas = [], []
    for f in archivos:
        ruta = os.path.join(CARPETA, f)
        antes = os.path.getsize(ruta)
        try:
            with Image.open(ruta) as im:
                w0, h0 = im.size
            datos, w, h = procesar(ruta)
        except Exception as e:
            print(f'  !! {f}: {e}')
            continue
        antes_tot += antes
        # si no achica nada, se deja el original (no vale la pena reencodar)
        if len(datos) >= antes * 0.95:
            despues_tot += antes
            saltadas.append(f)
            continue
        despues_tot += len(datos)
        cambiadas.append((antes - len(datos), f, w0, h0, w, h, antes, len(datos)))
        if aplicar:
            open(ruta, 'wb').write(datos)

    cambiadas.sort(reverse=True)
    print(f"{'APLICADO' if aplicar else 'SIMULACION (no se toco nada)'}\n")
    print(f"{'ARCHIVO':44} {'ANTES':>18}  {'AHORA':>18}")
    print('-' * 88)
    for _, f, w0, h0, w, h, a, d in cambiadas[:25]:
        print(f'  {f:42} {w0}x{h0} {a/1024:7.0f}KB  ->  {w}x{h} {d/1024:6.0f}KB')
    if len(cambiadas) > 25:
        print(f'  ... y {len(cambiadas)-25} mas')
    print()
    print(f'fotos achicadas : {len(cambiadas)}')
    print(f'fotos sin tocar : {len(saltadas)}  (ya estaban bien)')
    print(f'carpeta         : {antes_tot/1024/1024:.0f} MB  ->  {despues_tot/1024/1024:.0f} MB'
          f'   ({100*(1-despues_tot/antes_tot):.0f}% menos)')
    if not aplicar:
        print('\npara aplicarlo:  python tools/optimizar-fotos.py --aplicar')


if __name__ == '__main__':
    main()
