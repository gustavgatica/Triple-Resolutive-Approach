# ============================================================
# Modelo AMPL — Permutation Flowshop Scheduling (PFSP)
# Minimización de Makespan (C_max)
# ============================================================
# Referencias:
#   Johnson, S. M. (1954). Optimal two- and three-stage production
#     schedules. Naval Research Logistics Quarterly, 1(1), 61–68.
#   Taillard, E. (1993). Benchmarks for basic scheduling problems.
#     European Journal of Operational Research, 64(2), 278–285.
#
# Uso:
#   ampl: model flowshop.mod; data flowshop.dat; solve; display Cmax;
# ============================================================

# --- Parámetros ---
param n;                        # Número de trabajos
param m;                        # Número de máquinas
param p {1..n, 1..m};          # Tiempo de procesamiento: trabajo i en máquina j

# --- Variables de decisión ---
var C {1..n, 1..m} >= 0;       # C[i,j] = tiempo de finalización del trabajo i en máquina j
var Cmax >= 0;                  # Makespan (tiempo total de finalización)

# --- Función objetivo ---
minimize Makespan: Cmax;

# --- Restricciones ---
subject to Inicio:
    C[1,1] = p[1,1];
# El primer trabajo comienza y termina en la máquina 1 según su tiempo de proceso.

subject to Secuencia_M1 {i in 2..n}:
    C[i,1] = C[i-1,1] + p[i,1];
# En la máquina 1, los trabajos se procesan secuencialmente.

subject to Primer_Trabajo {j in 2..m}:
    C[1,j] = C[1,j-1] + p[1,j];
# El primer trabajo pasa por todas las máquinas sin espera.

subject to General {i in 2..n, j in 2..m}:
    C[i,j] >= C[i-1,j] + p[i,j];
# El trabajo i en la máquina j no puede iniciar hasta que el trabajo i-1 termine en j.

subject to General2 {i in 2..n, j in 2..m}:
    C[i,j] >= C[i,j-1] + p[i,j];
# El trabajo i en la máquina j no puede iniciar hasta que el propio trabajo i
# termine en la máquina j-1.

subject to Def_Makespan {i in 1..n}:
    Cmax >= C[i,m];
# El Makespan es el tiempo de finalización del último trabajo en la última máquina.

# Nota: Este modelo asume que la permutación de trabajos ya está fijada
# (1, 2, ..., n). Para optimizar la permutación se requiere un modelo
# de programación entera mixta con variables de asignación adicionales,
# o resolver el modelo iterativamente sobre todas las permutaciones (solo
# factible para n pequeño).
