"""
tableExport.py — Imprime la tabla consolidada de resultados en consola.
Uso: python src/utils/tableExport.py
"""
import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), 'results', 'tabla_consolidada.csv')

def print_table():
    if not os.path.exists(CSV_PATH):
        print("tabla_consolidada.csv no encontrada. Ejecuta: python src/main.py --all")
        return
    with open(CSV_PATH, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        return
    headers = list(rows[0].keys())
    widths  = [max(len(h), max(len(r[h]) for r in rows)) for h in headers]
    sep     = '+' + '+'.join('-' * (w + 2) for w in widths) + '+'
    def fmt_row(r):
        return '|' + '|'.join(f" {r[h]:<{widths[i]}} " for i, h in enumerate(headers)) + '|'
    print(sep)
    print(fmt_row({h: h for h in headers}))
    print(sep)
    prev_prob = None
    for row in rows:
        if row['Problema'] != prev_prob and prev_prob is not None:
            print(sep)
        print(fmt_row(row))
        prev_prob = row['Problema']
    print(sep)

if __name__ == '__main__':
    print_table()
