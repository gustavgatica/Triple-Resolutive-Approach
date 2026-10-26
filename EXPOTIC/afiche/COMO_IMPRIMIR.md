# Cómo exportar el afiche a PDF (90×120 cm)

1. Abre `afiche.html` en Chrome o Edge.
2. Ctrl+P → Destino: **Guardar como PDF**.
3. Más ajustes:
   - Tamaño de papel: **personalizado 90 × 120 cm** (si tu impresora virtual no lo permite, en Chrome el `@page` del HTML ya lo define; deja "Predeterminado").
   - Márgenes: **Ninguno**.
   - Escala: **100** (o "Predeterminada").
   - ✅ **Gráficos de fondo** (imprescindible para los colores).
4. Guarda como `Cartel_B_Pena_Diaz_2026.pdf`.

Notas:
- El logo UNAB es una recreación vectorial fiel al oficial (escala sin perder calidad); si prefieres el archivo oficial exacto, reemplaza el `<svg>` del encabezado por un `<img>`.
- El recuadro "QR repositorio" es un marcador de posición: genera un QR con la URL de tu GitHub y reemplázalo si quieres incluirlo.
