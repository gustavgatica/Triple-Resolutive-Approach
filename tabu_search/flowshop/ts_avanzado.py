"""
TS-Avanzado para Permutation Flowshop
=======================================
Mejoras sobre TS-Intermedio:
  1. MEMORIA DE FRECUENCIA: freq[job][pos] = nº de veces que el job estuvo
     en la posición pos de la permutación.
  2. PENALIZACIÓN ADAPTATIVA: al evaluar swaps, penaliza pares (job,pos)
     muy frecuentes, forzando exploración de permutaciones nuevas.
  3. λ ADAPTATIVO que equilibra intensificación y diversificación.
  4. Más iteraciones (5000; CLI usa 2000).
"""

import sys
import os
import time
import random
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from loader import load_instance, list_all_instances


def _makespan(perm, p, n_jobs, n_machines):
    C = [[0] * n_machines for _ in range(n_jobs)]
    for i in range(n_jobs):
        for j in range(n_machines):
            prev_job  = C[i - 1][j] if i > 0 else 0
            prev_mach = C[i][j - 1] if j > 0 else 0
            C[i][j]   = max(prev_job, prev_mach) + p[perm[i]][j]
    return C[n_jobs - 1][n_machines - 1]


def _neh(p, n_jobs, n_machines):
    totals = sorted(range(n_jobs), key=lambda j: sum(p[j]), reverse=True)
    perm   = [totals[0]]
    for k in range(1, n_jobs):
        job     = totals[k]; best_ms = float('inf'); best_pos = 0
        for pos in range(len(perm) + 1):
            trial = perm[:pos] + [job] + perm[pos:]
            ms = _makespan(trial, p, k + 1, n_machines)
            if ms < best_ms:
                best_ms = ms; best_pos = pos
        perm.insert(best_pos, job)
    return perm


def _perturb(perm, n_swaps, rng):
    p = perm[:]
    n = len(p)
    for _ in range(n_swaps):
        i = rng.randint(0, n - 2)
        j = rng.randint(i + 1, n - 1)
        p[i], p[j] = p[j], p[i]
    return p


def solve(instance_data: dict,
          tabu_min: int = 5,
          tabu_max: int = 20,
          change_every: int = 200,
          lambda_init: float = 0.0,
          lambda_max: float = 3.0,
          lambda_step_up: float = 0.1,
          lambda_step_down: float = 0.05,
          no_improve_limit: int = 500,
          max_iter: int = 5000,
          seed: int = 42) -> dict:
    """
    Tabu Search Avanzado para Permutation Flowshop.

    Returns dict: value, solution, iterations, time_s, history
    """
    rng = random.Random(seed)

    p          = instance_data['processing']
    n_jobs     = instance_data['n_jobs']
    n_machines = instance_data['n_machines']

    current = _neh(p, n_jobs, n_machines)
    cur_ms  = _makespan(current, p, n_jobs, n_machines)

    best    = current[:]
    best_ms = cur_ms

    tabu_size = rng.randint(tabu_min, tabu_max)
    tabu_list = deque(maxlen=tabu_size)

    # freq[job][pos] = times job was at position pos
    freq = [[0] * n_jobs for _ in range(n_jobs)]
    for pos, job in enumerate(current):
        freq[job][pos] += 1

    lam        = lambda_init
    no_improve = 0
    history    = [(0, best_ms)]
    t0 = time.perf_counter()

    for it in range(1, max_iter + 1):

        # Dynamic tabu size
        if it % change_every == 0:
            new_size  = rng.randint(tabu_min, tabu_max)
            tabu_list = deque(list(tabu_list)[-new_size:], maxlen=new_size)

        # Soft restart if stuck
        if no_improve >= no_improve_limit:
            current    = _perturb(best[:], n_swaps=max(3, n_jobs // 8), rng=rng)
            cur_ms     = _makespan(current, p, n_jobs, n_machines)
            tabu_list.clear()
            no_improve = 0

        best_pen   = float('inf')
        best_delta = float('inf')
        best_move  = None

        for i in range(n_jobs - 1):
            j = i + 1
            current[i], current[j] = current[j], current[i]
            new_ms   = _makespan(current, p, n_jobs, n_machines)
            current[i], current[j] = current[j], current[i]

            delta    = new_ms - cur_ms
            move     = (min(current[i], current[j]), max(current[i], current[j]))
            new_cost = cur_ms + delta
            is_tabu  = move in tabu_list

            if is_tabu and new_cost >= best_ms:
                continue

            # Penalized: add freq penalty for swapping current[i] away from pos i
            job_i, job_j = current[i], current[j]
            pen = lam * (freq[job_i][i] + freq[job_j][j]) / max(it, 1)
            pen_delta = delta + pen

            if pen_delta < best_pen:
                best_pen   = pen_delta
                best_delta = delta
                best_move  = (i, j, move)

        if best_move is None:
            i = rng.randint(0, n_jobs - 2)
            j = i + 1
            current[i], current[j] = current[j], current[i]
            best_delta = _makespan(current, p, n_jobs, n_machines) - cur_ms
            move = (min(current[i], current[j]), max(current[i], current[j]))
            current[i], current[j] = current[j], current[i]
            best_move = (i, j, move)

        i, j, move = best_move
        current[i], current[j] = current[j], current[i]
        cur_ms += best_delta

        # Update frequency
        for pos, job in enumerate(current):
            freq[job][pos] += 1

        tabu_list.append(move)

        if cur_ms < best_ms:
            best       = current[:]
            best_ms    = cur_ms
            no_improve = 0
            lam        = max(lambda_init, lam - lambda_step_down)
        else:
            no_improve += 1
            if no_improve % 100 == 0:
                lam = min(lambda_max, lam + lambda_step_up)

        history.append((it, best_ms))

    elapsed = time.perf_counter() - t0
    return {
        'value':      best_ms,
        'solution':   best,
        'iterations': it,
        'time_s':     elapsed,
        'history':    history,
    }


if __name__ == '__main__':
    instances = list_all_instances(
        os.path.join(os.path.dirname(__file__), '..', '..', 'instances'))
    fsp_files = instances.get('flowshop', [])
    print(f"{'Instance':<12} {'BKS':>8} {'TS-Avanz':>10} {'GAP%':>8} {'Time(s)':>8}")
    print('-' * 52)
    for fp in fsp_files:
        name = os.path.splitext(os.path.basename(fp))[0]
        data = load_instance(fp)
        res  = solve(data, max_iter=2000)
        bks  = data.get('bks', res['value'])
        gap  = (res['value'] - bks) / bks * 100 if bks > 0 else 0.0
        print(f"{name:<12} {bks:>8} {res['value']:>10} {gap:>7.2f}% {res['time_s']:>8.4f}")
