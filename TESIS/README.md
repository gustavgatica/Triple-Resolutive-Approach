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

> `tesis.pdf` es la versión entregada (53 páginas). Al recompilar con otra
> versión de LaTeX el contenido es el mismo, aunque los decimales pueden salir
> con coma en vez de punto por la configuración regional de `siunitx`.

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
├── tesis.pdf               Versión entregada del documento (53 páginas)
├── generar_figuras.py      Script que reconstruye las figuras desde el CSV
├── compilar.sh             Compilación en Linux o macOS
└── compilar.bat            Compilación en Windows
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
