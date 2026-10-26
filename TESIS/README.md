# TESIS — documento integrado

Documento único que reúne, en el orden acordado con el profesor guía:

**Preliminares** — página de derechos de autor, agradecimientos, declaración
de uso de inteligencia artificial, resumen con palabras clave, índices y lista
de siglas y nomenclatura.

1. **Motivación** — motivación, objetivos, códigos, gráficos y estructura del documento
2. **Metodología de trabajo** — decisiones de diseño y protocolo experimental
3. **Paper** — artículo IEEE embebido (`paper/main.pdf`, 9 páginas)
4. **Afiche EXPOTIC** — póster embebido (`EXPOTIC/afiche-triple-enfoque-resolutivo.pdf`)
5. **El repositorio** — requisitos, arquitectura (diagramas UML), componentes y extensión
6. **Conclusión** — cierre global de la tesis

**Bibliografía** — 32 referencias, reutilizando `paper/referencias.bib`.

Extensión total: 53 páginas.

Autor: Benjamín Peña Díaz · Profesor guía: Gustavo Gatica (UNAB) ·
Profesor co-guía: Rodrigo Linfati (Universidad del Bío-Bío).

## Presentación

`presentacion.html` — presentación de defensa de **11:35 minutos**, 14 diapositivas,
en español. Se abre con doble clic en cualquier navegador; no requiere instalación
ni conexión (salvo las tipografías de Google Fonts, que degradan a las del sistema).

| Tecla | Acción |
|-------|--------|
| `←` `→` `espacio` | Navegar entre diapositivas |
| `N` | Abrir/cerrar las **notas del expositor** |
| `F` | Pantalla completa |
| `Inicio` / `Fin` | Primera / última diapositiva |

También funciona con las flechas laterales, los puntos inferiores y gestos
táctiles. La repetición automática de tecla se ignora, así que mantener
apretado el clicker no desboca las diapositivas.

### Animaciones

El cambio de diapositiva es **direccional en 3D**: al avanzar, la nueva entra
desde la derecha girando sobre su eje vertical mientras la anterior se aleja
hacia la izquierda; al retroceder, el movimiento se invierte.

Las transiciones animan únicamente `transform` y `opacity`, que el navegador
resuelve en la GPU sin recalcular diseño ni pintura. `will-change` se aplica
sólo durante la transición para no sostener catorce capas de pantalla completa
en memoria.

Dentro de cada diapositiva el contenido entra escalonado según su tipo: el
título se revela con cortina, la línea del rótulo se dibuja sola, las tarjetas
suben en cascada con un empuje 3D, los indicadores numéricos rebotan, los pasos
del diagrama entran de izquierda a derecha y las barras del gráfico crecen
grupo por grupo. El documento respeta `prefers-reduced-motion`: si el sistema
pide menos movimiento, todo se reduce a un fundido simple.

### Distribución del tiempo

Cada diapositiva declara su tiempo sugerido en el atributo `data-time`, y el
panel de notas muestra el acumulado:

| # | Diapositiva | Tiempo |
|---|-------------|--------|
| 1 | Portada | 0:30 |
| 2 | El problema | 0:50 |
| 3 | Lo que la literatura no responde | 0:45 |
| 4 | Objetivos | 0:50 |
| 5 | Cinco problemas clásicos | 0:50 |
| 6 | ¿Cómo funciona la Búsqueda Tabú? | 0:55 |
| 7 | Tres niveles progresivos | 1:00 |
| 8 | Diseño experimental | 0:45 |
| 9 | GAP promedio por problema | 1:10 |
| 10 | Hallazgos clave | 1:00 |
| 11 | ¿Qué mecanismo aporta más? | 0:55 |
| 12 | El repositorio | 0:50 |
| 13 | Conclusiones y trabajo futuro | 0:55 |
| 14 | Cierre | 0:20 |
| | **Total** | **11:35** |

Para ajustar la duración, edita el atributo `data-time` de la diapositiva
correspondiente: el acumulado que muestra el panel de notas se recalcula solo.

## Compilar

**Windows:** doble clic en `compilar.bat` (o `cd TESIS && compilar.bat`).
**Linux / macOS:** `cd TESIS && ./compilar.sh`

El script hace las cuatro pasadas, comprueba que estén las dependencias, avisa
si quedan citas o referencias sin resolver y limpia los archivos temporales.
Si algo falla, conserva `tesis.log` para que puedas revisarlo.

A mano, si prefieres:

```bash
cd TESIS
pdflatex tesis.tex        # 1.ª pasada
bibtex   tesis            # resuelve la bibliografía
pdflatex tesis.tex        # 2.ª pasada: inserta las citas
pdflatex tesis.tex        # 3.ª pasada: índices y referencias cruzadas
```

Las cuatro pasadas son necesarias: sin `bibtex` las citas salen como `[?]`, y
sin la última pasada el índice queda desactualizado.

> El PDF compilado (`tesis.pdf`) no se versiona: se genera en cada compilación
> y está en `.gitignore` junto al resto de artefactos de LaTeX.

**Requisitos LaTeX:** `babel` con soporte de español (`texlive-lang-spanish`),
`siunitx`, `pdfpages`, `listings`, `cite`, `microtype`, `booktabs`,
`multirow`, `enumitem`, `geometry`, `setspace`, `caption`, `float`, `hyperref`,
`tikz`. Son los mismos que ya requiere `paper/main.tex`, más `pdfpages` y
`listings`.

## Regenerar las figuras

```bash
python TESIS/generar_figuras.py
```

Lee `results/tabla_consolidada.csv` y regenera los cuatro PDF de `figuras/`.
El logo de la portada (`figuras/logo_unab_ingenieria.png`) no se regenera.

## Estructura

```
TESIS/
├── tesis.tex               Documento maestro (preámbulo, portada, índices)
├── secciones/
│   ├── 00_agradecimientos.tex
│   ├── 00_declaracion_ia.tex  Declaración de uso de inteligencia artificial
│   ├── 00_resumen.tex      Resumen y palabras clave
│   ├── 00_siglas.tex       Siglas y nomenclatura
│   ├── 01_motivo.tex       Cap. 1 — Motivación
│   ├── 02_metodologia.tex  Cap. 2 — Metodología de trabajo
│   ├── 03_paper.tex        Cap. 3 — Paper (portadilla + \includepdf)
│   ├── 04_afiche.tex       Cap. 4 — Afiche EXPOTIC (portadilla + \includepdf)
│   ├── 05_repositorio.tex  Cap. 5 — El repositorio
│   └── 06_conclusion.tex   Cap. 6 — Conclusión
├── codigos/                Fragmentos de código insertados con \lstinputlisting
├── figuras/                Figuras propias del documento + logo
├── presentacion.html       Presentación de defensa (11:35 min, español)
├── generar_figuras.py      Script que reconstruye las figuras desde el CSV
├── PLAN_DE_TRABAJO.md      Plan original y estado de los puntos abiertos
├── PLAN_DE_CORRECCIONES.md Revisión del documento y correcciones aplicadas
└── CORRECCIONES_REVISION_2026-09-25.md  Correcciones del profesor guía (25-09-2026)
```

## Dependencias externas

`tesis.tex` referencia tres archivos fuera de esta carpeta mediante rutas
relativas. Los tres están versionados en el repositorio, de modo que el
documento compila desde un clon limpio:

- `../paper/main.pdf` — se inserta completo como capítulo 3
- `../EXPOTIC/afiche-triple-enfoque-resolutivo.pdf` — capítulo 4
- `../paper/referencias.bib` — fuente de la bibliografía

Si se recompila `paper/main.tex`, hay que regenerar `paper/main.pdf` antes de
volver a compilar la tesis, porque el capítulo 3 inserta el PDF, no el fuente.

## Pendiente

Los puntos abiertos de la última revisión están en
`CORRECCIONES_REVISION_2026-09-25.md`. El documento ya no contiene recuadros
`\pendiente`.

El apartado de las siglas **CRJ / ORJ** y **ESP** está reservado y marcado
visualmente en el Capítulo 1 (`secciones/01_motivo.tex`, macro `\pendiente`).
No corresponden a ninguna nomenclatura presente en el repositorio ni en el
paper. Una vez confirmado su significado, se reemplaza el bloque `\pendiente{...}`
por el contenido correspondiente.
