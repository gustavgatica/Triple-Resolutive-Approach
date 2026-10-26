"""
TS-Avanzado para Job Shop Scheduling
======================================
Mejoras sobre TS-Intermedio:
  1. MEMORIA DE FRECUENCIA: freq[job_a][job_b] = nº de veces que se swapeó
     el par (job_a, job_b) en la secuencia de prioridades.
  2. PENALIZACIÓN ADAPTATIVA: favorece pares poco explorados.
  3. λ ADAPTATIVO: balance intensificación/diversificación.
  4. REINICIO con perturbación basada en frecuencia: fuerza sacar del
     orden los jobs con mayor frecuencia de swap.
  5. Más iteraciones (1500; CLI usa 700).
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
            m = machines_seq[j][op]; t = times_seq[j][op]
            end = max(machine_avail[m], job_avail[j]) + t
            if end < earliest_end:
                earliest_end = end
        conflict = [(j, op) for j, op in schedulable
                    if max(machine_avail[machines_seq[j][op]], job_avail[j]) < earliest_end]
        chosen_j = chosen_op = None
        for j in schedule_order:
            for cj, cop in conflict:
                if cj == j:
                    chosen_j, chosen_op = cj, cop; break
            if chosen_j is not None:
                break
        if chosen_j is None:
            chosen_j, chosen_op = conflict[0]
        m = machines_seq[chosen_j][chosen_op]; t = times_seq[chosen_j][chosen_op]
        start = max(machine_avail[m], job_avail[chosen_j])
        end   = start + t
        machine_avail[m] = end; job_avail[chosen_j] = end
        job_next_op[chosen_j] += 1
        for idx, jj in enumerate(schedule_order):
            if jj == chosen_j:
                schedule_order.pop(idx); break
        if job_next_op[chosen_j] >= n_machines:
            remaining = [j for j in remaining if j != chosen_j]
    return max(machine_avail)


def _freq_based_perturb(perm, freq, n_swaps, rng):
    """Perturbación que prioriza sacar del orden los jobs con mayor frecuencia."""
    p = perm[:]
    n = len(p)
    # Build per-job total frequency
    job_freq = [sum(freq[j]) for j in range(n)]
    total    = sum(job_freq) or 1
    weights  = [f / total for f in job_freq]
    for _ in range(n_swaps):
        # Pick job proportional to frequency (diversify high-freq jobs)
        r = rng.random()
        cumw = 0.0
        chosen = 0
        for idx, w in enumerate(weights):
            cumw += w
            if r <= cumw:
                chosen = idx
                break
        pos_i = p.index(chosen)
        pos_j = rng.randint(0, n - 1)
        p[pos_i], p[pos_j] = p[pos_j], p[pos_i]
    return p


def solve(instance_data: dict,
          tabu_min: int = 5,
          tabu_max: int = 15,
          change_every: int = 100,
          lambda_init: float = 0.0,
          lambda_max: float = 3.0,
          lambda_step_up: float = 0.15,
          lambda_step_down: float = 0.05,
          no_improve_limit: int = 250,
          max_iter: int = 1500,
          seed: int = 42) -> dict:
    """
    Tabu Search Avanzado para Job Shop.

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

    # freq[job_a][job_b] = times pair (job_a, job_b) was swapped
    freq = [[0] * n_jobs for _ in range(n_jobs)]

    lam        = lambda_init
    no_improve = 0
    history    = [(0, best_ms)]
    t0 = time.perf_counter()

    for it in range(1, max_iter + 1):

        # Dynamic tabu size
        if it % change_every == 0:
            new_size  = rng.randint(tabu_min, tabu_max)
            tabu_list = deque(list(tabu_list)[-new_size:], maxlen=new_size)

        # Frequency-based restart if stuck
        if no_improve >= no_improve_limit:
            current    = _freq_based_perturb(best[:], freq, max(2, n_jobs // 4), rng)
            cur_ms     = makespan(current)
            tabu_list.clear()
            no_improve = 0

        best_pen   = float('inf')
        best_delta = float('inf')
        best_move  = None

        for i in range(n_jobs - 1):
            j = i + 1
            current[i], current[j] = current[j], current[i]
            new_ms   = makespan(current)
            current[i], current[j] = current[j], current[i]

            delta    = new_ms - cur_ms
            job_a, job_b = current[i], current[j]
            move     = (min(job_a, job_b), max(job_a, job_b))
            new_cost = cur_ms + delta
            is_tabu  = move in tabu_list

            if is_tabu and new_cost >= best_ms:
                continue

            # Penalized: penalize frequently-swapped pairs
            pen_pair  = freq[job_a][job_b] + freq[job_b][job_a]
            pen_delta = delta + lam * pen_pair / max(it, 1)

            if pen_delta < best_pen:
                best_pen   = pen_delta
                best_delta = delta
                best_move  = (i, j, move, job_a, job_b)

        if best_move is None:
            i = rng.randint(0, n_jobs - 2)
            j = i + 1
            current[i], current[j] = current[j], current[i]
            best_delta = makespan(current) - cur_ms
            job_a, job_b = current[i], current[j]
            move = (min(job_a, job_b), max(job_a, job_b))
            current[i], current[j] = current[j], current[i]
            best_move = (i, j, move, job_a, job_b)

        i, j, move, job_a, job_b = best_move
        current[i], current[j] = current[j], current[i]
        cur_ms += best_delta

        freq[job_a][job_b] += 1
        freq[job_b][job_a] += 1
        tabu_list.append(move)

        if cur_ms < best_ms:
            best       = current[:]
            best_ms    = cur_ms
            no_improve = 0
            lam        = max(lambda_init, lam - lambda_step_down)
        else:
            no_improve += 1
            if no_improve % 50 == 0:
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
    jss_files = instances.get('jobshop', [])
    print(f"{'Instance':<12} {'BKS':>8} {'TS-Avanz':>10} {'GAP%':>8} {'Time(s)':>8}")
    print('-' * 52)
    for fp in jss_files:
        name = os.path.splitext(os.path.basename(fp))[0]
        data = load_instance(fp)
        res  = solve(data, max_iter=700)
        bks  = data.get('bks', res['value'])
        gap  = (res['value'] - bks) / bks * 100 if bks > 0 else 0.0
        print(f"{name:<12} {bks:>8} {res['value']:>10} {gap:>7.2f}% {res['time_s']:>8.4f}")
