@echo off
REM ======================================================================
REM  Compila TESIS/tesis.tex -> tesis.pdf  (Windows)
REM
REM  Uso:  doble clic, o desde la terminal:  cd TESIS  &&  compilar.bat
REM
REM  Hace las cuatro pasadas necesarias y avisa si algo quedo mal.
REM ======================================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ==========================================================
echo   Compilando la tesis
echo ==========================================================
echo.

REM --- Comprobar dependencias externas ---------------------------------
set FALTA=0
if not exist "..\paper\main.pdf" (
  echo [ERROR] Falta ..\paper\main.pdf  ^(se inserta como capitulo 3^)
  echo         Compila primero el paper:  cd ..\paper ^&^& pdflatex main.tex
  set FALTA=1
)
if not exist "..\EXPOTIC\afiche-triple-enfoque-resolutivo.pdf" (
  echo [ERROR] Falta ..\EXPOTIC\afiche-triple-enfoque-resolutivo.pdf
  set FALTA=1
)
if not exist "..\paper\referencias.bib" (
  echo [ERROR] Falta ..\paper\referencias.bib  ^(bibliografia^)
  set FALTA=1
)
if "!FALTA!"=="1" (
  echo.
  echo Compilacion abortada: faltan dependencias.
  pause
  exit /b 1
)

REM --- Las cuatro pasadas ----------------------------------------------
echo [1/4] pdflatex  ^(primera pasada^)
pdflatex -interaction=nonstopmode tesis.tex > nul 2>&1

echo [2/4] bibtex    ^(bibliografia^)
bibtex tesis > nul 2>&1

echo [3/4] pdflatex  ^(inserta las citas^)
pdflatex -interaction=nonstopmode tesis.tex > nul 2>&1

echo [4/4] pdflatex  ^(indices y referencias cruzadas^)
pdflatex -interaction=nonstopmode tesis.tex > nul 2>&1

echo.
echo ==========================================================

if not exist "tesis.pdf" (
  echo   FALLO: no se genero tesis.pdf
  echo   Revisa tesis.log para ver el error.
  echo ==========================================================
  pause
  exit /b 1
)

REM --- Diagnostico ------------------------------------------------------
set PROBLEMA=0

findstr /C:"! " tesis.log > nul 2>&1
if not errorlevel 1 (
  echo   [AVISO] Hay errores de LaTeX. Busca "! " en tesis.log
  set PROBLEMA=1
)
findstr /C:"Citation" tesis.log | findstr /C:"undefined" > nul 2>&1
if not errorlevel 1 (
  echo   [AVISO] Citas sin resolver. Verifica que bibtex haya corrido.
  set PROBLEMA=1
)
findstr /C:"Reference" tesis.log | findstr /C:"undefined" > nul 2>&1
if not errorlevel 1 (
  echo   [AVISO] Referencias cruzadas sin resolver. Vuelve a compilar.
  set PROBLEMA=1
)

if "!PROBLEMA!"=="1" (
  echo.
  echo   tesis.pdf se genero, pero con avisos.
  echo   Se conserva tesis.log para que puedas revisarlos.
) else (
  echo   LISTO: tesis.pdf generado sin avisos
  REM Solo se limpia si todo salio bien; si no, el log hace falta.
  del /q tesis.aux tesis.log tesis.out tesis.toc tesis.lof tesis.lot tesis.lol tesis.bbl tesis.blg 2>nul
)

echo ==========================================================
echo.

start "" "tesis.pdf"
endlocal
