"""
TS-Avanzado para Knapsack 0-1
==============================
Mejoras sobre TS-Intermedio:
  1. MEMORIA DE FRECUENCIA: freq[i] = nº de veces que el ítem i fue incluido.
  2. PENALIZACIÓN ADAPTATIVA: al evaluar movimientos, añade λ·freq[i] al coste
     para desincentivar ítems muy visitados.
  3. DIVERSIFICACIÓN ADAPTATIVA: λ aumenta cuando la búsqueda está estancada y
     decrece cuando se encuentra mejora (balance intensificación/diversificación).
  4. Más iteraciones (2000).
"""

import sys
import os
import time
import random
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from loader import load_instance, list_all_instances


def _greedy_initial(n, profits, weights, capacity):
    ratios = sorted(range(n), key=lambda i: profits[i] / max(weights[i], 1), reverse=True)
    sol = [0] * n
    remaining = capacity
    for i in ratios:
        if weights[i] <= remaining:
            sol[i] = 1
            remaining -= weights[i]
    return sol


def solve(instance_data: dict,
          tabu_min: int = 5,
          tabu_max: int = 15,
          change_every: int = 50,
          lambda_init: float = 0.1,
          lambda_max: float = 2.0,
          lambda_step_up: float = 0.05,
          lambda_step_down: float = 0.02,
          no_improve_limit: int = 200,
          max_iter: int = 2000,
          seed: int = 42) -> dict:
    """
    Tabu Search Avanzado para Knapsack 0-1.

    Returns dict: value, solution, iterations, time_s, history
    """
    rng = random.Random(seed)

    profits  = instance_data['profits']
    weights  = instance_data['weights']
    capacity = instance_data['capacity']
    n        = instance_data['n']

    current = _greedy_initial(n, profits, weights, capacity)
    cur_val = sum(profits[i] for i in range(n) if current[i])
    cur_w   = sum(weights[i] for i in range(n) if current[i])

    best     = current[:]
    best_val = cur_val

    tabu_size = rng.randint(tabu_min, tabu_max)
    tabu_list = deque(maxlen=tabu_size)

    # Frequency memory: freq[i] = how many times item i was in solution
    freq = [0] * n
    for i in range(n):
        if current[i]:
            freq[i] += 1

    lam        = lambda_init   # penalty weight
    no_improve = 0
    history    = [(0, best_val)]
    t0 = time.perf_counter()

    for it in range(1, max_iter + 1):

        # Dynamic tabu size
        if it % change_every == 0:
            new_size  = rng.randint(tabu_min, tabu_max)
            tabu_list = deque(list(tabu_list)[-new_size:], maxlen=new_size)

        best_move         = None
        best_penalized    = -float('inf')
        best_actual_val   = -1

        for i in range(n):
            if current[i] == 0:
                new_w   = cur_w + weights[i]
                new_val = cur_val + profits[i]
            else:
                new_w   = cur_w - weights[i]
                new_val = cur_val - profits[i]

            if new_w > capacity:
                continue

            is_tabu = i in tabu_list

            # Aspiration: always accept if new global best
            aspiration = is_tabu and (new_val > best_val)
            if is_tabu and not aspiration:
                continue

            # Penalized score: reward high profit, penalize frequent items
            # For include: score = profit[i] - λ·freq[i]
            # For exclude: score = -profit[i] + λ·(total_iter - freq[i])  (diversify)
            if current[i] == 0:
                pen_score = new_val - lam * freq[i]
            else:
                pen_score = new_val + lam * (it - freq[i]) / max(it, 1)

            if pen_score > best_penalized:
                best_penalized  = pen_score
                best_actual_val = new_val
                best_move = i

        if best_move is None:
            candidates = [i for i in range(n)
                          if i not in tabu_list and
                          (cur_w - weights[i] if current[i] else cur_w + weights[i]) <= capacity]
            if not candidates:
                break
            best_move = rng.choice(candidates)
            best_actual_val = (cur_val + profits[best_move] if current[best_move] == 0
                               else cur_val - profits[best_move])

        # Apply move
        current[best_move] = 1 - current[best_move]
        if current[best_move] == 1:
            cur_val += profits[best_move]
            cur_w   += weights[best_move]
            freq[best_move] += 1
        else:
            cur_val -= profits[best_move]
            cur_w   -= weights[best_move]

        tabu_list.append(best_move)

        if cur_val > best_val:
            best       = current[:]
            best_val   = cur_val
            no_improve = 0
            lam        = max(lambda_init, lam - lambda_step_down)  # intensify
        else:
            no_improve += 1
            if no_improve >= no_improve_limit:
                lam = min(lambda_max, lam + lambda_step_up)  # diversify

        history.append((it, best_val))

    elapsed = time.perf_counter() - t0
    return {
        'value':      best_val,
        'solution':   best,
        'iterations': it,
        'time_s':     elapsed,
        'history':    history,
    }


if __name__ == '__main__':
    instances = list_all_instances(
        os.path.join(os.path.dirname(__file__), '..', '..', 'instances'))
    kp_files = instances.get('knapsack', [])
    print(f"{'Instance':<20} {'BKS':>8} {'TS-Avanz':>10} {'GAP%':>8} {'Time(s)':>8}")
    print('-' * 60)
    for fp in kp_files:
        name = os.path.splitext(os.path.basename(fp))[0]
        data = load_instance(fp)
        res  = solve(data)
        bks  = data.get('bks', res['value'])
        gap  = (bks - res['value']) / bks * 100 if bks > 0 else 0.0
        print(f"{name:<20} {bks:>8} {res['value']:>10} {gap:>7.2f}% {res['time_s']:>8.4f}")
