"""
loader.py — Parsers de instancias para los 5 problemas de optimización.

Formatos soportados:
  - Knapsack:  .kp    (OR-Library knapPI style)
  - TSP:       .tsp   (TSPLIB format)
  - VRP:       .vrp   (OR-Library Christofides format)
  - Flowshop:  .fsp   (Taillard format)
  - Job Shop:  .jss   (OR-Library jobshop1 format)
"""

import os
import math
import re


# ──────────────────────────────────────────────────────────────
# KNAPSACK
# ──────────────────────────────────────────────────────────────
def load_knapsack(filepath):
    """
    Carga una instancia Knapsack desde archivo .kp.

    Formato:
        # comentarios opcionales
        n  capacity
        profit_1  weight_1
        ...
        profit_n  weight_n

    Retorna:
        dict con claves: n, capacity, profits (list), weights (list), bks (int|None)
    """
    profits, weights = [], []
    n = capacity = None
    bks = None

    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):
                # Extraer BKS del comentario si existe
                m = re.search(r'BKS=(\d+)', line)
                if m:
                    bks = int(m.group(1))
                continue
            nums = list(map(int, line.split()))
            if n is None:
                n, capacity = nums[0], nums[1]
            else:
                profits.append(nums[0])
                weights.append(nums[1])

    return {
        'name': os.path.splitext(os.path.basename(filepath))[0],
        'problem': 'knapsack',
        'n': n,
        'capacity': capacity,
        'profits': profits,
        'weights': weights,
        'bks': bks,
    }


# ──────────────────────────────────────────────────────────────
# TSP
# ──────────────────────────────────────────────────────────────
# BKS conocidos para instancias TSPLIB usadas
TSP_BKS = {
    'berlin52': 7542,
    'eil51':    426,
    'eil76':    538,
    'kroA100':  21282,
    'kroB100':  22141,
}

def load_tsp(filepath):
    """
    Carga una instancia TSP desde archivo .tsp (formato TSPLIB).

    Soporta: EUC_2D y ATT edge weight types.

    Retorna:
        dict con claves: n, coords (list of (x,y)), dist_matrix, bks
    """
    coords = {}
    edge_type = 'EUC_2D'
    n = 0
    reading_nodes = False

    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if line.startswith('DIMENSION'):
                n = int(line.split()[-1])
            elif line.startswith('EDGE_WEIGHT_TYPE'):
                edge_type = line.split()[-1]
            elif line == 'NODE_COORD_SECTION':
                reading_nodes = True
            elif line in ('EOF', 'DISPLAY_DATA_SECTION'):
                reading_nodes = False
            elif reading_nodes:
                parts = line.split()
                if len(parts) >= 3:
                    idx = int(parts[0])
                    x, y = float(parts[1]), float(parts[2])
                    coords[idx] = (x, y)

    # Construir matriz de distancias
    nodes = [coords[i] for i in sorted(coords.keys())]
    dist = _build_dist_matrix(nodes, edge_type)

    name = os.path.splitext(os.path.basename(filepath))[0]
    return {
        'name': name,
        'problem': 'tsp',
        'n': n,
        'coords': nodes,
        'dist_matrix': dist,
        'bks': TSP_BKS.get(name),
    }

def _build_dist_matrix(coords, edge_type='EUC_2D'):
    n = len(coords)
    dist = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            dx = coords[i][0] - coords[j][0]
            dy = coords[i][1] - coords[j][1]
            if edge_type == 'ATT':
                r = math.sqrt((dx * dx + dy * dy) / 10.0)
                d = int(r)
                if d < r:
                    d += 1
            else:  # EUC_2D
                d = int(round(math.sqrt(dx * dx + dy * dy)))
            dist[i][j] = dist[j][i] = d
    return dist


# ──────────────────────────────────────────────────────────────
# VRP (Christofides — OR-Library format)
# ──────────────────────────────────────────────────────────────
# BKS conocidos (OR-Library Christofides instances)
VRP_BKS = {
    'vrpnc1': 524,
    'vrpnc2': 835,
    'vrpnc3': 826,
    'vrpnc4': 1028,
}

def load_vrp(filepath):
    """
    Carga instancia VRP en formato OR-Library (Christofides).

    Formato:
        n  capacity  max_route_length  depot_id
        depot_x  depot_y
        x1  y1  demand1
        ...
        xn  yn  demandn

    Retorna:
        dict: n_customers, capacity, depot (x,y), customers (list of (x,y,demand)),
              dist_matrix, bks
    """
    lines = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                lines.append(line)

    header = lines[0].split()
    n_cust = int(header[0])
    capacity = int(header[1])

    depot_parts = lines[1].split()
    depot = (float(depot_parts[0]), float(depot_parts[1]))

    customers = []
    for line in lines[2:2 + n_cust]:
        parts = line.split()
        x, y, d = float(parts[0]), float(parts[1]), int(parts[2])
        customers.append((x, y, d))

    # Construir matriz de distancias (depósito=0, clientes=1..n)
    all_nodes = [depot] + [(c[0], c[1]) for c in customers]
    n_total = len(all_nodes)
    dist = [[0.0] * n_total for _ in range(n_total)]
    for i in range(n_total):
        for j in range(i + 1, n_total):
            dx = all_nodes[i][0] - all_nodes[j][0]
            dy = all_nodes[i][1] - all_nodes[j][1]
            d = round(math.sqrt(dx * dx + dy * dy), 2)
            dist[i][j] = dist[j][i] = d

    name = os.path.splitext(os.path.basename(filepath))[0]
    return {
        'name': name,
        'problem': 'vrp',
        'n_customers': n_cust,
        'capacity': capacity,
        'depot': depot,
        'customers': customers,
        'dist_matrix': dist,
        'bks': VRP_BKS.get(name),
    }


# ──────────────────────────────────────────────────────────────
# FLOWSHOP (Taillard format)
# ──────────────────────────────────────────────────────────────
# BKS conocidos (Taillard 1993 y actualizaciones posteriores); los cinco son
# makespan óptimos. Las instancias se regeneran con
# instances/flowshop/generar_taillard.py.
FLOWSHOP_BKS = {
    'ta001': 1278,
    'ta011': 1582,
    'ta021': 2297,
    'ta031': 2724,
    'ta041': 2991,
}

def load_flowshop(filepath):
    """
    Carga instancia Permutation Flowshop Scheduling desde archivo .fsp.

    Formato:
        # comentarios
        n_jobs  n_machines
        p[0][0]  p[0][1]  ...  p[0][m-1]
        ...
        p[n-1][0]  ...  p[n-1][m-1]

    p[i][j] = tiempo de procesamiento del trabajo i en la máquina j.

    Retorna:
        dict: n_jobs, n_machines, processing (matrix n×m), bks
    """
    processing = []
    n_jobs = n_machines = None

    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            nums = list(map(int, line.split()))
            if n_jobs is None:
                n_jobs, n_machines = nums[0], nums[1]
            else:
                processing.append(nums)

    name = os.path.splitext(os.path.basename(filepath))[0]
    return {
        'name': name,
        'problem': 'flowshop',
        'n_jobs': n_jobs,
        'n_machines': n_machines,
        'processing': processing,
        'bks': FLOWSHOP_BKS.get(name),
    }


# ──────────────────────────────────────────────────────────────
# JOB SHOP SCHEDULING (OR-Library format)
# ──────────────────────────────────────────────────────────────
JOBSHOP_BKS = {
    'ft10': 930,
    'la01': 666,
    'la06': 926,
    'la11': 1222,
    'la21': 1046,
}

def load_jobshop(filepath):
    """
    Carga instancia Job Shop Scheduling desde archivo .jss.

    Formato (OR-Library):
        # comentarios
        n_jobs  n_machines
        machine_0 time_0  machine_1 time_1  ... (por trabajo)

    Retorna:
        dict: n_jobs, n_machines,
              machines (matriz n×m con secuencia de máquinas por trabajo),
              times (matriz n×m con tiempos de procesamiento),
              bks
    """
    n_jobs = n_machines = None
    machines_data = []
    times_data = []

    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            nums = list(map(int, line.split()))
            if n_jobs is None:
                n_jobs, n_machines = nums[0], nums[1]
            else:
                # Pares: (machine, time) por operación
                mach_row = [nums[2 * k] for k in range(n_machines)]
                time_row = [nums[2 * k + 1] for k in range(n_machines)]
                machines_data.append(mach_row)
                times_data.append(time_row)

    name = os.path.splitext(os.path.basename(filepath))[0]
    return {
        'name': name,
        'problem': 'jobshop',
        'n_jobs': n_jobs,
        'n_machines': n_machines,
        'machines': machines_data,
        'times': times_data,
        'bks': JOBSHOP_BKS.get(name),
    }


# ──────────────────────────────────────────────────────────────
# FUNCIÓN GENÉRICA
# ──────────────────────────────────────────────────────────────
def load_instance(filepath):
    """
    Detecta el tipo de problema por extensión y carga la instancia.
    """
    ext = os.path.splitext(filepath)[1].lower()
    loaders = {
        '.kp':  load_knapsack,
        '.tsp': load_tsp,
        '.vrp': load_vrp,
        '.fsp': load_flowshop,
        '.jss': load_jobshop,
    }
    if ext not in loaders:
        raise ValueError(f"Extensión no soportada: {ext}. Use: {list(loaders.keys())}")
    return loaders[ext](filepath)


# ──────────────────────────────────────────────────────────────
# UTILIDAD: listar todas las instancias del proyecto
# ──────────────────────────────────────────────────────────────
def list_all_instances(base_dir):
    """
    Devuelve un dict con las rutas de todas las instancias agrupadas por problema.
    base_dir: ruta a la carpeta 'instances/'
    """
    problems = {
        'knapsack': '.kp',
        'tsp':      '.tsp',
        'vrp':      '.vrp',
        'flowshop': '.fsp',
        'jobshop':  '.jss',
    }
    result = {}
    for prob, ext in problems.items():
        folder = os.path.join(base_dir, prob)
        if os.path.isdir(folder):
            files = sorted(
                os.path.join(folder, f)
                for f in os.listdir(folder)
                if f.endswith(ext)
            )
            result[prob] = files
    return result


# ──────────────────────────────────────────────────────────────
# PRUEBA RÁPIDA
# ──────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import sys

    # Detectar ruta base
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base = os.path.join(os.path.dirname(script_dir), 'instances')

    instances = list_all_instances(base)
    print("=== Instancias disponibles ===")
    for prob, files in instances.items():
        print(f"\n[{prob.upper()}]")
        for f in files:
            try:
                data = load_instance(f)
                bks = data.get('bks', 'N/A')
                name = data['name']
                print(f"  {name:15s}  BKS={bks}")
            except Exception as e:
                print(f"  ERROR cargando {f}: {e}")
