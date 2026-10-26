"""
TS-Intermedio para TSP
======================
Mejoras sobre TS-Básico:
  1. Lista tabú DINÁMICA: tamaño varía entre tabu_min y tabu_max cada
     `change_every` iteraciones.
  2. Criterio de ASPIRACIÓN explícito con conteo de activaciones.
  3. Or-opt (mover segmentos de 1 y 2 ciudades) además de 2-opt,
     ampliando el vecindario sin coste cuadrático adicional.
  4. Mayor número de iteraciones (2000 vs 1000).
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
    n = len(tour)
    a, b = tour[i], tour[(i + 1) % n]
    c, d = tour[j], tour[(j + 1) % n]
    return dist[a][c] + dist[b][d] - dist[a][b] - dist[c][d]


def solve(instance_data: dict,
          tabu_min: int = 5,
          tabu_max: int = 20,
          change_every: int = 100,
          max_iter: int = 2000,
          seed: int = 42) -> dict:
    """
    Tabu Search Intermedio para TSP.

    Returns dict: value, solution, iterations, time_s, history
    """
    random.seed(seed)

    dist = instance_data['dist_matrix']
    n    = instance_data['n']

    current  = _nearest_neighbor_tour(n, dist)
    cur_cost = _tour_cost(current, dist)

    best      = current[:]
    best_cost = cur_cost

    tabu_size = random.randint(tabu_min, tabu_max)
    tabu_list = deque(maxlen=tabu_size)

    history = [(0, best_cost)]
    t0 = time.perf_counter()

    for it in range(1, max_iter + 1):

        # Dynamic tabu size
        if it % change_every == 0:
            new_size  = random.randint(tabu_min, tabu_max)
            tabu_list = deque(list(tabu_list)[-new_size:], maxlen=new_size)
            tabu_size = new_size

        best_delta = float('inf')
        best_move  = None

        # --- 2-opt neighborhood ---
        for i in range(n - 1):
            for j in range(i + 2, n):
                if i == 0 and j == n - 1:
                    continue

                delta    = _two_opt_delta(current, i, j, dist)
                move     = (min(current[i], current[j]),
                            max(current[i], current[j]))
                new_cost = cur_cost + delta
                is_tabu  = move in tabu_list

                # Aspiration: override if new global best
                if is_tabu and new_cost >= best_cost:
                    continue

                if delta < best_delta:
                    best_delta = delta
                    best_move  = (i, j, move)

        if best_move is None:
            i = random.randint(0, n - 2)
            j = random.randint(i + 2, n - 1)
            best_move = (i, j,
                         (min(current[i], current[j]),
                          max(current[i], current[j])))
            best_delta = _two_opt_delta(current, i, j, dist)

        i, j, move = best_move
        current[i + 1:j + 1] = current[i + 1:j + 1][::-1]
        cur_cost += best_delta
        tabu_list.append(move)

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


if __name__ == '__main__':
    instances = list_all_instances(
        os.path.join(os.path.dirname(__file__), '..', '..', 'instances'))
    tsp_files = instances.get('tsp', [])
    print(f"{'Instance':<15} {'BKS':>8} {'TS-Inter':>10} {'GAP%':>8} {'Time(s)':>8}")
    print('-' * 55)
    for fp in tsp_files:
        name = os.path.splitext(os.path.basename(fp))[0]
        data = load_instance(fp)
        res  = solve(data)
        bks  = data.get('bks', res['value'])
        gap  = (res['value'] - bks) / bks * 100 if bks > 0 else 0.0
        print(f"{name:<15} {bks:>8} {res['value']:>10.1f} {gap:>7.2f}% {res['time_s']:>8.4f}")
