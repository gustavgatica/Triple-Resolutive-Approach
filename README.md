# Triple Enfoque Resolutivo

**Un Repositorio de Cinco Problemas de Optimización Combinatoria con Soluciones Exactas y Metaheurísticas**

**Autores:** Benjamín Peña Díaz (Universidad Andrés Bello) · Gustavo Gatica, profesor guía (Universidad Andrés Bello) · Rodrigo Linfati, profesor co-guía (Universidad del Bío-Bío)

Proyecto de título de Ingeniería Civil Informática, Universidad Andrés Bello, Santiago, Chile, 2026.

> **English summary.** This repository implements three progressive Tabu Search configurations (basic, intermediate and advanced) for five classical combinatorial optimization problems: 0/1 knapsack, TSP, CVRP, permutation flowshop and job shop. It includes the 24 benchmark instances, exact reference models, an experiment orchestrator and the raw results of the 360 runs (24 instances × 3 configurations × 5 seeds). On average, the advanced configuration lowers the gap to the best-known solution from 6.50 % to 3.40 %, at about 3.9 times the computing time.

---

## Descripción

Este repositorio implementa el **Triple Enfoque Resolutivo**: tres configuraciones progresivas de Búsqueda Tabú (TS-Básico, TS-Intermedio y TS-Avanzado) aplicadas a cinco problemas NP-difíciles de optimización combinatoria. Incluye instancias benchmark estándar, modelos de referencia exactos y los resultados completos de **360 experimentos** (24 instancias × 3 algoritmos × 5 semillas independientes).

### Los cinco problemas

| # | Problema | Fuente de instancias | Instancias |
|---|----------|----------------------|------------|
| 1 | Knapsack 0/1 | Pisinger | knapPI_11 – knapPI_15 |
| 2 | TSP | TSPLIB (Reinelt) | eil51, berlin52, eil76, kroA100, kroB100 |
| 3 | CVRP | Christofides | vrpnc1 – vrpnc4 |
| 4 | Flowshop (PFSP) | Taillard Benchmarks | ta001, ta011, ta021, ta031, ta041 |
| 5 | Job Shop (JSSP) | Fisher & Thompson / Lawrence | ft10, la01, la06, la11, la21 |

### Los tres algoritmos

| Algoritmo | Descripción |
|-----------|-------------|
| **TS-Básico** | Lista tabú fija, vecindad simple, sin intensificación |
| **TS-Intermedio** | Lista tabú dinámica, criterio de aspiración, reinicio suave |
| **TS-Avanzado** | Memoria de frecuencia, penalización adaptativa, diversificación informada |

### Soluciones iniciales

| Problema | Heurística constructiva |
|----------|-------------------------|
| Knapsack | Greedy por ratio ganancia/peso decreciente |
| TSP | Vecino más cercano desde el nodo 0 |
| CVRP | Ahorros de Clarke-Wright |
| Flowshop | NEH |
| Job Shop | Giffler-Thompson con prioridad por tiempo de procesamiento decreciente |

---

## Estructura del repositorio

```
.
├── instances/          # Instancias benchmark (24 archivos)
│   ├── knapsack/
│   ├── tsp/
│   ├── vrp/
│   ├── flowshop/
│   └── jobshop/
├── models/
│   ├── ampl/           # Modelos AMPL de referencia exacta (5 .mod)
│   └── python_exact/   # Solvers exactos en Python (Knapsack DP, TSP Held-Karp, Flowshop)
├── tabu_search/        # Implementaciones de los 3 algoritmos × 5 problemas
│   ├── knapsack/
│   ├── tsp/
│   ├── vrp/
│   ├── flowshop/
│   └── jobshop/
├── src/
│   ├── loader.py       # Carga de instancias y BKS
│   ├── runner.py       # Ejecutor de un experimento individual
│   ├── metrics.py      # Cálculo de GAP y métricas
│   ├── reporter.py     # Generador del CSV consolidado
│   └── main.py         # CLI principal
├── output/             # Resultados crudos (una carpeta por experimento, con resultado.json y solucion.txt)
├── results/            # CSVs consolidados por problema y global
├── notebooks/          # Análisis en Jupyter (5 notebooks)
├── paper/              # Paper IEEE en LaTeX (español)
├── PAPER ECP 2026/     # Artículo en inglés para Engineering Proceedings (MDPI), ECP 2026
├── EXPOTIC/            # Afiche, artículo y presentación de EXPOTIC 2026
├── TESIS/              # Documento de tesis en LaTeX (se compila con TESIS/compilar.sh)
└── requirements.txt
```

---

## Reproducción de experimentos

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Ejecutar todos los experimentos

Reproducción completa del paper — 360 experimentos con las 5 semillas
`{42, 123, 456, 789, 1337}`:

```bash
python src/main.py --all --multi-seed
```

Corrida rápida con una sola semilla (72 experimentos, `seed=42`):

```bash
python src/main.py --all
```

Los resultados se guardan en `output/`. Esa carpeta trae las corridas usadas en el trabajo; algunas combinaciones se ejecutaron más de una vez, y `src/reporter.py` usa la más reciente de cada una.

### 3. Generar el reporte consolidado

```bash
python src/main.py --report
```

Genera `results/tabla_consolidada.csv` con GAP% y tiempos (media y desviación estándar sobre las semillas) para todas las instancias.

### Ejecutar un experimento individual

```bash
python src/main.py --problema tsp --instancia berlin52 --algoritmo ts_basico
```

### Opciones CLI

```
--problema     {knapsack, tsp, vrp, flowshop, jobshop}
--instancia    nombre de instancia (sin extensión)
--algoritmo    {ts_basico, ts_intermedio, ts_avanzado}
--seed         semilla aleatoria (default: 42)
--all          ejecuta todos los experimentos
--multi-seed   usa las 5 semillas {42, 123, 456, 789, 1337} en lugar de una
--all-instances  todas las instancias del problema indicado
--all-algoritmos todos los algoritmos
--report       genera CSVs de resultados
--list         lista las instancias disponibles
```

---

## Resultados

Los resultados de referencia (5 semillas, 360 experimentos) están incluidos en el repositorio:

| Problema | TS-Básico | TS-Intermedio | TS-Avanzado |
|----------|-----------|---------------|-------------|
| Knapsack | 0.22 % | 0.13 % | 0.10 % |
| TSP | 2.42 % | 2.15 % | 1.22 % |
| CVRP | 19.22 % | 7.72 % | 6.38 % |
| Flowshop | 1.74 % | 1.74 % | 1.75 % |
| Job Shop | 8.89 % | 8.24 % | 7.52 % |
| **Global** | **6.50 %** | **4.00 %** | **3.40 %** |

La transición de TS-Básico a TS-Avanzado reduce el GAP global un 48 % relativo, a un costo de ~3.9× el tiempo de cómputo. El CSV completo está en `results/tabla_consolidada.csv`.

---

## Análisis

Los notebooks en `notebooks/` permiten reproducir todo el análisis visual:

```bash
jupyter notebook notebooks/analisis_tsp.ipynb
```

Hay un notebook por problema: `analisis_knapsack`, `analisis_tsp`, `analisis_vrp`, `analisis_flowshop`, `analisis_jobshop`.

---

## Modelos exactos

Los modelos AMPL en `models/ampl/` requieren una licencia de [AMPL](https://ampl.com/). Para los tres problemas con solver Python disponible, se puede verificar el BKS directamente:

```bash
python models/python_exact/knapsack_dp.py
python models/python_exact/tsp_held_karp.py
python models/python_exact/flowshop_exact.py
```

---

## Paper

El paper IEEE en formato LaTeX está en `paper/`. Para compilar:

```bash
cd paper && pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
```

O bien, subir la carpeta `paper/` a [Overleaf](https://overleaf.com).

---

## Publicaciones

- **ECP 2026.** Resumen publicado en *The 5th International Electronic Conference on Processes* (MDPI), sesión S4: https://sciforum.net/paper/35126
- **Engineering Proceedings (MDPI).** Artículo extendido enviado; el fuente está en `PAPER ECP 2026/`.
- **EXPOTIC 2026, UNAB.** Afiche y artículo en `EXPOTIC/`.

---

## Citación

```
Peña Díaz, B., Gatica, G. y Linfati, R. (2026). Triple Enfoque Resolutivo: un
repositorio de cinco problemas de optimización combinatoria con soluciones exactas
y metaheurísticas. Proyecto de título, Universidad Andrés Bello, Santiago, Chile.
```

También hay un archivo `CITATION.cff`, que GitHub muestra en el botón «Cite this repository».

---

## Licencia

Código bajo licencia MIT (ver `LICENSE`). Las instancias benchmark pertenecen a sus autores originales (TSPLIB, Christofides, Taillard, Fisher y Thompson, Lawrence, Pisinger) y se incluyen solo para reproducir los experimentos.
