"""
TS-Intermedio para Job Shop Scheduling
=======================================
Mejoras sobre TS-Básico:
  1. Lista tabú DINÁMICA [5, 15].
  2. Criterio de ASPIRACIÓN explícito con contador de activaciones.
  3. Reinicio suave: si no hay mejora en `no_improve_limit` iteraciones,
     se perturba la mejor solución conocida.
  4. Mayor número de iteraciones (1000 en experimentos; CLI usa 500).

Nota: el vecindario sigue siendo swap adyacente O(n). El swap no-adyacente
completo O(n²) se reserva para TS-Avanzado.
"""

import sys
import os
import time
import random
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from loader import load_instance, list_all_instances


def _gt_schedule(priority_list, machines_seq, times_seq, n_jobs, n_machines):
    job_next_op   = [0] * n_jobs
    machine_avail = [0] * n_machines
    job_avail     = [0] * n_jobs
    schedule_order = list(priority_list)
    remaining = list(schedule_order)

    for _ in range(n_jobs * n_machines):
        if not remaining:
            break
        schedulable = [(j, job_next_op[j]) for j in remaining
                       if job_next_op[j] < n_machines]
        if not schedulable:
            break
        earliest_end = float('inf')
        for j, op in schedulable:
            m   = machines_seq[j][op]
            t   = times_seq[j][op]
            end = max(machine_avail[m], job_avail[j]) + t
            if end < earliest_end:
                earliest_end = end
        conflict = [(j, op) for j, op in schedulable
                    if max(machine_avail[machines_seq[j][op]], job_avail[j]) < earliest_end]
        chosen_j, chosen_op = None, None
        for j in schedule_order:
            for cj, cop in conflict:
                if cj == j:
                    chosen_j, chosen_op = cj, cop
                    break
            if chosen_j is not None:
                break
        if chosen_j is None:
            chosen_j, chosen_op = conflict[0]
        m     = machines_seq[chosen_j][chosen_op]
        t     = times_seq[chosen_j][chosen_op]
        start = max(machine_avail[m], job_avail[chosen_j])
        end   = start + t
        machine_avail[m]       = end
        job_avail[chosen_j]    = end
        job_next_op[chosen_j] += 1
        for idx, jj in enumerate(schedule_order):
            if jj == chosen_j:
                schedule_order.pop(idx)
                break
        if job_next_op[chosen_j] >= n_machines:
            remaining = [j for j in remaining if j != chosen_j]
    return max(machine_avail)


def _perturb(perm, n_swaps=3, rng=random):
    p = perm[:]
    n = len(p)
    for _ in range(n_swaps):
        i = rng.randint(0, n - 2)
        j = rng.randint(i + 1, n - 1)
        p[i], p[j] = p[j], p[i]
    return p


def solve(instance_data: dict,
          tabu_min: int = 5,
          tabu_max: int = 15,
          change_every: int = 100,
          no_improve_limit: int = 200,
          max_iter: int = 1000,
          seed: int = 42) -> dict:
    """
    Tabu Search Intermedio para Job Shop.

    Returns dict: value, solution, iterations, time_s, history
    """
    rng = random.Random(seed)

    machines_seq = instance_data['machines']
    times_seq    = instance_data['times']
    n_jobs       = instance_data['n_jobs']
    n_machines   = instance_data['n_machines']

    def makespan(perm):
        return _gt_schedule(perm, machines_seq, times_seq, n_jobs, n_machines)

    current = sorted(range(n_jobs), key=lambda j: sum(times_seq[j]), reverse=True)
    cur_ms  = makespan(current)

    best    = current[:]
    best_ms = cur_ms

    tabu_size = rng.randint(tabu_min, tabu_max)
    tabu_list = deque(maxlen=tabu_size)

    no_improve       = 0
    aspiration_count = 0
    history = [(0, best_ms)]
    t0 = time.perf_counter()

    for it in range(1, max_iter + 1):

        # Dynamic tabu size
        if it % change_every == 0:
            new_size  = rng.randint(tabu_min, tabu_max)
            tabu_list = deque(list(tabu_list)[-new_size:], maxlen=new_size)

        # Soft restart if stuck
        if no_improve >= no_improve_limit:
            current    = _perturb(best[:], n_swaps=max(2, n_jobs // 5), rng=rng)
            cur_ms     = makespan(current)
            tabu_list.clear()
            no_improve = 0

        best_delta = float('inf')
        best_move  = None

        # --- Adjacent-swap neighborhood ---
        for i in range(n_jobs - 1):
            j = i + 1
            current[i], current[j] = current[j], current[i]
            new_ms   = makespan(current)
            current[i], current[j] = current[j], current[i]

            delta    = new_ms - cur_ms
            move     = (min(current[i], current[j]), max(current[i], current[j]))
            new_cost = cur_ms + delta
            is_tabu  = move in tabu_list

            if is_tabu and new_cost >= best_ms:
                continue
            if is_tabu and new_cost < best_ms:
                aspiration_count += 1

            if delta < best_delta:
                best_delta = delta
                best_move  = (i, j, move)

        if best_move is None:
            i = rng.randint(0, n_jobs - 2)
            j = i + 1
            current[i], current[j] = current[j], current[i]
            best_delta = makespan(current) - cur_ms
            move = (min(current[i], current[j]), max(current[i], current[j]))
            current[i], current[j] = current[j], current[i]
            best_move = (i, j, move)

        i, j, move = best_move
        current[i], current[j] = current[j], current[i]
        cur_ms += best_delta
        tabu_list.append(move)

        if cur_ms < best_ms:
            best       = current[:]
            best_ms    = cur_ms
            no_improve = 0
        else:
            no_improve += 1

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
    jss_files = instances.get('jobshop', [])
    print(f"{'Instance':<12} {'BKS':>8} {'TS-Inter':>10} {'GAP%':>8} {'Time(s)':>8}")
    print('-' * 52)
    for fp in jss_files:
        name = os.path.splitext(os.path.basename(fp))[0]
        data = load_instance(fp)
        res  = solve(data, max_iter=500)
        bks  = data.get('bks', res['value'])
        gap  = (res['value'] - bks) / bks * 100 if bks > 0 else 0.0
        print(f"{name:<12} {bks:>8} {res['value']:>10} {gap:>7.2f}% {res['time_s']:>8.4f}")
