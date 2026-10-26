"""
tableMix.py — Calcula GAP promedio por algoritmo y genera mix.csv.
Uso: python src/utils/tableMix.py
"""
import sys, os, csv
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _ROOT)

CSV_IN  = os.path.join(_ROOT, 'results', 'tabla_consolidada.csv')
CSV_OUT = os.path.join(_ROOT, 'src', 'utils', 'mix.csv')

def compute_mix():
    if not os.path.exists(CSV_IN):
        print("Primero ejecuta: python src/main.py --all")
        return
    with open(CSV_IN, encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    stats = {'TS-Básico': [], 'TS-Intermedio': [], 'TS-Avanzado': []}
    by_prob = {}
    for row in rows:
        prob = row['Problema']
        if prob not in by_prob:
            by_prob[prob] = {'TS-Básico': [], 'TS-Intermedio': [], 'TS-Avanzado': []}
        for key, col in [('TS-Básico','GAP_B(%)'),('TS-Intermedio','GAP_I(%)'),('TS-Avanzado','GAP_A(%)')]:
            if row[col]:
                val = float(row[col])
                stats[key].append(val)
                by_prob[prob][key].append(val)

    print(f"\n{'Algoritmo':<20} {'GAP Promedio Global':>22}")
    print('-' * 44)
    for alg in ['TS-Básico','TS-Intermedio','TS-Avanzado']:
        vals = stats[alg]
        avg  = sum(vals)/len(vals) if vals else 0
        print(f"{alg:<20} {avg:>+21.4f}%")

    print(f"\n{'Problema':<18} {'TS-Básico':>12} {'TS-Inter':>12} {'TS-Avanz':>12}")
    print('-' * 58)
    for prob, d in sorted(by_prob.items()):
        def avg(lst): return sum(lst)/len(lst) if lst else float('nan')
        print(f"{prob:<18} {avg(d['TS-Básico']):>+11.2f}% {avg(d['TS-Intermedio']):>+11.2f}% {avg(d['TS-Avanzado']):>+11.2f}%")

    # Escribir mix.csv
    with open(CSV_OUT, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['Problema','TS-Básico_GAP%','TS-Intermedio_GAP%','TS-Avanzado_GAP%'])
        for prob, d in sorted(by_prob.items()):
            def avg(lst): return f"{sum(lst)/len(lst):+.4f}" if lst else ''
            w.writerow([prob, avg(d['TS-Básico']), avg(d['TS-Intermedio']), avg(d['TS-Avanzado'])])
    print(f"\n✓ mix.csv generado en {CSV_OUT}")

if __name__ == '__main__':
    compute_mix()
