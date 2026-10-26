"""
TS-Avanzado para TSP
=====================
Mejoras sobre TS-Intermedio:
  1. MEMORIA DE FRECUENCIA DE ARISTAS: freq[a][b] = nº de veces que la arista
     (a,b) fue eliminada por un movimiento 2-opt.
  2. PENALIZACIÓN ADAPTATIVA: coste_penalizado = delta - λ·freq[a][b]
     (favorece eliminar aristas poco usadas → diversificación).
  3. λ ADAPTATIVO: aumenta cuando estancado, baja al mejorar.
  4. REINICIO desde mejor solución perturbada si sin mejora > límite.
  5. Más iteraciones (3000).
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
        nxt  = min((j for j in range(n) if not visited[j]), key=lambda j: dist[last][j])
        tour.append(nxt)
        visited[nxt] = True
    return tour


def _two_opt_delta(tour, i, j, dist):
    n = len(tour)
    a, b = tour[i], tour[(i + 1) % n]
    c, d = tour[j], tour[(j + 1) % n]
    return dist[a][c] + dist[b][d] - dist[a][b] - dist[c][d]


def _perturb_double_bridge(tour, rng):
    """Double-bridge perturbation (4-opt move) to escape local optima."""
    n = len(tour)
    positions = sorted(rng.sample(range(1, n), 4))
    a, b, c, d = positions
    # Reconnect segments in different order
    new_tour = (tour[:a] + tour[c:d] + tour[b:c] + tour[a:b] + tour[d:])
    return new_tour


def solve(instance_data: dict,
          tabu_min: int = 7,
          tabu_max: int = 25,
          change_every: int = 150,
          lambda_init: float = 0.0,
          lambda_max: float = 5.0,
          lambda_step_up: float = 0.2,
          lambda_step_down: float = 0.1,
          no_improve_limit: int = 300,
          max_iter: int = 3000,
          seed: int = 42) -> dict:
    """
    Tabu Search Avanzado para TSP.

    Returns dict: value, solution, iterations, time_s, history
    """
    rng = random.Random(seed)

    dist = instance_data['dist_matrix']
    n    = instance_data['n']

    current  = _nearest_neighbor_tour(n, dist)
    cur_cost = _tour_cost(current, dist)

    best      = current[:]
    best_cost = cur_cost

    tabu_size = rng.randint(tabu_min, tabu_max)
    tabu_list = deque(maxlen=tabu_size)

    # Frequency memory: freq[a][b] = times edge (a,b) was removed
    freq = [[0] * n for _ in range(n)]

    lam        = lambda_init
    no_improve = 0
    history    = [(0, best_cost)]
    t0 = time.perf_counter()

    for it in range(1, max_iter + 1):

        # Dynamic tabu size
        if it % change_every == 0:
            new_size  = rng.randint(tabu_min, tabu_max)
            tabu_list = deque(list(tabu_list)[-new_size:], maxlen=new_size)

        # Double-bridge restart if very stuck
        if no_improve >= no_improve_limit:
            current   = _perturb_double_bridge(best[:], rng)
            cur_cost  = _tour_cost(current, dist)
            tabu_list.clear()
            no_improve = 0

        best_penalized = float('inf')
        best_move      = None

        for i in range(n - 1):
            for j in range(i + 2, n):
                if i == 0 and j == n - 1:
                    continue

                delta = _two_opt_delta(current, i, j, dist)
                move  = (min(current[i], current[j]), max(current[i], current[j]))

                is_tabu  = move in tabu_list
                new_cost = cur_cost + delta

                if is_tabu and new_cost >= best_cost:
                    continue

                # Penalized delta: penalize frequently-removed edges
                a, b = current[i], current[(i + 1) % n]
                c, d = current[j], current[(j + 1) % n]
                pen_delta = delta + lam * (freq[a][b] + freq[c][d])

                if pen_delta < best_penalized:
                    best_penalized = pen_delta
                    best_move      = (i, j, move, a, b, c, d)

        if best_move is None:
            i = rng.randint(0, n - 2)
            j = rng.randint(i + 2, n - 1)
            delta = _two_opt_delta(current, i, j, dist)
            best_move = (i, j,
                         (min(current[i], current[j]), max(current[i], current[j])),
                         current[i], current[(i+1)%n],
                         current[j], current[(j+1)%n])

        i, j, move, a, b, c, d = best_move
        current[i + 1:j + 1] = current[i + 1:j + 1][::-1]
        cur_cost = _tour_cost(current, dist)

        # Update frequency for removed edges
        freq[a][b] += 1
        freq[b][a] += 1
        freq[c][d] += 1
        freq[d][c] += 1

        tabu_list.append(move)

        if cur_cost < best_cost:
            best       = current[:]
            best_cost  = cur_cost
            no_improve = 0
            lam        = max(lambda_init, lam - lambda_step_down)
        else:
            no_improve += 1
            if no_improve % 50 == 0:
                lam = min(lambda_max, lam + lambda_step_up)

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
    print(f"{'Instance':<15} {'BKS':>8} {'TS-Avanz':>10} {'GAP%':>8} {'Time(s)':>8}")
    print('-' * 55)
    for fp in tsp_files:
        name = os.path.splitext(os.path.basename(fp))[0]
        data = load_instance(fp)
        res  = solve(data, max_iter=500)
        bks  = data.get('bks', res['value'])
        gap  = (res['value'] - bks) / bks * 100 if bks > 0 else 0.0
        print(f"{name:<15} {bks:>8} {res['value']:>10.1f} {gap:>7.2f}% {res['time_s']:>8.4f}")
