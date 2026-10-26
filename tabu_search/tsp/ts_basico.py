"""
TS-Básico para TSP (Travelling Salesman Problem)
=================================================
Vecindario: 2-opt (inversión de subsegmento de ruta)
Lista tabú: fija, tamaño 10, almacena par de aristas eliminadas (i,j) ordenado
Criterio de parada: max_iter iteraciones
"""

import sys
import os
import time
import random
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from loader import load_instance, list_all_instances


def _tour_cost(tour, dist):
    n = len(tour)
    return sum(dist[tour[i]][tour[(i + 1) % n]] for i in range(n))


def _nearest_neighbor_tour(n, dist, start=0):
    visited = [False] * n
    tour = [start]
    visited[start] = True
    for _ in range(n - 1):
        last = tour[-1]
        nxt = min((j for j in range(n) if not visited[j]),
                  key=lambda j: dist[last][j])
        tour.append(nxt)
        visited[nxt] = True
    return tour


def _two_opt_delta(tour, i, j, dist):
    """
    Cost change for reversing segment tour[i+1..j].
    Removes edges (tour[i], tour[i+1]) and (tour[j], tour[j+1]).
    """
    n = len(tour)
    a, b = tour[i], tour[(i + 1) % n]
    c, d = tour[j], tour[(j + 1) % n]
    return dist[a][c] + dist[b][d] - dist[a][b] - dist[c][d]


def solve(instance_data: dict,
          tabu_size: int = 10,
          max_iter: int = 1000,
          seed: int = 42) -> dict:
    """
    Tabu Search Básico para TSP.

    Returns
    -------
    dict with keys:
        value     : best tour length found (float/int)
        solution  : best tour as list of city indices
        iterations: number of iterations executed
        time_s    : elapsed time in seconds
        history   : list of (iteration, best_value) tuples
    """
    random.seed(seed)

    dist = instance_data['dist_matrix']
    n    = instance_data['n']

    # --- Initial solution: nearest neighbor from city 0 ---
    current = _nearest_neighbor_tour(n, dist)
    cur_cost = _tour_cost(current, dist)

    best = current[:]
    best_cost = cur_cost

    tabu_list = deque(maxlen=tabu_size)
    history = [(0, best_cost)]

    t0 = time.perf_counter()

    for it in range(1, max_iter + 1):
        best_delta = float('inf')
        best_move  = None  # (i, j) indices into tour

        # --- Explore 2-opt neighborhood ---
        for i in range(n - 1):
            for j in range(i + 2, n):
                if i == 0 and j == n - 1:
                    continue  # equivalent to no change for circular tour

                delta = _two_opt_delta(current, i, j, dist)
                move  = (min(current[i], current[j]),
                         max(current[i], current[j]))  # canonical edge pair

                is_tabu = move in tabu_list
                new_cost = cur_cost + delta

                # Accept if not tabu, or aspiration (better than global best)
                if is_tabu and new_cost >= best_cost:
                    continue

                if delta < best_delta:
                    best_delta = delta
                    best_move  = (i, j, move)

        if best_move is None:
            # Fallback: random non-tabu 2-opt
            i = random.randint(0, n - 2)
            j = random.randint(i + 2, n - 1)
            best_move = (i, j,
                         (min(current[i], current[j]),
                          max(current[i], current[j])))
            best_delta = _two_opt_delta(current, i, j, dist)

        i, j, move = best_move

        # Apply 2-opt: reverse segment current[i+1..j]
        current[i + 1:j + 1] = current[i + 1:j + 1][::-1]
        cur_cost += best_delta

        tabu_list.append(move)

        # Update global best
        if cur_cost < best_cost:
            best      = current[:]
            best_cost = cur_cost

        history.append((it, best_cost))

    elapsed = time.perf_counter() - t0

    return {
        'value':      best_cost,
        'solution':   best,
        'iterations': it,
        'time_s':     elapsed,
        'history':    history,
    }


# ---------------------------------------------------------------------------
# CLI runner
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    instances = list_all_instances(
        os.path.join(os.path.dirname(__file__), '..', '..', 'instances'))
    tsp_files = instances.get('tsp', [])

    if not tsp_files:
        print("No TSP instances found.")
        sys.exit(1)

    print(f"{'Instance':<15} {'BKS':>8} {'TS-Básico':>10} {'GAP%':>8} {'Time(s)':>8}")
    print('-' * 55)
    for fp in tsp_files:
        name = os.path.splitext(os.path.basename(fp))[0]
        data = load_instance(fp)
        res  = solve(data)
        bks  = data.get('bks', res['value'])
        gap  = (res['value'] - bks) / bks * 100 if bks > 0 else 0.0
        print(f"{name:<15} {bks:>8} {res['value']:>10.1f} {gap:>7.2f}% {res['time_s']:>8.4f}")
