"""
Modulo: Listado Pedidos Importantes (Web LDS)
Proyecto donde se confirmo: PR000335-SP5 (pausado 15/09/2026 antes de
escribir ningun caso de este aplicativo puntual).
Componente Angular: app-listado-pedidos-importantes
Ruta de menu confirmada en vivo: Comercial > Atención Integral Al
Cliente > Listado Pedidos Importantes (item hoja directo, un solo
popup).

**Confianza: SOLO navegacion.** Unicamente se confirmo en vivo que la
ruta de menu y el componente raiz son correctos (la app abre) - no se
exploraron filtros, grilla ni ninguna accion todavia. Si se retoma este
modulo, hace falta una exploracion en vivo completa antes de escribir
casos (Paso 2 de NUEVO_PROYECTO_CHECKLIST.md).

Requiere del framework compartido (via los bloques NAV / HELPERS_ESPERA):
  abrir_aplicacion, esperar_fin_de_carga, capturar_paso
"""


def abrir_listado_pedidos_importantes(page, paso_excel=1):
    return abrir_aplicacion(page, ["Comercial", "Atención Integral Al Cliente", "Listado Pedidos Importantes"], "app-listado-pedidos-importantes", paso_excel=paso_excel)
