"""
Modulo: Resumen De Pedidos (Web LDS)
Proyecto donde se confirmo: PR000335-SP5 (pausado 15/09/2026 antes de
escribir ningun caso de este aplicativo puntual).
Componente Angular: app-resumen-pedidos-page
Ruta de menu confirmada en vivo: Comercial > Atención Integral Al
Cliente > Resumen De Pedidos (item hoja directo, un solo popup).

**Confianza: SOLO navegacion.** Unicamente se confirmo en vivo que la
ruta de menu y el componente raiz son correctos (la app abre) - no se
exploraron filtros, grilla ni ninguna accion todavia. Si se retoma este
modulo, hace falta una exploracion en vivo completa antes de escribir
casos (Paso 2 de NUEVO_PROYECTO_CHECKLIST.md).

Requiere del framework compartido (via los bloques NAV / HELPERS_ESPERA):
  abrir_aplicacion, esperar_fin_de_carga, capturar_paso
"""


def abrir_resumen_pedidos(page, paso_excel=1):
    return abrir_aplicacion(page, ["Comercial", "Atención Integral Al Cliente", "Resumen De Pedidos"], "app-resumen-pedidos-page", paso_excel=paso_excel)
