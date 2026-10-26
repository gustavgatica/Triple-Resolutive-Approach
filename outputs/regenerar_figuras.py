"""
regenerar_figuras.py — Regenera las 5 figuras de convergencia del paper.

Uso:
  python outputs/regenerar_figuras.py

Las figuras se guardan en paper/figuras/convergencia_{prob}.pdf.
"""

from __future__ import annotations

import os
import sys
import json
import glob
import numpy as np

import matplotlib.pyplot as plt

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

OUTPUT_DIR = os.path.join(_ROOT, 'output')
FIGURES_DIR = os.path.join(_ROOT, 'paper', 'figuras')

os.makedirs(FIGURES_DIR, exist_ok=True)

plt.rcParams.update({
    'figure.dpi': 150,
    'font.size': 10,
    'axes.spines.top': False,
    'axes.spines.right': False,
})

ALGOS = ['ts_basico', 'ts_intermedio', 'ts_avanzado']
ALGO_LABELS = {
    'ts_basico':     'TS-Básico',
    'ts_intermedio': 'TS-Intermedio',
    'ts_avanzado':   'TS-Avanzado',
}
COLORS = {
    'ts_basico':     '#4c72b0',
    'ts_intermedio': '#dd8452',
    'ts_avanzado':   '#55a868',
}
LINESTYLES = {
    'ts_basico':     'solid',
    'ts_intermedio': 'dashed',
    'ts_avanzado':   'dotted',
}

CONFIGS = [
    {
        'prob':      'knapsack',
        'inst':      'knapPI_11',
        'ylabel':    'Valor objetivo',
        'title':     'Convergencia — Knapsack 0/1, instancia knapPI\\_11',
        'max_iters': 200,
        'maximize':  True,
    },
    {
        'prob':   'tsp',
        'inst':   'kroA100',
        'ylabel': 'Longitud del tour',
        'title':  'Convergencia — TSP, instancia kroA100',
    },
    {
        'prob':   'vrp',
        'inst':   'vrpnc1',
        'ylabel': 'Distancia total',
        'title':  'Convergencia — CVRP, instancia vrpnc1',
    },
    {
        'prob':   'flowshop',
        'inst':   'ta041',
        'ylabel': 'Makespan (Cmax)',
        'title':  'Convergencia — Flowshop, instancia ta041',
    },
    {
        'prob':   'jobshop',
        'inst':   'la21',
        'ylabel': 'Makespan (Cmax)',
        'title':  'Convergencia — Job Shop, instancia la21',
    },
]


def _load_history(prob: str, inst: str, algo: str) -> list[tuple[int, float]]:
    """Carga el historial de convergencia del resultado mas reciente."""
    pattern = os.path.join(OUTPUT_DIR, prob, f'{inst}_{algo}_*')
    folders = sorted(glob.glob(pattern))
    if not folders:
        return []
    result_path = os.path.join(folders[-1], 'resultado.json')
    try:
        with open(result_path, encoding='utf-8') as f:
            res = json.load(f)
        return res.get('history', [])
    except Exception:
        return []


def _load_gap(prob: str, inst: str, algo: str) -> float | None:
    """Carga el GAP (%) del resultado mas reciente."""
    pattern = os.path.join(OUTPUT_DIR, prob, f'{inst}_{algo}_*')
    folders = sorted(glob.glob(pattern))
    if not folders:
        return None
    result_path = os.path.join(folders[-1], 'resultado.json')
    try:
        with open(result_path, encoding='utf-8') as f:
            res = json.load(f)
        return res.get('gap_pct')
    except Exception:
        return None


def generate_figure(cfg: dict) -> None:
    prob = cfg['prob']
    inst = cfg['inst']
    ylabel = cfg['ylabel']
    title = cfg['title']
    max_iters = cfg.get('max_iters')

    # Flowshop: los 3 niveles convergen identicamente en cada instancia.
    # Se muestra grafico de barras con GAP medio (5 semillas) por instancia.
    if prob == 'flowshop':
        from src.reporter import _load_results, _aggregate_results
        records = _load_results()
        best = _aggregate_results(records)
        instances = ['ta001', 'ta011', 'ta021', 'ta031', 'ta041']
        x = np.arange(len(instances))
        width = 0.25
        fig, ax = plt.subplots(figsize=(7, 3.5))
        for i, algo in enumerate(ALGOS):
            gaps = [best[('flowshop', inst_i, algo)]['gap_mean']
                    if ('flowshop', inst_i, algo) in best else 0.0
                    for inst_i in instances]
            ax.bar(x + (i - 1) * width, gaps, width,
                   label=ALGO_LABELS[algo],
                   color=COLORS[algo], alpha=0.85)
        ax.axhline(0, color='black', linewidth=0.8, linestyle='--')
        ax.set_xticks(x)
        ax.set_xticklabels(instances, fontsize=9)
        ax.set_xlabel('Instancia')
        ax.set_ylabel('GAP (%)')
        ax.set_title('GAP (%) por instancia — Flowshop', fontsize=11)
        ax.legend(fontsize=9)
        plt.tight_layout()
        out_path = os.path.join(FIGURES_DIR, f'convergencia_{prob}.pdf')
        plt.savefig(out_path, bbox_inches='tight')
        plt.close(fig)
        print(f'  OK {out_path}')
        return

    fig, ax = plt.subplots(figsize=(7, 3.5))

    for algo in ALGOS:
        hist = _load_history(prob, inst, algo)
        if not hist:
            print(f"  [SKIP] {prob}/{inst}/{algo}: sin historia")
            continue
        iters = [h[0] for h in hist]
        vals = [h[1] for h in hist]
        if max_iters:
            pairs = [(i, v) for i, v in zip(iters, vals) if i <= max_iters]
            if pairs:
                iters, vals = zip(*pairs)
        ax.plot(iters, vals, label=ALGO_LABELS[algo],
                color=COLORS[algo], linewidth=1.6,
                linestyle=LINESTYLES[algo])

    ax.set_xlabel('Iteracion')
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=11)
    ax.legend(fontsize=9)

    plt.tight_layout()
    out_path = os.path.join(FIGURES_DIR, f'convergencia_{prob}.pdf')
    plt.savefig(out_path, bbox_inches='tight')
    plt.close(fig)
    print(f'  OK {out_path}')


def main() -> None:
    print(f'\nRegenerando {len(CONFIGS)} figuras...\n')
    for cfg in CONFIGS:
        generate_figure(cfg)
    print('\nFiguras actualizadas en paper/figuras/')


if __name__ == '__main__':
    main()
