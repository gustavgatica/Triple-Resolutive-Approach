# Modelos de referencia exacta

Este directorio contiene los modelos de referencia para verificar los valores BKS (*Best Known Solution*) usados en el cálculo de GAP.

## Estructura

```
models/
├── ampl/               # Modelos AMPL (los 5 problemas)
│   ├── knapsack.mod
│   ├── tsp_mtz.mod
│   ├── cvrp.mod
│   ├── flowshop.mod
│   └── jobshop_manne.mod
└── python_exact/       # Solvers exactos en Python (3 de 5 problemas)
    ├── knapsack_dp.py      # Programación dinámica — O(n·W)
    ├── tsp_held_karp.py    # Held-Karp — O(n²·2ⁿ)
    └── flowshop_exact.py   # DP exacto (Johnson + extensión)
```

## Disponibilidad de solvers Python por problema

| Problema | Solver Python | Motivo |
|----------|:---:|--------|
| Knapsack 0/1 | ✅ | Programación dinámica exacta, tratable para n=100 |
| TSP | ✅ | Held-Karp exacto, tratable para n≤52 (berlin52) |
| Flowshop | ✅ | DP exacto por Johnson generalizado, tratable para instancias pequeñas |
| CVRP | ❌ | ILP con variables de ruta; instancias de 50+ clientes requieren solver comercial |
| Job Shop | ❌ | ILP con disyunciones (formulación Manne); ft10 (10×10) ya supera lo tratable sin solver especializado |

Para VRP y Job Shop, los BKS provienen de la literatura:
- **CVRP**: Christofides & Eilon (1969), consolidados en OR-Library
- **Job Shop**: Fisher & Thompson (1963) y Lawrence (1984), consolidados en OR-Library

Estos valores están hardcodeados en `src/loader.py` (diccionarios `VRP_BKS` y `JOBSHOP_BKS`).

## Uso de los solvers Python

```bash
# Verificar BKS de Knapsack (instancias knapPI_11–15)
python models/python_exact/knapsack_dp.py

# Verificar BKS de TSP (berlin52, eil51, eil76)
python models/python_exact/tsp_held_karp.py

# Verificar BKS de Flowshop (ta001)
python models/python_exact/flowshop_exact.py
```

## Uso de los modelos AMPL

Requieren licencia de [AMPL](https://ampl.com/) y un solver ILP (e.g., CPLEX, Gurobi, HiGHS).

```bash
ampl knapsack.mod
ampl tsp_mtz.mod
# etc.
```

Los modelos AMPL son de referencia conceptual; no se usan en el flujo principal de experimentos.
