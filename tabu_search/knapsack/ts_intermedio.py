"""
TS-Intermedio para Knapsack 0-1
================================
Mejoras sobre TS-Básico:
  1. Lista tabú DINÁMICA: tamaño varía entre tabu_min y tabu_max cada
     `change_every` iteraciones (rompe ciclos, diversificación implícita).
  2. Criterio de ASPIRACIÓN explícito: cualquier movimiento tabú se acepta
     si produce una solución mejor que el mejor global conocido.
  3. Mayor número de iteraciones (1000 vs 500).
"""

import sys
import os
import time
import random
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from loader import load_instance, list_all_instances


def _value_weight(solution, profits, weights):
    v = sum(profits[i] for i in range(len(solution)) if solution[i])
    w = sum(weights[i] for i in range(len(solution)) if solution[i])
    return v, w


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
          max_iter: int = 1000,
          seed: int = 42) -> dict:
    """
    Tabu Search Intermedio para Knapsack 0-1.

    Returns dict: value, solution, iterations, time_s, history
    """
    random.seed(seed)

    profits  = instance_data['profits']
    weights  = instance_data['weights']
    capacity = instance_data['capacity']
    n        = instance_data['n']

    current = _greedy_initial(n, profits, weights, capacity)
    cur_val, cur_w = _value_weight(current, profits, weights)

    best     = current[:]
    best_val = cur_val

    # Dynamic tabu list
    tabu_size = random.randint(tabu_min, tabu_max)
    tabu_list = deque(maxlen=tabu_size)

    history = [(0, best_val)]
    t0 = time.perf_counter()

    for it in range(1, max_iter + 1):

        # --- Dynamically resize tabu list every `change_every` iters ---
        if it % change_every == 0:
            new_size = random.randint(tabu_min, tabu_max)
            # Rebuild deque with new maxlen (keep recent entries)
            tabu_list = deque(list(tabu_list)[-new_size:], maxlen=new_size)
            tabu_size = new_size

        best_move         = None
        best_neighbor_val = -1

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

            # Aspiration: override tabu if this is a new global best
            aspiration_override = is_tabu and (new_val > best_val)

            if is_tabu and not aspiration_override:
                continue

            if new_val > best_neighbor_val:
                best_neighbor_val = new_val
                best_move = i

        if best_move is None:
            candidates = [i for i in range(n)
                          if i not in tabu_list and
                          (cur_w - weights[i] if current[i] else cur_w + weights[i]) <= capacity]
            if not candidates:
                break
            best_move = random.choice(candidates)
            best_neighbor_val = (cur_val + profits[best_move]
                                 if current[best_move] == 0
                                 else cur_val - profits[best_move])

        # Apply move
        current[best_move] = 1 - current[best_move]
        if current[best_move] == 1:
            cur_val += profits[best_move]
            cur_w   += weights[best_move]
        else:
            cur_val -= profits[best_move]
            cur_w   -= weights[best_move]

        tabu_list.append(best_move)

        if cur_val > best_val:
            best     = current[:]
            best_val = cur_val

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
    print(f"{'Instance':<20} {'BKS':>8} {'TS-Inter':>10} {'GAP%':>8} {'Time(s)':>8}")
    print('-' * 60)
    for fp in kp_files:
        name = os.path.splitext(os.path.basename(fp))[0]
        data = load_instance(fp)
        res  = solve(data)
        bks  = data.get('bks', res['value'])
        gap  = (bks - res['value']) / bks * 100 if bks > 0 else 0.0
        print(f"{name:<20} {bks:>8} {res['value']:>10} {gap:>7.2f}% {res['time_s']:>8.4f}")
