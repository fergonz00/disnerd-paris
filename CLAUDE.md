# App Disney Paris — contexto del proyecto

Guía de viaje de Disneyland Paris + París para los clientes de **Sofi Disnerd** (@disnerd.sofi).
Single-file HTML/CSS/JS inline. Login con Supabase, admin "sofi" gestiona clientes.

## 📌 Dónde quedamos — última sesión: 2026-07-23 (larga: mapa, fichas, shows)

Sesión larga. La app pasó de ser una guía de texto a tener **mapa interactivo, fichas al nivel de Orlando y cero dependencias externas**.

### 🚨 Lo primero: España bloquea Cloudflare (la app no abría para los viajeros de allá)

Los ISP españoles (Movistar/Vodafone/Orange/Digi) bloquean **rangos enteros de IPs de Cloudflare** por las órdenes anti-piratería de LaLiga. `cdn.jsdelivr.net` resuelve a Cloudflare, así que el bundle de Supabase no cargaba — y como `const { createClient } = supabase;` era la primera línea del único `<script>`, el `ReferenceError` **mataba TODA la app**: se veía perfecta pero el botón "Ingresar" no hacía nada.

- `supabase.min.js` (v2.110.8, UMD) commiteado al repo. `.gitattributes` con `-text` para que autocrlf no lo corrompa.
- `createClient` en try/catch + guarda en `doLogin`, para que si algo externo falla el resto del script sobreviva.
- Las **116 fotos bajadas de imgur** a `fotos/` (imgur está en Fastly, mismo riesgo). Una ya estaba muerta: la del Muro del "Te Amo" — se consiguió una nueva.
- ⚠️ **REGLA: nada de CDNs externos, ni JS ni fotos.** El único host externo que queda es `fonts.googleapis.com` (Google no está en los bloqueos y degrada solo).

### 🗺️ Mapa interactivo (lo más grande de la sesión)

Solapa **🗺️ Mapa** entre Shows y Comer, en los dos parques. **Arquitectura portada de Orlando, función por función.**

- **Los datos se generan, no se dibujan a mano.** `tools/proyectar.py` (rota el parque para que quede como lo ve el viajero desde la entrada) + `tools/tierras.py` (Voronoi multi-semilla dentro del contorno real de OSM) + `tools/generar-mapas.py` (junta todo y escribe el bloque `MAPAS`).
- Para regenerar: `python tools/proyectar.py && python tools/tierras.py && python tools/generar-mapas.py`, y después pegar `tools/_mapas.js` en el `index.html`.
- **Dos capas**: 🎢 Atracciones (color por intensidad) y 🍽️ Para comer (color por con/sin reserva). Los filtros y colores son **los de Orlando**: `Todo | ⭐ Imperdibles | 🎢 Adrenalina | 🧸 Tranquilas` y `Todo | 🍽️ Con reserva | 🥤 Sin reserva`, `MAPA_FOOD_COLOR = {rr:'#c9a227', rl:'#e8934a'}`.
- **Zoom completo**: botones + − ⤢, pinch, rueda, arrastrar. Límites 1 a 2.6 con clamp. `touchAction` dinámico.
- **Click en la tierra** para aislarla, con toggle. Bloque **sticky** para que el mapa quede fijo arriba.
- **51/51 fichas con pin**, cada una dentro de su tierra, 0 solapamientos. `python tools/audit-mapa.py` lo verifica.
- ⚠️ **Ojo con los IDs**: Orlando tiene UNA pantalla de mapa y usa ids fijos. Acá los dos parques viven a la vez en el DOM, así que van prefijados (`dlp-mapa-svg`, `wds-mapa-svg`) y se resuelven con los helpers `_mid()` / `_mall()`.

### 💡 Estrategia → ficha → mapa

Portado de Orlando. **Diferencia de implementación**: allá los ítems salen de datos (`steps[].at[]`); acá la estrategia es HTML escrito a mano, así que se recorren los `li` del DOM.

- Si el ítem entero no resuelve, **se buscan los nombres DENTRO del texto** y cada uno queda clickeable. Sin esto DAW enganchaba solo 2 (la guía agrupa "Zona Toy Story: Slinky…, Toy Soldiers… y RC Racer" en un ítem). Ahora **DLP 14 y DAW 13**.
- Se recorren solo nodos de texto con un TreeWalker, así no se rompe el `<strong>` que ya estaba.
- `_normRef` tiene los artículos **franceses** (et, du, au, aux, des) además de los EN/ES, si no "Indiana Jones and the Temple of Peril" no matchea con "…et le Temple du Péril".
- La ficha inline es **flex con miniatura de 96×72** (`object-fit: cover`), igual que Orlando — no a todo el ancho.
- ⚠️ **Nada de `loading="lazy"` en las fichas que se arman a pedido** (la inline y la del mapa): la carga diferida no se dispara y la foto queda en blanco. Pasó dos veces.

### 📝 Fichas: 51 atracciones y 36 lugares para comer

- **Las 44 descripciones existentes ampliadas** al nivel de Orlando: de mediana 157 a 412 (DLP) y 378 (DAW), ninguna por debajo de 300 caracteres. Todo verificado contra la web oficial de Disneyland Paris antes de escribir.
- **Los tips salieron de las fichas de atracciones** (decisión de Fer). Los de Restaurantes (6) y Guía Francia (45) **se quedan**.
- **24 fichas nuevas**: 7 atracciones que estaban en el listado oficial y faltaban (las dos *arcades* de Main Street son las más útiles: son el atajo techado cuando llueve o pasa el desfile; **Les Tapis Volants** era la única atracción operativa que faltaba en DAW) y 17 lugares para comer (solo servicio en mesa y rápido — **sin kioscos**, filtrado con la clasificación del propio sitio de Disney).
- ⚠️ **Al insertar cards nuevas, insertar TODAS las de una zona en UNA operación.** De a una corre las posiciones del texto y el ancla de cierre del grupo deja de servir: las cards terminan FUERA del div de su zona y los filtros las ignoran. Me costó tres intentos.

### 🎭 Shows: los 20 pasan a fichas con foto y pin (no eran cards)

Eran secciones de texto en la solapa Shows (sin foto, sin acordeón, sin pin) y 6 estaban **duplicados** como ficha en Atracciones. Ahora los 20 son fichas `.atraccion` completas.

- Se convirtieron manteniendo la **agrupación por categoría** de la solapa Shows (cierre, desfiles, Avengers Campus…), no por tierra.
- Se sacaron los 6 duplicados de Atracciones (Rhythms, PhilharMagique, A Celebration, TOGETHER, Minnie's Dream Factory, Mickey and the Magician), conservándoles la descripción larga.
- ⚠️ **`fichas()` ahora lee la solapa Atracciones Y la de Shows.** La tierra del show sale de su **pin en `MAPAS`**, no del section-label (los shows se agrupan por categoría, no por tierra).
- Los 20 con **pin azul** en el mapa. Como no viven en la solapa Atracciones, su tierra y su coordenada salen de `coords.json` (cargadas a mano). `generar-mapas.py` usa la tierra de coords cuando el pin no está en Atracciones, y marca `int='blue'` para los tipo show. `audit-mapa.py` suma los shows de coords para poder verificar punto-en-polígono.
- **Vencidos sacados:** Dancing with Deadpool (terminó 15-jul) y Minnie's Marching Band (reemplazada por la Princess Cavalcade). **Nuevos:** Disney Princess Cavalcade (arrancó 24-jul), Guardians of the Galaxy, Warriors of Wakanda. **Pedestal for Mjolnir** quedó marcado "sin confirmar" — no figura en la cartelera oficial 2026, preguntarle a Sofi.

### 🖼️ Fotos: 155, ninguna sin usar y ninguna pesada

- **0 fichas sin foto.** Carpeta en 42 MB.
- `tools/optimizar-fotos.py --aplicar` achica al lado máximo de 1600px, calidad 85, progresivo, respetando la orientación EXIF. La app dibuja a 700px, así que sobra. Había fotos de 8256px y 12,5 MB — el viajero se bajaba eso con roaming.
- `tools/audit-fotos.py` reporta fichas sin foto, verticales que quedan altísimas, baja resolución y huérfanas.

### 🍽️ Restaurantes ampliados

Las 36 fichas de restaurante pasaron de mediana 262 a **335 caracteres** (las atracciones están en ~400). Verificado contra la web oficial (tipo de servicio, cocina, rango de precio, si se reserva). La capa "Para comer" del mapa filtra por **con / sin reserva** (colores de Orlando `#c9a227`/`#e8934a`, emoji 🍽️/🥤), con la clasificación del sitio oficial.

### ✅ Datos corregidos (verificados contra fuente oficial)

- **Indiana Jones** decía "la única en todo Disney con un loop" — falso, Hyperspace Mountain tiene 3 inversiones. Lo correcto: fue la **primera** montaña rusa Disney en dar vuelta al público (1993). Además le faltaba el badge **Single Rider**.
- **Autopia**: desde **1,32 m manejan solos**; de 81 cm a 1,32 m acompañados.
- **Mickey and the Magician** decía Studio Theater → va en el **Animagique Theater** (la app lo ponía junto a TOGETHER en el mismo teatro, y no puede ser).
- **Rhythms of the Pride Lands** decía "teatro de Adventureland" → **Frontierland Theatre**.
- **Royal Banquet** pasa a ⭐ favorito: el PDF de Sofi lo lista y era el único de sus cinco sin la estrella.
- ⚠️ **Error del PDF de Sofi, no de la app**: dice "Mickey and the Magician: en Disneyland" y el show es en Adventure World. La app está bien.

### Estado al cerrar (chequeo final pasado)

Los dos parques + Francia quedaron completos. Inventario: **45 atracciones** (32 DLP + 13 DAW), **20 shows** (5 + 15, todos con foto y pin), **36 restaurantes**, **46 lugares de Francia**, **155 fotos**. Chequeo final: 0 imágenes rotas, 0 errores JS, 0 fichas sin foto, 0 duplicados, audit-mapa TODO OK, filtros de los dos parques dan exacto, circuito estrategia→ficha→mapa→volver OK.

### Pendiente (nada urgente)

1. **Pedestal for Mjolnir**: marcado "sin confirmar". Preguntarle a Sofi si sigue en cartelera 2026.
2. **Cuatro fotos chicas** que Fer no consiguió mejores: restaurant-hakuna-matata (596×335), au-chalet-de-la-marionnette (649×472), toad-hall-restaurant (689×551), super-diner (800×450). Se dejan.
3. **Dos fotos huérfanas**: `blue-lagoon.jpg` y `disney-junior.jpg`, de cambios viejos. Preguntar si se borran.
4. Los restaurantes de **hoteles y Disney Village** no están en el mapa (quedan fuera de los parques). Si se quisieran, haría falta un mapa del resort.
5. **Error del PDF de Sofi** (no de la app): "Mickey and the Magician: en Disneyland" — es en Adventure World. Avisarle para que lo corrija en su documento.

## 📌 Sesión anterior: 2026-07-22

**Sesión 2026-07-22 (viajeros de España no podían abrir la app):** era un bloqueo de ISP, no un bug de la app.
- **Causa:** `index.html` cargaba supabase-js desde `cdn.jsdelivr.net`, que resuelve a **Cloudflare** (`104.17.207.5` / `104.17.208.5`). Los ISP españoles (Movistar/Vodafone/Orange/Digi) bloquean rangos enteros de Cloudflare por las órdenes anti-piratería de LaLiga.
- **Por qué rompía TODO:** `const { createClient } = supabase;` era la primera línea del **único** bloque `<script>`. Si el bundle no cargaba → `ReferenceError` → moría el script entero (login, navegación, tabs, filtros, acordeones). Síntoma: la página se ve perfecta pero el botón "✨ Ingresar" no hace nada.
- **Fix:** `supabase.min.js` (v2.110.8, `dist/umd`, byte-idéntico al de jsDelivr) commiteado al repo y servido por Netlify. `.gitattributes` con `-text` para que autocrlf no lo toque. Además `createClient` en try/catch + guarda `!sb` en `doLogin` + try/catch en la query (avisa "no hay conexión" en vez de morir callado).
- Verificado en prod: **cero** requests a jsdelivr; el único host externo al cargar es `fonts.googleapis.com` (degrada solo a fuente fallback). Login real contra Supabase OK.
- Commit `15fc7a6`.
- ⚠️ **Regla nueva: NO agregar `<script src>` de CDNs externos.** Todo JS va local al repo. Cualquier CDN (jsDelivr, unpkg, cdnjs) está sobre Cloudflare y deja la app muerta en España.

**Segunda parte de la misma sesión — las 45 fotos de imgur bajadas al repo (commit `718bb69`):**
- `i.imgur.com` está sobre Fastly y también entra en los bloqueos. Ahora **las 116 imágenes de la app salen de `fotos/`**, cero externas.
- 44 bajadas con nombres kebab-case derivados del `alt` (misma convención que las 72 previas), cero colisiones, validadas con PIL (ninguna corrupta ni duplicada).
- ⚠️ **1 foto se perdió: `XKinJD1` = Muro del "Te Amo"** (Montmartre, Día 3). **Ya estaba muerta en imgur** (redirigía a `removed.png`, 503 bytes) — o sea que hacía rato no se veía para NADIE, no solo España. No se notaba porque el `<img>` tenía `onerror` que la escondía. Saqué la etiqueta; la card conserva todo su texto.
  - **Pendiente:** pedirle esa foto a Sofi → guardarla como `fotos/muro-del-te-amo.jpg` y volver a poner el `<img class="atraccion-foto">` en la card (index.html, `lugar-card` del Muro del "Te Amo").
- **Fotos huérfanas en `fotos/`** (quedaron de cambios de contenido previos, no molestan): `blue-lagoon.jpg` (restaurante fusionado en Captain Jack) y `disney-junior.jpg` (show reemplazado por Minnie's Dream Factory).
- `fotos/` pesa ahora **99 MB** / 116 archivos. Máximo por archivo 2,6 MB (límite GitHub: 100 MB, sin problema).
- **Único host externo que queda: `fonts.googleapis.com`.** Google NO está en los bloqueos de LaLiga, y si fallara la app degrada sola a la fuente de fallback (sigue 100% funcional). Si algún día se quiere blindar del todo, hay que bajar los woff2 y reescribir el `@font-face`.

### ⚠️ Regla de fotos (desde 2026-07-22)
**Las fotos nuevas van SIEMPRE a `fotos/` en el repo. Nunca más imgur ni ningún hosting externo.** Aparte del bloqueo de España, imgur borra imágenes por su cuenta (ya nos comió una).

## 📌 Sesión anterior: 2026-06-26

**Sesión 2026-06-26 (fix marcado por una viajera):** se fusionaron **Blue Lagoon** y **Captain Jack** en un solo restaurante. Eran el MISMO lugar (el viejo "Blue Lagoon Restaurant" de DLP fue rebautizado *Captain Jack's – Restaurant des Pirates* en 2017, dentro de Pirates of the Caribbean) y la guía tenía la descripción partida en dos cards.
- Eliminé la card "Blue Lagoon Restaurant" y volqué todo su texto dentro de **Captain Jack** (descripción unificada: dentro de la atracción, botes, cielo estrellado + taberna pirata, cocina caribeña/cajun; mantiene badge ⭐ y tip de reservar con anticipación). Saqué la frase "menos icónico que Blue Lagoon".
- Resultado: **19 restaurantes** (DLP pasó de 8 → 7), HTML balanceado 63/63 atraccion/chevron.
- Commit `de42826`, pusheado a `main`, deployado a `paris.disnerd.com.ar`.
- ⚠️ Nota: Blue Lagoon SÍ existió en París (no es solo de California) — solo está renombrado. No re-agregar como restaurante aparte.

## 📌 Sesión anterior: 2026-06-02

**Estado:** working tree limpio, `main` sincronizado con `origin/main` y deployado a `paris.disnerd.com.ar`. HTML balanceado (validado: div/span/p/li OK, 64 chevron = 64 atraccion).

**Última sesión (2026-06-02):** Sofi pasó data nueva por audio + 1 foto del Drive. 2 agregados (conciliados con fuentes oficiales):
1. **Souvenirs del World of Frozen** — card nueva en Estrategia DAW, justo después de la card "Después de Crush... World of Frozen":
   - 🫙 **Tarrito de miniaturas (~€35)** en la tienda **Fjord View**: lo llenás vos de una pared de mini figuritas de Frozen. (Verificado: es el "Make Your Own Mini Figurine Collection Jar".)
   - 💌 **Postal internacional (~€8, 3 versiones)**: en la caja le ponen sello internacional, la escribís y la dejás en el buzón internacional.
   - Son los 2 souvenirs más buscados de la zona. La bullet de "shops" ahora apunta a esta card.
2. **Brindis viral de champagne** (te quedás el vaso, ~€20, en carritos por todo el parque) — agregado en **Comer DLP** y **Comer DAW**. Copa **celeste** en DAW (World of Frozen 🩵), **dorada** en DLP. Foto `fotos/brindis-paris.jpg` (la celeste, frente a la estatua Partners de DAW) puesta en **ambas** guías; en Comer DLP con aclaración de que ahí la copa es **dorada**.
- Commits: `c0e3e9c` (souvenirs + brindis) + `2914392` (foto en DLP).
- **Pendiente menor:** si Sofi manda la foto de la copa **dorada** de DLP, reemplazarla en Comer DLP.

**Sesión anterior (2026-05-28):** Sofi pasó data de **escapada a Alsacia (Colmar + Strasbourg)** — agregada a la solapa ✨ Recomendaciones como card nueva debajo de los cafés (commits `e2ec20a` + `b11a1a9` + `990ddb9`).
- Colmar: texto **tal cual lo escribió Sofi**, solo capitalicé "La Bella y la Bestia" + "Bella". No agregué dato extra (la "Fuente de Bella" / Bartholdi se sacó a pedido de Fer — su voz manda, ver feedback memory `feedback-conciliar-sofi`).
- Strasbourg: texto de Sofi + agregados factuales aprobados (catedral gótica con **332 escalones**, **La Petite France** con casas entramadas s.XVI).
- 2 tips separados al final: uno de transporte (TGV 2h 20min a Strasbourg + 30 min a Colmar), otro de itinerario (1 día = Strasbourg / 1 noche = dormir Strasbourg + Colmar al volver).

**Estado anterior (2026-05-26):**
Working tree limpio. 64 atracciones (`.atraccion` == `.chevron`). 70 fotos en `/fotos/`.

**Lo último que hicimos (corregimos 3 errores de contenido que marcó Sofi, conciliados con fuentes oficiales):**
1. **Personajes en hoteles** → son en el **lobby de cada hotel** (mañana ~8-11h, gratis, según temática), NO en el restaurante. Generalizado en Estrategia DLP→Check-in con lista por hotel.
2. **Chuck Wagon Café** (Restaurants) → saqué el badge "Personajes a la mañana" + tip aclara que es el lobby del Cheyenne (Woody/Jessie), no el buffet.
3. **World of Frozen** (Estrategia DAW) → solo **Olaf** es animatronic. **"Rúna" NO es animatronic**, es un peluche de troll bebé que se "adopta" en la tienda Fjord View (~€75, agotado a may-2026). La saqué.
   - Commits: `0bdcb91` (contenido) + `17fa57f` (esta doc).

**Decisiones tomadas:**
- ❌ **Alturas estilo Orlando DESCARTADO** (input de altura → qué pueden subir): son pocas atracciones, no tiene sentido. La tab Alturas actual (tabla) queda como está.
- ✅ "Runa" resuelto (era confusión de Sofi).

**Próximo paso / pendiente abierto:** esperar que Sofi mande más data para ampliar la solapa ✨ Recomendaciones (shopping, restaurantes no-Disney, tips de moda). Ya tiene cafés + escapada a Alsacia. No hay nada urgente en curso.

## Recursos

| | |
|---|---|
| Carpeta local | `C:\proyectos\App Disney Paris\` |
| Archivo principal | `index.html` (~4400 líneas, todo inline) |
| Herramientas | `tools/` — generadores del mapa y audits (Python) |
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

- **NADA de hosts externos** (ni CDN de JS ni fotos): España bloquea Cloudflare y Fastly. Todo va al repo. Ver la sesión 2026-07-23.
- **Fotos nuevas:** a `fotos/`, nombre en kebab-case ASCII. Después correr `python tools/optimizar-fotos.py --aplicar`.
- **Fotos en acordeones:** `height: auto`, nunca `object-fit: cover` con height fijo (deforma verticales).
- **Cards de portada:** `object-fit: cover` + misma altura.
- **Atracciones/lugares:** solo 1 abierto a la vez por tab/día (lógica en `toggleAtraccion` / `toggleLugar`).
- **`.chevron` count** debe coincidir con **`.atraccion` count**.
- ⚠️ Al verificar con regex, usar `<div class="atraccion" onclick` **exacto**: `class=.atraccion.` con comodines cuenta también `atraccion-header` y `atraccion-body` y tapa los errores.
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

**Estrategia DAW** (actualizada según PDF 21-may): **ARRANCAR POR CRUSH COASTER** (no Frozen). Disclaimer: si menores no quieren, adultos van por Single Rider o Premier Access. Después Frozen Ever After + tiempo en la land (Anna/Elsa con **fila virtual**; **Olaf** es el animatronic que camina libre y habla — aparece cuando quiere). Después Ratatouille → Avengers → Tower → Toy Story → Cars. **OJO:** "Rúna" NO es animatronic — es un peluche interactivo de troll bebé que se "adopta" en la tienda Fjord View (~€75, agotado a may-2026). No confundir.

**Tipos de filas** (card rediseñada): 3 tipos visualmente diferenciados — Standby / Premier Access ONE (se compra en parque desde la app) / Single Rider. Tip al final sobre Premier Access Ultimate.

**Magic Pass** (nuevo en Check-in): tickets virtuales QR únicos por persona en la app Disneyland Paris + Apple Wallet. Disponible 7 días antes. Se escanea en molinetes. Reemplaza tarjeta física.

**Encuentros con personajes en el LOBBY de cada hotel** (mañana ~8-11h, gratis, según temática del hotel — NO en el restaurante): Cheyenne→Woody/Jessie · Sequoia→Mickey/Goofy/Chip&Dale guardabosques · Santa Fe→Rayo McQueen · Newport Bay→Donald/Daisy · Disneyland Hotel→princesas.

**Transporte privado:** Leo Jasso Tours WhatsApp `+33 7 43 55 22 40` (de parte de Sofi Disnerd).

### Restaurants (pantalla unificada con filtros)

Total: **20 restaurantes** con `data-zona`:
- **DLP (8)**: Plaza Gardens (👨‍👩‍👧 personajes), Auberge de Cendrillon (👸 princesas), Blue Lagoon, Walt's ⭐, Silver Spur, Captain Jack ⭐, Agrabah Café, Royal Banquet
- **DAW (4)**: Bistrot Chez Rémy ⭐, The Regal View ⭐, PYM Kitchen, Stark Factory
- **Hoteles (6)**: Manhattan ⭐, Downtown (Hotel NY) · Cape Cod (Newport Bay) · Hunter's Grill (Sequoia) · Chuck Wagon Café (Cheyenne — el resto NO tiene personajes; los encuentros son en el lobby del hotel) · La Cantina (Santa Fe)
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

**Card 1 — Cafés** (curados por Sofi, agrupados por vibe):
- **Estética + vibe:** Saint Pearl, Boot Café (Marais · Día 6)
- **Café posta nivel experto:** Substance, Motors (Saint-Germain · Día 4)
- **Contenido Pinterest:** Jōhō, The Coffee (varios)
- **París clásico:** Café de Flore, Les Deux Magots (Saint-Germain · Día 4)

Los cafés que encajan geográficamente aparecen con un `.cafe-tip` (ícono ☕ dorado) dentro de los lugares del día correspondiente.

**Card 2 — Escapada Alsacia** (agregada 28-may-2026):
- Intro de Colmar + Strasbourg, sugerencia de quedarse una noche.
- Colmar: texto de Sofi tal cual (peli Bella y Bestia, pueblo que inspiró la aldea).
- Strasbourg: texto de Sofi + agregados factuales (catedral gótica con 332 escalones, La Petite France).
- 2 tips: cómo llegar (TGV 2h 20min Paris→Strasbourg + 30 min tren regional a Colmar) e itinerario (1 día = Strasbourg / 1 noche = dormir Strasbourg + Colmar antes de volver).

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

1. **Recomendaciones** — ampliar con más categorías cuando Sofi mande data (shopping, restaurantes no-Disney, tips de moda, etc).
2. Revisar visualmente cada pantalla en el navegador después de cambios grandes.

**Descartado:** Alturas estilo Orlando (input de altura → qué pueden subir). Decisión del usuario 26-may: son pocas atracciones, no tiene sentido. La tab Alturas actual (tabla) queda como está.
**Resuelto 26-may:** "Runa" era confusión de Sofi — es peluche, no animatronic (ver arriba).

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
