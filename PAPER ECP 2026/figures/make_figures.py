"""
make_figures.py — Genera la figura de convergencia del proceeding paper (ECP 2026).

Uso (desde la raíz del repositorio):
  python "PAPER ECP 2026/figures/make_figures.py"

Lee los resultado.json de output/ (semilla 42, corrida más reciente por
combinación, igual que src/reporter.py) y guarda figures/convergence.pdf con
las etiquetas en inglés.
"""

from __future__ import annotations

import os
import json
import glob

import matplotlib.pyplot as plt

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))

OUTPUT_DIR = os.path.join(_ROOT, 'output')
SEED = 42

plt.rcParams.update({
    'figure.dpi': 150,
    'font.size': 8,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.edgecolor': '#898781',
    'axes.linewidth': 0.6,
    'xtick.color': '#52514e',
    'ytick.color': '#52514e',
    'pdf.fonttype': 42,
})

ALGOS = ['ts_basico', 'ts_intermedio', 'ts_avanzado']
ALGO_LABELS = {
    'ts_basico':     'TS-Basic',
    'ts_intermedio': 'TS-Intermediate',
    'ts_avanzado':   'TS-Advanced',
}
# Paleta validada para daltonismo; el estilo de línea repite la identidad
# para la impresión en escala de grises.
COLORS = {
    'ts_basico':     '#2a78d6',
    'ts_intermedio': '#eb6834',
    'ts_avanzado':   '#1baf7a',
}
LINESTYLES = {
    'ts_basico':     'solid',
    'ts_intermedio': 'dashed',
    'ts_avanzado':   'dotted',
}

PANELS = [
    {'prob': 'knapsack', 'inst': 'knapPI_11', 'title': '(a) Knapsack, knapPI_11',
     'maximize': True, 'max_iters': 200},
    {'prob': 'tsp',      'inst': 'kroA100',   'title': '(b) TSP, kroA100',
     'ymax': 4.0},
    {'prob': 'vrp',      'inst': 'vrpnc1',    'title': '(c) CVRP, vrpnc1'},
    {'prob': 'jobshop',  'inst': 'la21',      'title': '(d) Job shop, la21'},
]


def _load_runs() -> dict:
    """Corrida más reciente por (problema, instancia, algoritmo) con SEED."""
    runs: dict[tuple, dict] = {}
    for path in glob.glob(os.path.join(OUTPUT_DIR, '*', '*', 'resultado.json')):
        with open(path, encoding='utf-8') as f:
            rec = json.load(f)
        if rec.get('seed', 42) != SEED:
            continue
        rec['output_dir'] = os.path.dirname(path)
        key = (rec['problema'], rec['instancia'], rec['algoritmo'])
        if key not in runs or rec['output_dir'] > runs[key]['output_dir']:
            runs[key] = rec
    return runs


def _gap_history(rec: dict, maximize: bool) -> tuple[list, list]:
    bks = rec['bks']
    iters = [h[0] for h in rec['history']]
    if maximize:
        gaps = [(bks - h[1]) / bks * 100 for h in rec['history']]
    else:
        gaps = [(h[1] - bks) / bks * 100 for h in rec['history']]
    return iters, gaps


def main() -> None:
    runs = _load_runs()
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 4.1))

    for ax, cfg in zip(axes.flat, PANELS):
        for algo in ALGOS:
            rec = runs.get((cfg['prob'], cfg['inst'], algo))
            if rec is None:
                print(f"  [SKIP] {cfg['prob']}/{cfg['inst']}/{algo}: sin resultado")
                continue
            iters, gaps = _gap_history(rec, cfg.get('maximize', False))
            if cfg.get('max_iters'):
                keep = [k for k, i in enumerate(iters) if i <= cfg['max_iters']]
                iters = [iters[k] for k in keep]
                gaps = [gaps[k] for k in keep]
            ax.plot(iters, gaps, label=ALGO_LABELS[algo], color=COLORS[algo],
                    linewidth=1.6, linestyle=LINESTYLES[algo])
            first_best = next(i for i, g in zip(iters, gaps) if g == gaps[-1])
            print(f"  {cfg['inst']:10s} {algo:14s} gap inicial={gaps[0]:6.2f} "
                  f"final={gaps[-1]:6.2f} (desde it {first_best}, "
                  f"{iters[-1]} it mostradas)")
        if cfg.get('ymax'):
            ax.set_ylim(top=cfg['ymax'])
        ax.set_ylim(bottom=0)
        ax.set_title(cfg['title'], fontsize=8.5, loc='left')
        ax.grid(axis='y', color='#e1e0d9', linewidth=0.5)
        ax.set_axisbelow(True)

    for ax in axes[-1]:
        ax.set_xlabel('Iteration')
    for ax in axes[:, 0]:
        ax.set_ylabel('Gap to BKS (%)')

    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', ncol=3, frameon=False,
               bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.94))

    out_path = os.path.join(_HERE, 'convergence.pdf')
    fig.savefig(out_path, bbox_inches='tight')
    plt.close(fig)
    print(f'  OK {out_path}')


if __name__ == '__main__':
    main()
