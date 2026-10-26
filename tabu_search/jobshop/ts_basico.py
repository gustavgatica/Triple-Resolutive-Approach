"""
TS-Básico para Job Shop Scheduling
====================================
Objetivo : minimizar makespan (Cmax)
Representación: lista de prioridades (permutation-based decoding via GT algorithm)
Vecindario : intercambio de dos operaciones adyacentes en la secuencia de prioridades
Lista tabú : fija, tamaño 10, almacena el par (op_a, op_b) intercambiados
Criterio de parada: max_iter iteraciones

Nota: se usa el algoritmo de Giffler-Thompson (GT) para decodificar la secuencia
de prioridades en un schedule factible y calcular el makespan.
"""

import sys
import os
import time
import random
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from loader import load_instance, list_all_instances


# ---------------------------------------------------------------------------
# Giffler-Thompson (GT) scheduler
# ---------------------------------------------------------------------------

def _gt_schedule(priority_list, machines_seq, times_seq, n_jobs, n_machines):
    """
    Decode a priority list into a schedule using Giffler-Thompson algorithm.

    priority_list: list of (job, op_idx) in priority order
    machines_seq[j][k]: machine for job j, operation k
    times_seq[j][k]  : processing time for job j, operation k

    Returns makespan.
    """
    # job_next_op[j] = index of next operation to schedule for job j
    job_next_op   = [0] * n_jobs
    machine_avail = [0] * n_machines   # earliest time machine becomes free
    job_avail     = [0] * n_jobs       # earliest time job becomes free

    schedule_order = list(priority_list)  # list of job indices in order
    remaining = list(schedule_order)

    # We schedule operations one by one following GT
    completion = {}  # (job, op) -> completion time

    for _ in range(n_jobs * n_machines):
        if not remaining:
            break

        # Find schedulable operations: those whose previous op is done
        schedulable = []
        for j in remaining:
            op = job_next_op[j]
            if op < n_machines:
                schedulable.append((j, op))

        if not schedulable:
            break

        # Among schedulable ops, find earliest completion on their required machine
        earliest_end = float('inf')
        for j, op in schedulable:
            m   = machines_seq[j][op]
            t   = times_seq[j][op]
            end = max(machine_avail[m], job_avail[j]) + t
            if end < earliest_end:
                earliest_end = end

        # Conflict set: schedulable ops on machines with machine_avail < earliest_end
        conflict = []
        for j, op in schedulable:
            m   = machines_seq[j][op]
            t   = times_seq[j][op]
            start = max(machine_avail[m], job_avail[j])
            if start < earliest_end:
                conflict.append((j, op))

        # Choose from conflict set by priority order
        chosen_j, chosen_op = None, None
        for j in schedule_order:
            for (cj, cop) in conflict:
                if cj == j:
                    chosen_j, chosen_op = cj, cop
                    break
            if chosen_j is not None:
                break

        if chosen_j is None:
            chosen_j, chosen_op = conflict[0]

        # Schedule chosen operation
        m     = machines_seq[chosen_j][chosen_op]
        t     = times_seq[chosen_j][chosen_op]
        start = max(machine_avail[m], job_avail[chosen_j])
        end   = start + t

        machine_avail[m]      = end
        job_avail[chosen_j]   = end
        job_next_op[chosen_j] += 1
        completion[(chosen_j, chosen_op)] = end

        # Advance in priority list for this job (remove first occurrence)
        for idx, jj in enumerate(schedule_order):
            if jj == chosen_j:
                schedule_order.pop(idx)
                break
        # Also remove from remaining if all ops done
        if job_next_op[chosen_j] >= n_machines:
            remaining = [j for j in remaining if j != chosen_j]

    return max(machine_avail)


# ---------------------------------------------------------------------------
# Main solver
# ---------------------------------------------------------------------------

def solve(instance_data: dict,
          tabu_size: int = 10,
          max_iter: int = 2500,
          seed: int = 42) -> dict:
    """
    Tabu Search Básico para Job Shop Scheduling.

    Returns
    -------
    dict with keys:
        value     : best makespan found (int)
        solution  : job priority list (list of job indices)
        iterations: int
        time_s    : float
        history   : list of (iteration, best_value) tuples
    """
    random.seed(seed)

    machines_seq = instance_data['machines']   # machines_seq[j][k]
    times_seq    = instance_data['times']       # times_seq[j][k]
    n_jobs       = instance_data['n_jobs']
    n_machines   = instance_data['n_machines']

    def makespan(perm):
        return _gt_schedule(perm, machines_seq, times_seq, n_jobs, n_machines)

    # --- Initial solution: jobs ordered by total processing time (desc) ---
    current = sorted(range(n_jobs),
                     key=lambda j: sum(times_seq[j]),
                     reverse=True)
    cur_ms  = makespan(current)

    best    = current[:]
    best_ms = cur_ms

    tabu_list = deque(maxlen=tabu_size)
    history   = [(0, best_ms)]

    t0 = time.perf_counter()

    for it in range(1, max_iter + 1):
        best_delta = float('inf')
        best_move  = None

        # --- Adjacent-swap neighborhood ---
        for i in range(n_jobs - 1):
            j = i + 1
            current[i], current[j] = current[j], current[i]
            new_ms = makespan(current)
            current[i], current[j] = current[j], current[i]  # undo

            delta = new_ms - cur_ms
            move  = (min(current[i], current[j]),
                     max(current[i], current[j]))

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
            best_delta = makespan(current) - cur_ms
            move = (min(current[i], current[j]), max(current[i], current[j]))
            current[i], current[j] = current[j], current[i]
            best_move = (i, j, move)

        i, j, move = best_move
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
    jss_files = instances.get('jobshop', [])

    if not jss_files:
        print("No Job Shop instances found.")
        sys.exit(1)

    print(f"{'Instance':<12} {'BKS':>8} {'TS-Básico':>10} {'GAP%':>8} {'Time(s)':>8}")
    print('-' * 52)
    for fp in jss_files:
        name = os.path.splitext(os.path.basename(fp))[0]
        data = load_instance(fp)
        res  = solve(data)
        bks  = data.get('bks', res['value'])
        gap  = (res['value'] - bks) / bks * 100 if bks > 0 else 0.0
        print(f"{name:<12} {bks:>8} {res['value']:>10} {gap:>7.2f}% {res['time_s']:>8.4f}")
