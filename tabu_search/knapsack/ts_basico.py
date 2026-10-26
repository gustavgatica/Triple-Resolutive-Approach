"""
TS-Básico para Knapsack 0-1
===========================
Vecindario: flip de un bit (incluir/excluir ítem)
Lista tabú: fija, tamaño 10, almacena índice del ítem flipado
Criterio de parada: max_iter iteraciones sin mejora global
"""

import sys
import os
import time
import random
from collections import deque

# Allow running from any directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from loader import load_instance, list_all_instances


def _value_weight(solution, profits, weights):
    """Total profit and weight of a solution (binary list)."""
    v = sum(profits[i] for i in range(len(solution)) if solution[i])
    w = sum(weights[i] for i in range(len(solution)) if solution[i])
    return v, w


def _greedy_initial(n, profits, weights, capacity):
    """Greedy initial solution: add items by profit/weight ratio."""
    ratios = sorted(range(n), key=lambda i: profits[i] / max(weights[i], 1), reverse=True)
    sol = [0] * n
    remaining = capacity
    for i in ratios:
        if weights[i] <= remaining:
            sol[i] = 1
            remaining -= weights[i]
    return sol


def solve(instance_data: dict,
          tabu_size: int = 10,
          max_iter: int = 500,
          seed: int = 42) -> dict:
    """
    Tabu Search Básico para Knapsack 0-1.

    Returns
    -------
    dict with keys:
        value     : best objective value found (int)
        solution  : binary list of selected items
        iterations: number of iterations executed
        time_s    : elapsed time in seconds
        history   : list of (iteration, best_value) tuples
    """
    random.seed(seed)

    profits  = instance_data['profits']
    weights  = instance_data['weights']
    capacity = instance_data['capacity']
    n        = instance_data['n']

    # --- Initial solution ---
    current = _greedy_initial(n, profits, weights, capacity)
    cur_val, cur_w = _value_weight(current, profits, weights)

    best = current[:]
    best_val = cur_val

    tabu_list = deque(maxlen=tabu_size)
    history = [(0, best_val)]

    t0 = time.perf_counter()

    for it in range(1, max_iter + 1):
        best_move = None
        best_neighbor_val = -1

        # --- Explore full neighborhood (flip each bit) ---
        for i in range(n):
            # Compute new weight after flip
            if current[i] == 0:
                new_w = cur_w + weights[i]
            else:
                new_w = cur_w - weights[i]

            # Skip infeasible
            if new_w > capacity:
                continue

            # Compute new value
            if current[i] == 0:
                new_val = cur_val + profits[i]
            else:
                new_val = cur_val - profits[i]

            # Tabu check + aspiration (accept if better than global best)
            is_tabu = i in tabu_list
            if is_tabu and new_val <= best_val:
                continue

            if new_val > best_neighbor_val:
                best_neighbor_val = new_val
                best_move = i

        if best_move is None:
            # No feasible non-tabu move; pick random non-tabu feasible flip
            candidates = [i for i in range(n)
                          if i not in tabu_list and
                          (cur_w - weights[i] if current[i] else cur_w + weights[i]) <= capacity]
            if not candidates:
                break
            best_move = random.choice(candidates)
            if current[best_move] == 0:
                best_neighbor_val = cur_val + profits[best_move]
            else:
                best_neighbor_val = cur_val - profits[best_move]

        # Apply move
        current[best_move] = 1 - current[best_move]
        if current[best_move] == 1:
            cur_val += profits[best_move]
            cur_w  += weights[best_move]
        else:
            cur_val -= profits[best_move]
            cur_w  -= weights[best_move]

        tabu_list.append(best_move)

        # Update best
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


# ---------------------------------------------------------------------------
# CLI runner
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    base = os.path.join(os.path.dirname(__file__), '..', '..', 'instances', 'knapsack')
    instances = list_all_instances(os.path.join(os.path.dirname(__file__), '..', '..', 'instances'))
    kp_files = instances.get('knapsack', [])

    if not kp_files:
        print("No knapsack instances found.")
        sys.exit(1)

    print(f"{'Instance':<20} {'BKS':>8} {'TS-Básico':>10} {'GAP%':>8} {'Time(s)':>8}")
    print('-' * 60)
    for fp in kp_files:
        name = os.path.splitext(os.path.basename(fp))[0]
        data = load_instance(fp)
        res  = solve(data)
        bks  = data.get('bks', res['value'])
        gap  = (bks - res['value']) / bks * 100 if bks > 0 else 0.0
        print(f"{name:<20} {bks:>8} {res['value']:>10} {gap:>7.2f}% {res['time_s']:>8.4f}")
