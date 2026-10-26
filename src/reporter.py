"""
reporter.py — Consolida resultados de output/ en CSVs y tablas LaTeX.

Genera:
  results/tabla_{problema}.csv        ← resultados por problema
  results/tabla_consolidada.csv       ← tabla maestra (75 experimentos)
  src/tables/instance-{N}.tex         ← tablas LaTeX por instancia (estilo OPTIMA)

Uso:
  from src.reporter import generate_report
  generate_report()

  python src/reporter.py
"""

from __future__ import annotations

import sys
import os
import json
import csv
import glob
import statistics
from collections import defaultdict

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

OUTPUT_DIR  = os.path.join(_ROOT, 'output')
RESULTS_DIR = os.path.join(_ROOT, 'results')
TABLES_DIR  = os.path.join(_ROOT, 'src', 'tables')

PROBLEMS   = ['knapsack', 'tsp', 'vrp', 'flowshop', 'jobshop']
ALGORITHMS = ['ts_basico', 'ts_intermedio', 'ts_avanzado']

ALG_LABEL = {
    'ts_basico':     'TS-Básico',
    'ts_intermedio': 'TS-Intermedio',
    'ts_avanzado':   'TS-Avanzado',
}

PROB_LABEL = {
    'knapsack': 'Knapsack (0-1)',
    'tsp':      'TSP',
    'vrp':      'CVRP',
    'flowshop': 'Flowshop',
    'jobshop':  'Job Shop',
}


# ---------------------------------------------------------------------------
# Leer resultados desde output/
# ---------------------------------------------------------------------------

def _load_results() -> list[dict]:
    """Lee todos los resultado.json de output/ y devuelve lista de dicts."""
    records = []
    pattern = os.path.join(OUTPUT_DIR, '*', '*', 'resultado.json')
    for path in glob.glob(pattern):
        try:
            with open(path, encoding='utf-8') as f:
                rec = json.load(f)
            rec['output_dir'] = os.path.dirname(path)
            records.append(rec)
        except Exception:
            pass
    return records


def _latest_per_combo(records: list[dict]) -> dict:
    """
    Para cada (problema, instancia, algoritmo) conserva solo el resultado
    más reciente (mayor timestamp implícito en el nombre de carpeta).
    Usado internamente por _aggregate_results.
    """
    best: dict[tuple, dict] = {}
    for rec in records:
        key = (rec['problema'], rec['instancia'], rec['algoritmo'])
        if key not in best or rec['output_dir'] > best[key]['output_dir']:
            best[key] = rec
    return best


def _aggregate_results(records: list[dict]) -> dict:
    """
    Agrupa resultados por (problema, instancia, algoritmo, semilla),
    conservando solo la corrida más reciente por semilla.
    Luego calcula media y desviación estándar del GAP y el tiempo
    sobre todas las semillas disponibles.

    El dict devuelto tiene la misma clave (prob, inst, alg) que
    _latest_per_combo pero cada valor incluye además:
        gap_mean, gap_std, time_mean, time_std, n_seeds
    """
    # Paso 1: corrida más reciente por (prob, inst, alg, seed)
    by_seed: dict[tuple, dict] = {}
    for rec in records:
        seed = rec.get('seed', 42)
        key  = (rec['problema'], rec['instancia'], rec['algoritmo'], seed)
        if key not in by_seed or rec['output_dir'] > by_seed[key]['output_dir']:
            by_seed[key] = rec

    # Paso 2: agrupar por (prob, inst, alg) y calcular estadísticas
    groups: dict[tuple, list] = defaultdict(list)
    for (prob, inst, alg, _seed), rec in by_seed.items():
        groups[(prob, inst, alg)].append(rec)

    aggregated: dict[tuple, dict] = {}
    for key, runs in groups.items():
        gaps   = [r['gap_pct'] for r in runs]
        times  = [r['time_s']  for r in runs]
        # Para figuras/solución se usa el mejor run (menor GAP)
        best   = min(runs, key=lambda r: r['gap_pct'])

        aggregated[key] = {
            **best,
            'gap_mean':  statistics.mean(gaps),
            'gap_std':   statistics.stdev(gaps) if len(gaps) > 1 else 0.0,
            'gap_min':   min(gaps),
            'gap_max':   max(gaps),
            'time_mean': statistics.mean(times),
            'time_std':  statistics.stdev(times) if len(times) > 1 else 0.0,
            'n_seeds':   len(runs),
        }

    return aggregated


# ---------------------------------------------------------------------------
# Generar CSVs
# ---------------------------------------------------------------------------

def _write_consolidated(best: dict, out_path: str) -> None:
    """
    Escribe tabla_consolidada.csv con una fila por (problema, instancia).
    Incluye media y std de GAP y tiempo cuando hay múltiples semillas.
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fieldnames = [
        'Problema', 'Instancia', 'BKS', 'Seeds',
        'GAP_B(%)', 'GAP_B_std', 'T_B(s)', 'T_B_std',
        'GAP_I(%)', 'GAP_I_std', 'T_I(s)', 'T_I_std',
        'GAP_A(%)', 'GAP_A_std', 'T_A(s)', 'T_A_std',
    ]
    # Agrupar por (problema, instancia)
    combos: dict[tuple, dict] = {}
    for (prob, inst, alg), rec in best.items():
        k = (prob, inst)
        if k not in combos:
            combos[k] = {'prob': prob, 'inst': inst,
                         'bks': rec['bks'], 'seeds': rec['n_seeds']}
        if alg == 'ts_basico':
            combos[k].update({
                'g_b': rec['gap_mean'], 'g_b_std': rec['gap_std'],
                't_b': rec['time_mean'], 't_b_std': rec['time_std'],
            })
        elif alg == 'ts_intermedio':
            combos[k].update({
                'g_i': rec['gap_mean'], 'g_i_std': rec['gap_std'],
                't_i': rec['time_mean'], 't_i_std': rec['time_std'],
            })
        elif alg == 'ts_avanzado':
            combos[k].update({
                'g_a': rec['gap_mean'], 'g_a_std': rec['gap_std'],
                't_a': rec['time_mean'], 't_a_std': rec['time_std'],
            })

    def _fmt(val, fmt): return fmt.format(val) if val != '' else ''

    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for (prob, inst) in sorted(combos.keys()):
            c = combos[(prob, inst)]
            w.writerow({
                'Problema':   PROB_LABEL.get(prob, prob),
                'Instancia':  inst,
                'BKS':        c.get('bks', ''),
                'Seeds':      c.get('seeds', 1),
                'GAP_B(%)':   f"{c['g_b']:+.2f}"   if 'g_b'   in c else '',
                'GAP_B_std':  f"{c['g_b_std']:.2f}" if 'g_b_std' in c else '',
                'T_B(s)':     f"{c['t_b']:.2f}"    if 't_b'   in c else '',
                'T_B_std':    f"{c['t_b_std']:.2f}" if 't_b_std' in c else '',
                'GAP_I(%)':   f"{c['g_i']:+.2f}"   if 'g_i'   in c else '',
                'GAP_I_std':  f"{c['g_i_std']:.2f}" if 'g_i_std' in c else '',
                'T_I(s)':     f"{c['t_i']:.2f}"    if 't_i'   in c else '',
                'T_I_std':    f"{c['t_i_std']:.2f}" if 't_i_std' in c else '',
                'GAP_A(%)':   f"{c['g_a']:+.2f}"   if 'g_a'   in c else '',
                'GAP_A_std':  f"{c['g_a_std']:.2f}" if 'g_a_std' in c else '',
                'T_A(s)':     f"{c['t_a']:.2f}"    if 't_a'   in c else '',
                'T_A_std':    f"{c['t_a_std']:.2f}" if 't_a_std' in c else '',
            })
    print(f"  OK {out_path}")


def _write_per_problem(best: dict) -> None:
    """
    Escribe tabla_{problema}.csv para cada problema.
    Incluye media y desviación estándar si hay múltiples semillas.
    """
    os.makedirs(RESULTS_DIR, exist_ok=True)
    for prob in PROBLEMS:
        path = os.path.join(RESULTS_DIR, f'tabla_{prob}.csv')
        rows = [(inst, alg, rec)
                for (p, inst, alg), rec in best.items() if p == prob]
        if not rows:
            continue
        with open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow([
                'Instancia', 'Algoritmo', 'BKS', 'Valor',
                'GAP(%)', 'GAP_std(%)',
                'Iter', 'Tiempo(s)', 'Tiempo_std(s)', 'Seeds'
            ])
            for inst, alg, rec in sorted(rows):
                w.writerow([
                    inst,
                    ALG_LABEL.get(alg, alg),
                    rec['bks'],
                    f"{rec['value']:.4g}",
                    f"{rec['gap_mean']:+.2f}",
                    f"{rec['gap_std']:.2f}",
                    rec['iterations'],
                    f"{rec['time_mean']:.2f}",
                    f"{rec['time_std']:.2f}",
                    rec['n_seeds'],
                ])
        print(f"  OK {path}")


# ---------------------------------------------------------------------------
# Generar tablas LaTeX (estilo repositorio OPTIMA: instance-N.tex)
# ---------------------------------------------------------------------------

def _write_latex_tables(best: dict) -> None:
    """
    Genera src/tables/instance-{N}.tex, una por instancia, con los resultados
    de los 3 algoritmos. Formato tabular LaTeX listo para \\input{}.
    """
    os.makedirs(TABLES_DIR, exist_ok=True)

    # Ordenar instancias globalmente
    all_instances = sorted(set((p, i) for (p, i, _) in best.keys()))

    for idx, (prob, inst) in enumerate(all_instances):
        tex_path = os.path.join(TABLES_DIR, f'instance-{idx}.tex')
        rows = []
        for alg in ALGORITHMS:
            key = (prob, inst, alg)
            if key in best:
                rec = best[key]
                rows.append((ALG_LABEL[alg], rec['value'], rec['bks'],
                              rec['gap_pct'], rec['time_s']))

        if not rows:
            continue

        lines = [
            r'\begin{table}[h]',
            r'\centering',
            (r'\caption{Resultados para ' +
             f'{PROB_LABEL.get(prob, prob)} -- {inst}' + r'}'),
            r'\label{tab:' + f'{prob}_{inst}' + r'}',
            r'\begin{tabular}{lrrrr}',
            r'\hline',
            r'\textbf{Algoritmo} & \textbf{Valor} & \textbf{BKS} '
            r'& \textbf{GAP(\%)} & \textbf{Tiempo (s)} \\',
            r'\hline',
        ]
        for alg_label, val, bks, gap_pct, t in rows:
            lines.append(
                f'{alg_label} & {val:.4g} & {bks:.4g} '
                f'& {gap_pct:+.2f} & {t:.2f} \\\\'
            )
        lines += [
            r'\hline',
            r'\end{tabular}',
            r'\end{table}',
        ]

        with open(tex_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')

    print(f"  OK {len(all_instances)} tablas LaTeX en {TABLES_DIR}/")


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def generate_report(verbose: bool = True) -> None:
    """
    Lee output/, agrega resultados por semilla y genera CSVs y tablas LaTeX.
    Si hay una sola semilla por combo, el comportamiento es idéntico al anterior.
    Si hay múltiples semillas, calcula media ± std por (prob, inst, alg).
    """
    records = _load_results()
    if not records:
        print("No se encontraron resultados en output/. Ejecuta primero main.py --all")
        return

    # Agregar por semilla en lugar de quedarse solo con el más reciente
    best = _aggregate_results(records)

    n_seeds = max(v['n_seeds'] for v in best.values()) if best else 1
    if verbose:
        print(f"\nConsolidando {len(best)} combos de {len(records)} corridas "
              f"(hasta {n_seeds} semillas por combo)...\n")

    _write_per_problem(best)
    _write_consolidated(best, os.path.join(RESULTS_DIR, 'tabla_consolidada.csv'))
    _write_latex_tables(best)

    if verbose:
        if n_seeds > 1:
            print(f"\nReporte completo. {len(best)} combos con media±std "
                  f"calculada sobre {n_seeds} semillas.")
        else:
            print(f"\nReporte completo. {len(best)} experimentos procesados. "
                  f"(Ejecuta con --multi-seed para obtener media±std)")


if __name__ == '__main__':
    generate_report()
