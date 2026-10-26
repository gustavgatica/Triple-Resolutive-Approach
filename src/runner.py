"""
runner.py — Ejecuta un experimento (problema × instancia × algoritmo)
y guarda el resultado en output/{problema}/{instancia}_{algoritmo}_{timestamp}/

Estructura de salida (espejo del repositorio OPTIMA):
    output/
    └── tsp/
        └── berlin52_ts_basico_2026_5_29_10_30_15/
            ├── resultado.json   ← métricas + historial de convergencia
            └── solucion.txt     ← representación textual de la solución

Uso como módulo:
    from src.runner import run_experiment
    resultado = run_experiment('tsp', 'berlin52', 'ts_basico')

Uso CLI:
    python src/runner.py --problema tsp --instancia berlin52 --algoritmo ts_basico
"""

from __future__ import annotations

import sys
import os
import json
import importlib
import datetime
import argparse

# Asegura que el raíz de 'Tesis Final' esté en el path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from src.loader  import load_instance, list_all_instances
from src.metrics import summarize, MINIMIZATION

# ---------------------------------------------------------------------------
# Constantes de configuración
# ---------------------------------------------------------------------------

PROBLEMS = ['knapsack', 'tsp', 'vrp', 'flowshop', 'jobshop']
ALGORITHMS = ['ts_basico', 'ts_intermedio', 'ts_avanzado']

# Extensiones de archivo por problema
EXTENSIONS = {
    'knapsack': '.kp',
    'tsp':      '.tsp',
    'vrp':      '.vrp',
    'flowshop': '.fsp',
    'jobshop':  '.jss',
}

# Carpeta de instancias
INSTANCES_DIR = os.path.join(_ROOT, 'instances')
OUTPUT_DIR    = os.path.join(_ROOT, 'output')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_instance_file(problema: str, instancia: str) -> str:
    """Localiza el archivo de instancia dado el nombre (sin extensión)."""
    ext  = EXTENSIONS[problema]
    path = os.path.join(INSTANCES_DIR, problema, instancia + ext)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Instancia no encontrada: {path}")
    return path


def _load_solver(problema: str, algoritmo: str):
    """Importa y devuelve la función solve() del módulo correspondiente."""
    module_path = f"tabu_search.{problema}.{algoritmo}"
    try:
        mod = importlib.import_module(module_path)
    except ModuleNotFoundError as e:
        raise ImportError(f"No se encontró el módulo {module_path}: {e}")
    return mod.solve


def _make_output_dir(problema: str, instancia: str, algoritmo: str) -> str:
    """Crea y devuelve la carpeta de salida con timestamp."""
    now = datetime.datetime.now()
    # Formato: Instancia_Algoritmo_YYYY_M_D_H_Min_S (igual que OPTIMA)
    ts  = f"{now.year}_{now.month}_{now.day}_{now.hour}_{now.minute}_{now.second}"
    folder_name = f"{instancia}_{algoritmo}_{ts}"
    out_path    = os.path.join(OUTPUT_DIR, problema, folder_name)
    os.makedirs(out_path, exist_ok=True)
    return out_path


def _solution_to_text(problema: str, solution, instance_data: dict) -> str:
    """Convierte la solución a texto legible."""
    if problema == 'knapsack':
        selected = [i for i, x in enumerate(solution) if x]
        return (f"Items seleccionados ({len(selected)}/{instance_data['n']}): "
                f"{selected}\n"
                f"Peso total: {sum(instance_data['weights'][i] for i in selected)}"
                f" / {instance_data['capacity']}")
    elif problema == 'tsp':
        route = solution + [solution[0]]
        return "Ruta: " + " -> ".join(str(c) for c in route)
    elif problema == 'vrp':
        lines = [f"Rutas ({len(solution)}):"]
        for i, route in enumerate(solution):
            lines.append(f"  Ruta {i+1}: 0 -> {' -> '.join(str(c) for c in route)} -> 0")
        return "\n".join(lines)
    elif problema in ('flowshop', 'jobshop'):
        return "Permutación: " + " -> ".join(str(j) for j in solution)
    return str(solution)


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def run_experiment(problema: str,
                   instancia: str,
                   algoritmo: str,
                   seed: int = 42,
                   verbose: bool = True) -> dict:
    """
    Ejecuta un experimento completo y guarda los resultados.

    Returns
    -------
    dict con: problema, instancia, algoritmo, value, bks, gap_pct,
              iterations, time_s, output_dir
    """
    # Cargar instancia y solver
    fp     = _find_instance_file(problema, instancia)
    data   = load_instance(fp)
    solve  = _load_solver(problema, algoritmo)

    if verbose:
        print(f"  [{problema}] {instancia} × {algoritmo} ...", end='', flush=True)

    # Ejecutar
    result = solve(data, seed=seed)

    # Calcular métricas
    metrics = summarize(result, data, problema)

    if verbose:
        sign = "" if metrics['gap_pct'] >= 0 else ""
        print(f" valor={metrics['value']:.1f}  GAP={metrics['gap_pct']:.2f}%"
              f"  t={metrics['time_s']:.2f}s")

    # Guardar resultados
    out_dir = _make_output_dir(problema, instancia, algoritmo)

    # resultado.json
    output = {
        'problema':   problema,
        'instancia':  instancia,
        'algoritmo':  algoritmo,
        'seed':       seed,
        'value':      metrics['value'],
        'bks':        metrics['bks'],
        'gap_pct':    metrics['gap_pct'],
        'iterations': metrics['iterations'],
        'time_s':     metrics['time_s'],
        'history':    result.get('history', []),
    }
    with open(os.path.join(out_dir, 'resultado.json'), 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # solucion.txt
    sol_text = _solution_to_text(problema, result['solution'], data)
    with open(os.path.join(out_dir, 'solucion.txt'), 'w', encoding='utf-8') as f:
        f.write(f"Problema : {problema}\n")
        f.write(f"Instancia: {instancia}\n")
        f.write(f"Algoritmo: {algoritmo}\n")
        f.write(f"Valor    : {metrics['value']}\n")
        f.write(f"BKS      : {metrics['bks']}\n")
        f.write(f"GAP      : {metrics['gap_pct']:.4f}%\n\n")
        f.write(sol_text + "\n")

    return {**output, 'output_dir': out_dir}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ejecutar un experimento TS')
    parser.add_argument('--problema',   required=True, choices=PROBLEMS)
    parser.add_argument('--instancia',  required=True)
    parser.add_argument('--algoritmo',  required=True, choices=ALGORITHMS)
    parser.add_argument('--seed',       type=int, default=42)
    args = parser.parse_args()

    res = run_experiment(args.problema, args.instancia, args.algoritmo, args.seed)
    print(f"\nResultado guardado en: {res['output_dir']}")
