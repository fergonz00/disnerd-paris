# App Disney Paris — contexto del proyecto

Guía de viaje de Disneyland Paris + París para los clientes de **Sofi Disnerd** (@disnerd.sofi).
Single-file HTML/CSS/JS inline. Login con Supabase, admin "sofi" gestiona clientes.

## Recursos

| | |
|---|---|
| Carpeta local | `C:\proyectos\App Disney Paris\` |
| Archivo principal | `index.html` (~2500 líneas, todo inline) |
| Repo GitHub | `fergonz00/disnerd-paris` (rama `main`) |
| Deploy Netlify | `disnerd-paris.netlify.app` |
| Dominio público | **`paris.disnerd.com.ar`** (HTTPS activo) |
| DNS | Netlify DNS (nameservers `dnsX.p05.nsone.net`) |

**Supabase auth:** `wjfglsafgaltusmbnccl.supabase.co`, tabla `disnerd_paris_users` (id, usuario, clave, nombre), RLS desactivado.
**Admin:** `sofi` / `SofiDisnerd2026` — único usuario con panel para crear/borrar clientes.

**Contacto Sofi (aparece en la app):** WhatsApp `541132924274` · Instagram `@disnerd.sofi`.

## Estructura de pantallas

```
Login (supabase)
├── 🏠 Inicio (bienvenida con tono Sofi + links a destinos)
├── 🏰 Disneyland Paris (hub con 3 cards)
│   ├── Disneyland Park — tabs: Atracciones/Shows/Estrategia/Comer/Alturas
│   ├── Disney Adventure World (ex WDS, renombrado 29/03/2026) — mismas tabs
│   └── 🍽️ Restaurants (card full-width abajo) — pantalla unificada con filtros
│       (Todos / DLP / DAW / Hoteles / Disney Village)
├── 🇫🇷 Guía Francia — tabs: Transporte | ✨ Recomendaciones | Día 1-6
│       (Torre Eiffel · Louvre · Montmartre · Notre Dame · Versalles · Marais)
└── ✦ Panel Sofi (solo admin)
```

Bottom nav: Inicio · Disney · Francia · Panel (oculto si no sos Sofi).

**Las pestañas "Comer" de DLP/DAW** quedan minimalistas (desayuno + snacks + link a la pantalla unificada Restaurants). Los 20 restaurantes viven en `pantalla-restaurants` con `data-zona` y filtros JS (`filtrarRestos`).

## Convenciones técnicas críticas

- **Imgur:** `imgur.com/ID` → convertir a `i.imgur.com/ID.jpg`. URLs `imgur.com/a/ID` son álbumes, no sirven.
- **Fotos en acordeones:** `height: auto`, nunca `object-fit: cover` con height fijo (deforma verticales).
- **Cards de portada:** `object-fit: cover` + misma altura.
- **Atracciones/lugares:** solo 1 abierto a la vez por tab/día (lógica en `toggleAtraccion` / `toggleLugar`).
- **`.chevron` count** debe coincidir con **`.atraccion` count** (actualmente 39).
- **Balance HTML:** todos los tags balanceados. Verificar con Python antes de pushear.
- **Clases CSS custom:** `.cierre-calido` (WhatsApp en cada pantalla) · `.cafe-tip` (recomendaciones café cerca de lugares).

## Estado actual del contenido (al 2026-05-26)

### Parques

**Shows DLP** (4, agrupados por categoría):
- Cierre: Tales of Magic
- Desfiles: Stars on Parade · A Million Splashes of Colour (7-feb a 6-sep 2026)
- Musicales: Lion King Rhythms · Mickey et son Orchestre PhilharMagique (Discoveryland Theatre)

**Shows DAW** (14, agrupados por categoría):
- Cierre nocturno: Disney Cascade of Lights ⭐
- Teatro: Mickey and the Magician · TOGETHER: A Pixar Musical Adventure · Stitch Live! · Minnie's Dream Factory (reemplazó Disney Junior feb 2026) · Animation Academy
- Avengers Campus: Heroic Welcome · Avengers Unite! · The Amazing Spider-Man Show · Pedestal for Mjolnir Worthiness (Thor+Loki) · Dancing with Deadpool (⚠️ solo 28-mar a 15-jul 2026)
- En calles: Minnie's Marching Band · Musical Moment with Rapunzel and Flynn · A Celebration in Arendelle

**Atracciones**: todas las que lista Sofi + Pinocchio en Fantasyland + Cars Quatre Roues Rallye.

**Estrategia DLP** (actualizada según PDF 21-may): Big Thunder + Hyperspace en early access. **Pirates/Indiana/Phantom Manor están CERRADAS en early access** — encarar al horario oficial. Fantasyland al final.

**Estrategia DAW** (actualizada según PDF 21-may): **ARRANCAR POR CRUSH COASTER** (no Frozen). Disclaimer: si menores no quieren, adultos van por Single Rider o Premier Access. Después Frozen Ever After + tiempo en la land (Anna/Elsa con **fila virtual**, Olaf y **Runa** aparecen cuando quieren). Después Ratatouille → Avengers → Tower → Toy Story → Cars.

**Tipos de filas** (card rediseñada): 3 tipos visualmente diferenciados — Standby / Premier Access ONE (se compra en parque desde la app) / Single Rider. Tip al final sobre Premier Access Ultimate.

**Magic Pass** (nuevo en Check-in): tickets virtuales QR únicos por persona en la app Disneyland Paris + Apple Wallet. Disponible 7 días antes. Se escanea en molinetes. Reemplaza tarjeta física.

**Encuentros con personajes en hoteles 8-11am** (Woody en Cheyenne).

**Transporte privado:** Leo Jasso Tours WhatsApp `+33 7 43 55 22 40` (de parte de Sofi Disnerd).

### Restaurants (pantalla unificada con filtros)

Total: **20 restaurantes** con `data-zona`:
- **DLP (8)**: Plaza Gardens (👨‍👩‍👧 personajes), Auberge de Cendrillon (👸 princesas), Blue Lagoon, Walt's ⭐, Silver Spur, Captain Jack ⭐, Agrabah Café, Royal Banquet
- **DAW (4)**: Bistrot Chez Rémy ⭐, The Regal View ⭐, PYM Kitchen, Stark Factory
- **Hoteles (6)**: Manhattan ⭐, Downtown (Hotel NY) · Cape Cod (Newport Bay) · Hunter's Grill (Sequoia) · Chuck Wagon Café (Cheyenne, 👨‍👩‍👧 personajes Toy Story am) · La Cantina (Santa Fe)
- **Disney Village (2)**: Annette's Diner · The Steakhouse

Snacks/datos útiles (Mickey Beignet, no Starbucks dentro del parque) quedan en la pestaña Comer DLP.

### Francia (6 días, todos con contexto histórico/cultural + referencias cine/Disney)
| Día | Tema | Lugares |
|---|---|---|
| 1 | Torre Eiffel | Bir-Hakeim → Trocadéro → Torre → Champ de Mars → Palais de Tokyo → Arco → Champs → **Juego de luces (cierre)** |
| 2 | Louvre | Tullerías → Palais Royal → Louvre → **Pont des Arts** → Saint-Eustache → Ópera → Lafayette → Vendôme |
| 3 | Montmartre | Muro Te Amo → Sacré-Cœur → Tertre → Galette → **Rue Lepic** → Deux Moulins → Moulin Rouge |
| 4 | Notre Dame (Día Disnerdo 🏰) | Sainte-Chapelle → Notre Dame → Île Saint-Louis → Panteón → Catacumbas → Saint-Étienne (portal Amélie) → Luxemburgo → Saint-Sulpice → Saint-Germain |
| 5 | Versalles | Palacio → Jardines → Trianon → Hameau de la Reine |
| 6 | Marais | Bastilla → Vosges → Sully → Saint-Paul → Rue des Rosiers → Vieille du Temple → Archivos → Picasso → **Hôtel de Ville** |

**Referencias Disney explícitas:** El Jorobado de Notre Dame en Día 4 (gárgolas Victor/Hugo/Laverne, Corte de los Milagros en Catacumbas), La Bella y la Bestia inspirada en Galería de los Espejos de Versalles, Disney Store flagship en Champs-Élysées.

### Solapa ✨ Recomendaciones (entre Transporte y Día 1)
Cafés curados por Sofi, agrupados por vibe:
- **Estética + vibe:** Saint Pearl, Boot Café (Marais · Día 6)
- **Café posta nivel experto:** Substance, Motors (Saint-Germain · Día 4)
- **Contenido Pinterest:** Jōhō, The Coffee (varios)
- **París clásico:** Café de Flore, Les Deux Magots (Saint-Germain · Día 4)

Los cafés que encajan geográficamente aparecen con un `.cafe-tip` (ícono ☕ dorado) dentro de los lugares del día correspondiente.

## Cierre cálido
Cada pantalla principal (Inicio, DLP, DAW, Francia) termina con la card `.cierre-calido` con gradiente celeste→lavanda→rosa, mensaje de Sofi y botones WhatsApp + Instagram.

## Deploy

No hay build step — es un HTML estático. Cambios se pushean al repo y Netlify hace deploy automático en ~30 segundos.

```bash
cd "/c/proyectos/App Disney Paris"
git add index.html
git -c user.email=fergonzalezsch88@gmail.com -c user.name="Fer Gonzalez" commit -m "<msg>"
git push origin main
```

El `.gitignore` excluye `*.pdf` y `guia_sofi.txt` (quedan solo locales para consulta).

## Archivos locales (no commiteados)

- `Disneyland Paris Strategic Itinerary.pdf` — guía estratégica de Sofi (orden mañana + tips)
- `guia_sofi.txt` — texto extraído del PDF strategic itinerary
- Las otras 2 guías viven en Google Drive:
  - `GUIA DISNERD PARIS.pdf` (general: hoteles, comer, Premier Access, shows)
  - `Guía Francia.pdf` (6 días, transporte)
  - `Disneyland Paris Strategic Itinerary.pdf` (también en Drive)

Se pueden releer con MCP `mcp__claude_ai_Google_Drive__read_file_content` usando los IDs:
- Strategic VIEJO: `1vPqFRseHdr6nbEdQPGzxn4Mr6vIGVzlA`
- **Strategic NUEVO (21-may-2026, el vigente)**: `1hiRZgKZXSVAUyk_tgpRuy-jY-nopAcGU`
- General: `1rAYURSPhK912stngbVgcKirXvUasSeTz`
- Francia: `1ce_JUk_Q-NNLdjRyc-ZBFo9lGkmem3Gs`

## Pendientes / próximos pasos

1. **Alturas** — replicar la sección de Orlando: input de alturas de los hijos + por cada parque (DLP / DAW) mostrar qué atracciones pueden subir y cuáles no, según altura mínima. Estructura similar a la de Orlando, solo cambian las atracciones.
2. **Recomendaciones** — ampliar con más categorías cuando Sofi mande data (shopping, restaurantes no-Disney, tips de moda, etc).
3. Verificar nombre **"Runa"** del animatronic de Frozen (Sofi lo mencionó en su PDF — confirmar si es el nombre oficial del nuevo animatronic o si se refiere a Sven).
4. Revisar visualmente cada pantalla en el navegador después de cambios grandes.

## ⚠️ Regla importante para shows/atracciones

**Conciliar SIEMPRE la info que pasa Sofi contra fuentes oficiales (WebSearch) ANTES de modificar el código.** Sofi a veces tiene errores (nombres, parques, shows discontinuados). En la sesión del 2026-05-26 se descubrió que:
- "Disney Junior Dream Factory" → reemplazado por "Minnie's Dream Factory" en feb 2026
- "Mickey PhilharMagic" en DLP = "Mickey et son Orchestre PhilharMagique" (que estaba mal en DAW)
- "Pixar Adventure" → nombre oficial es "TOGETHER: A Pixar Musical Adventure"
- "Avengers: Power the Night" → terminó, hoy es Disney Cascade of Lights
- "Disney Marching Band" → nombre oficial es "Minnie's Marching Band"
- "Asgard Pedestal" → nombre oficial es "Pedestal for Mjolnir Worthiness"
- "Disney Junior Dream Factory" del PDF viejo: ya no existe.

## Comandos útiles

**Validar HTML balance rápido:**
```bash
python -c "
import re
with open(r'C:\proyectos\App Disney Paris\index.html', 'r', encoding='utf-8') as f:
    c = f.read()
for t in ['div','span','p','h4','ul','li','button']:
    o = len(re.findall(rf'<{t}[\s>]', c)); x = len(re.findall(rf'</{t}>', c))
    print(f'{t}: {o} vs {x}  {\"OK\" if o==x else \"DIFF\"}')
"
```

**Listar orden de días en Francia:**
```bash
python -c "
import re
c = open(r'C:\proyectos\App Disney Paris\index.html',encoding='utf-8').read()
for d in re.findall(r'id=\"(dia-[^\"]+)\".*?(?=<div class=\"dia-content|<!-- ── PANEL)', c, re.DOTALL):
    pass  # ver análisis en chat
"
```
