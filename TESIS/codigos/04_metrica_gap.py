# Metrica unica de comparacion: GAP porcentual respecto al mejor valor
# conocido (BKS). El signo se invierte para Knapsack, que es el unico
# problema de maximizacion del conjunto.
# Fuente: src/metrics.py

def gap(value: float, bks: float, minimization: bool = True) -> float:
    """
    Minimizacion (TSP, VRP, Flowshop, Job Shop):
        GAP = (value - BKS) / BKS * 100
    Maximizacion (Knapsack):
        GAP = (BKS - value) / BKS * 100

    Un GAP negativo indica que se supero el BKS, lo que es posible porque
    el BKS no es un optimo demostrado sino el mejor valor reportado en la
    literatura.
    """
    if bks <= 0:
        return 0.0
    if minimization:
        return (value - bks) / bks * 100.0
    else:
        return (bks - value) / bks * 100.0


MINIMIZATION: dict[str, bool] = {
    "knapsack": False,   # maximizar valor
    "tsp":      True,
    "vrp":      True,
    "flowshop": True,
    "jobshop":  True,
}
