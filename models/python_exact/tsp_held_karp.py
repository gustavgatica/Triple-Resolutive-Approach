"""
tsp_held_karp.py — Solver exacto para TSP mediante el algoritmo de
Held-Karp (programación dinámica con bitmask).

Complejidad: O(2^n · n^2) en tiempo, O(2^n · n) en espacio.
Límite práctico: n ≤ 20 ciudades.

Para instancias TSPLIB (berlin52, eil51, etc.) este solver no es
aplicable directamente; en ese caso se reporta la cota inferior
greedy (vecino más cercano) como referencia, y el BKS proviene
de la literatura.

Uso desde CLI:
    python tsp_held_karp.py ../../instances/tsp/eil10.tsp  (instancia pequeña)
    python tsp_held_karp.py ../../instances/tsp/berlin52.tsp  (solo greedy)

Uso como módulo:
    from tsp_held_karp import held_karp, nearest_neighbor
    cost, tour = held_karp(dist_matrix)
"""

import sys
import os
import time
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from loader import load_tsp


# ──────────────────────────────────────────────────────────────
# Algoritmo de Held-Karp (exacto, n ≤ 20)
# ──────────────────────────────────────────────────────────────
def held_karp(dist: list) -> tuple:
    """
    Resuelve el TSP exactamente con Held-Karp (DP + bitmask).

    Parámetros:
        dist : matriz de distancias n×n (list of lists)

    Retorna:
        (optimal_cost, tour)  donde tour es una lista de índices 0-based.
    """
    n = len(dist)
    if n > 20:
        raise ValueError(f"Held-Karp solo es práctico para n≤20 (instancia tiene n={n})")

    INF = float('inf')
    FULL = (1 << n) - 1

    # dp[S][i] = costo mínimo de recorrer exactamente el conjunto S de ciudades,
    #            terminando en la ciudad i, partiendo desde la ciudad 0.
    dp = [[INF] * n for _ in range(1 << n)]
    parent = [[-1] * n for _ in range(1 << n)]

    dp[1][0] = 0  # Empezar en ciudad 0, conjunto {0}

    for S in range(1, 1 << n):
        if not (S & 1):          # el conjunto S debe incluir la ciudad 0
            continue
        for u in range(n):
            if not (S >> u & 1):
                continue
            if dp[S][u] == INF:
                continue
            # Expandir hacia cada ciudad v no visitada
            for v in range(n):
                if S >> v & 1:
                    continue
                S2 = S | (1 << v)
                new_cost = dp[S][u] + dist[u][v]
                if new_cost < dp[S2][v]:
                    dp[S2][v] = new_cost
                    parent[S2][v] = u

    # Cerrar el tour: regresar a ciudad 0
    opt_cost = INF
    last = -1
    for u in range(1, n):
        cost = dp[FULL][u] + dist[u][0]
        if cost < opt_cost:
            opt_cost = cost
            last = u

    # Reconstruir el tour
    tour = []
    S = FULL
    cur = last
    while cur != -1:
        tour.append(cur)
        prev = parent[S][cur]
        S = S ^ (1 << cur)
        cur = prev
    tour.reverse()

    return opt_cost, tour


# ──────────────────────────────────────────────────────────────
# Heurística Vecino Más Cercano (cota inferior de referencia)
# ──────────────────────────────────────────────────────────────
def nearest_neighbor(dist: list, start: int = 0) -> tuple:
    """
    Heurística del vecino más cercano para TSP.
    No es exacta, pero sirve como solución inicial y referencia.

    Retorna:
        (cost, tour)
    """
    n = len(dist)
    visited = [False] * n
    tour = [start]
    visited[start] = True
    current = start

    for _ in range(n - 1):
        best_d, best_j = float('inf'), -1
        for j in range(n):
            if not visited[j] and dist[current][j] < best_d:
                best_d = dist[current][j]
                best_j = j
        tour.append(best_j)
        visited[best_j] = True
        current = best_j

    cost = sum(dist[tour[i]][tour[(i + 1) % n]] for i in range(n))
    return cost, tour


def tour_cost(tour: list, dist: list) -> int:
    """Calcula el costo de un tour dado."""
    n = len(tour)
    return sum(dist[tour[i]][tour[(i + 1) % n]] for i in range(n))


# ──────────────────────────────────────────────────────────────
# Resolver desde archivo
# ──────────────────────────────────────────────────────────────
def solve_from_file(filepath: str) -> dict:
    inst = load_tsp(filepath)
    n = inst['n']
    dist = inst['dist_matrix']
    bks = inst['bks']

    result = {
        'instance':   inst['name'],
        'n':          n,
        'bks':        bks,
        'method':     None,
        'value':      None,
        'tour':       None,
        'gap_pct':    None,
        'time_s':     None,
    }

    if n <= 20:
        # Exacto con Held-Karp
        t0 = time.perf_counter()
        cost, tour = held_karp(dist)
        elapsed = time.perf_counter() - t0
        result.update({
            'method':  'Held-Karp (exacto)',
            'value':   cost,
            'tour':    tour,
            'time_s':  elapsed,
        })
    else:
        # Demasiado grande para Held-Karp → solo vecino más cercano
        t0 = time.perf_counter()
        # Mejor de 5 inicios distintos
        best_cost, best_tour = float('inf'), None
        for start in range(min(5, n)):
            c, t = nearest_neighbor(dist, start)
            if c < best_cost:
                best_cost, best_tour = c, t
        elapsed = time.perf_counter() - t0
        result.update({
            'method':  f'Vecino-Más-Cercano (n={n}, heurística)',
            'value':   best_cost,
            'tour':    best_tour,
            'time_s':  elapsed,
        })

    if bks is not None and result['value'] is not None:
        result['gap_pct'] = (result['value'] - bks) / bks * 100.0

    return result


def print_result(r: dict):
    print(f"\nInstancia : {r['instance']}")
    print(f"n         : {r['n']} ciudades")
    print(f"Método    : {r['method']}")
    print(f"BKS       : {r['bks']}")
    print(f"Costo     : {r['value']}")
    if r['gap_pct'] is not None:
        print(f"GAP       : {r['gap_pct']:.2f}%")
    print(f"Tiempo    : {r['time_s']:.4f} s")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python tsp_held_karp.py <archivo.tsp>")
        print("\nEjecutando en TODAS las instancias TSP del proyecto...")

        base = os.path.join(os.path.dirname(__file__), '..', '..', 'instances', 'tsp')
        files = sorted(f for f in os.listdir(base) if f.endswith('.tsp'))

        print(f"\n{'Instancia':<12} {'n':>5} {'BKS':>8} {'Valor':>8} {'GAP%':>8} {'Tiempo(s)':>10}  Método")
        print("-" * 70)
        for fname in files:
            r = solve_from_file(os.path.join(base, fname))
            gap_str = f"{r['gap_pct']:.2f}" if r['gap_pct'] is not None else "N/A"
            method_short = r['method'].split('(')[0].strip()
            print(f"{r['instance']:<12} {r['n']:>5} {str(r['bks']):>8} {r['value']:>8} "
                  f"{gap_str:>8} {r['time_s']:>10.4f}  {method_short}")
    else:
        r = solve_from_file(sys.argv[1])
        print_result(r)
