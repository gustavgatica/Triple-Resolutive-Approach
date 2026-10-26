"""
TS-Básico para Permutation Flowshop Scheduling
===============================================
Objetivo : minimizar makespan (Cmax)
Vecindario: intercambio de posiciones adyacentes (adjacent-swap / insertion)
Lista tabú: fija, tamaño 10, almacena el par (job_i, job_j) intercambiados
Criterio de parada: max_iter iteraciones
"""

import sys
import os
import time
import random
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from loader import load_instance, list_all_instances


# ---------------------------------------------------------------------------
# Makespan computation
# ---------------------------------------------------------------------------

def _makespan(perm, p, n_jobs, n_machines):
    """
    Compute makespan for a permutation of jobs given processing times p[job][machine].
    Uses standard DP: C[i][j] = max(C[i-1][j], C[i][j-1]) + p[perm[i]][j]
    """
    C = [[0] * n_machines for _ in range(n_jobs)]
    for i in range(n_jobs):
        for j in range(n_machines):
            prev_job  = C[i - 1][j] if i > 0 else 0
            prev_mach = C[i][j - 1] if j > 0 else 0
            C[i][j]   = max(prev_job, prev_mach) + p[perm[i]][j]
    return C[n_jobs - 1][n_machines - 1]


# ---------------------------------------------------------------------------
# NEH heuristic for initial solution
# ---------------------------------------------------------------------------

def _neh(p, n_jobs, n_machines):
    """NEH heuristic: order jobs by decreasing total processing time."""
    totals = sorted(range(n_jobs), key=lambda j: sum(p[j]), reverse=True)
    perm = [totals[0]]
    for k in range(1, n_jobs):
        job = totals[k]
        best_ms  = float('inf')
        best_pos = 0
        for pos in range(len(perm) + 1):
            trial = perm[:pos] + [job] + perm[pos:]
            ms = _makespan(trial, p, k + 1, n_machines)
            if ms < best_ms:
                best_ms  = ms
                best_pos = pos
        perm.insert(best_pos, job)
    return perm


# ---------------------------------------------------------------------------
# Main solver
# ---------------------------------------------------------------------------

def solve(instance_data: dict,
          tabu_size: int = 10,
          max_iter: int = 2000,
          seed: int = 42) -> dict:
    """
    Tabu Search Básico para Permutation Flowshop.

    Returns
    -------
    dict with keys:
        value     : best makespan found (int)
        solution  : job permutation as list of job indices
        iterations: int
        time_s    : float
        history   : list of (iteration, best_value) tuples
    """
    random.seed(seed)

    p          = instance_data['processing']   # p[job][machine]
    n_jobs     = instance_data['n_jobs']
    n_machines = instance_data['n_machines']

    # --- Initial solution via NEH ---
    current  = _neh(p, n_jobs, n_machines)
    cur_ms   = _makespan(current, p, n_jobs, n_machines)

    best    = current[:]
    best_ms = cur_ms

    tabu_list = deque(maxlen=tabu_size)
    history   = [(0, best_ms)]

    t0 = time.perf_counter()

    for it in range(1, max_iter + 1):
        best_delta = float('inf')
        best_move  = None  # (i, j, canonical_move)

        # --- Adjacent-swap neighborhood: swap positions i and i+1 ---
        # O(n) evaluations per iteration for scalability with large instances.
        for i in range(n_jobs - 1):
            j = i + 1
            current[i], current[j] = current[j], current[i]
            new_ms = _makespan(current, p, n_jobs, n_machines)
            current[i], current[j] = current[j], current[i]  # undo

            delta = new_ms - cur_ms
            move  = (min(current[i], current[j]),
                     max(current[i], current[j]))  # canonical job pair

            is_tabu  = move in tabu_list
            new_cost = cur_ms + delta

            if is_tabu and new_cost >= best_ms:
                continue

            if delta < best_delta:
                best_delta = delta
                best_move  = (i, j, move)

        if best_move is None:
            # Fallback: random adjacent swap
            i = random.randint(0, n_jobs - 2)
            j = i + 1
            current[i], current[j] = current[j], current[i]
            best_delta = _makespan(current, p, n_jobs, n_machines) - cur_ms
            move = (min(current[i], current[j]), max(current[i], current[j]))
            current[i], current[j] = current[j], current[i]  # undo
            best_move = (i, j, move)

        i, j, move = best_move

        # Apply move
        current[i], current[j] = current[j], current[i]
        cur_ms += best_delta
        tabu_list.append(move)

        if cur_ms < best_ms:
            best    = current[:]
            best_ms = cur_ms

        history.append((it, best_ms))

    elapsed = time.perf_counter() - t0

    return {
        'value':      best_ms,
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
    fsp_files = instances.get('flowshop', [])

    if not fsp_files:
        print("No Flowshop instances found.")
        sys.exit(1)

    print(f"{'Instance':<12} {'BKS':>8} {'TS-Básico':>10} {'GAP%':>8} {'Time(s)':>8}")
    print('-' * 52)
    for fp in fsp_files:
        name = os.path.splitext(os.path.basename(fp))[0]
        data = load_instance(fp)
        res  = solve(data)
        bks  = data.get('bks', res['value'])
        gap  = (res['value'] - bks) / bks * 100 if bks > 0 else 0.0
        print(f"{name:<12} {bks:>8} {res['value']:>10} {gap:>7.2f}% {res['time_s']:>8.4f}")
