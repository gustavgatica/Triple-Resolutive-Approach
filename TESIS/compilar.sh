#!/usr/bin/env bash
# ======================================================================
#  Compila TESIS/tesis.tex -> tesis.pdf  (Linux / macOS)
#  Uso:  cd TESIS && ./compilar.sh
# ======================================================================
set -u
cd "$(dirname "$0")"

echo
echo "=========================================================="
echo "  Compilando la tesis"
echo "=========================================================="
echo

falta=0
for dep in ../paper/main.pdf ../EXPOTIC/afiche-triple-enfoque-resolutivo.pdf ../paper/referencias.bib; do
  if [ ! -f "$dep" ]; then
    echo "[ERROR] Falta $dep"
    falta=1
  fi
done
if [ "$falta" = 1 ]; then
  echo
  echo "Compilacion abortada: faltan dependencias."
  echo "Si falta paper/main.pdf, compila primero el paper:"
  echo "  cd ../paper && pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex"
  exit 1
fi

echo "[1/4] pdflatex  (primera pasada)"
pdflatex -interaction=nonstopmode tesis.tex >/dev/null 2>&1
echo "[2/4] bibtex    (bibliografia)"
bibtex tesis >/dev/null 2>&1
echo "[3/4] pdflatex  (inserta las citas)"
pdflatex -interaction=nonstopmode tesis.tex >/dev/null 2>&1
echo "[4/4] pdflatex  (indices y referencias cruzadas)"
pdflatex -interaction=nonstopmode tesis.tex >/dev/null 2>&1

echo
echo "=========================================================="

if [ ! -f tesis.pdf ]; then
  echo "  FALLO: no se genero tesis.pdf — revisa tesis.log"
  echo "=========================================================="
  exit 1
fi

problema=0
grep -q "^! "                     tesis.log && { echo "  [AVISO] Errores de LaTeX (busca \"! \" en tesis.log)"; problema=1; }
grep -q "Citation.*undefined"     tesis.log && { echo "  [AVISO] Citas sin resolver"; problema=1; }
grep -q "Reference.*undefined"    tesis.log && { echo "  [AVISO] Referencias cruzadas sin resolver"; problema=1; }

paginas=$(pdfinfo tesis.pdf 2>/dev/null | awk '/^Pages/{print $2}')

if [ "$problema" = 1 ]; then
  echo
  echo "  tesis.pdf generado con avisos (${paginas:-?} paginas)."
  echo "  Se conserva tesis.log para revisarlos."
else
  echo "  LISTO: tesis.pdf generado sin avisos (${paginas:-?} paginas)"
  rm -f tesis.aux tesis.log tesis.out tesis.toc tesis.lof tesis.lot tesis.lol tesis.bbl tesis.blg
fi

echo "=========================================================="
echo
