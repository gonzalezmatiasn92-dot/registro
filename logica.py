import re
from datetime import datetime, timedelta

def formato_moneda(valor):
    """Da formato de dinero local argentino ($ 1.250.000,00)"""
    return f"$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def limpiar_monto(texto):
    """Procesador de números y fórmulas avanzadas con soporte de '=' e ingresos negativos"""
    if not texto:
        return 0.0
    texto_str = str(texto).strip()
    es_negativo = False
    
    if texto_str.startswith("-"):
        es_negativo = True
        texto_str = texto_str[1:]
    elif texto_str.startswith("=-"):
        es_negativo = True
        texto_str = "=" + texto_str[2:]
        
    if texto_str.startswith("="):
        try:
            formula = texto_str[1:].replace(".", "").replace(",", ".")
            formula_segura = re.sub(r'[^0-9+\-*/().]', '', formula)
            res = float(eval(formula_segura))
            return -res if es_negativo else res
        except:
            return 0.0
    try:
        res = float(texto_str.replace(".", "").replace(",", "."))
        return -res if es_negativo else res
    except:
        return 0.0

def calcular_balances_historicos(movimientos_nube, fecha_actual):
    """Cerebro matemático: Procesa el acumulado infinito y los rangos de la interfaz"""
    tot_efectivo_acumulado = 0.0
    saldo_acara = 0.0
    saldo_carcos = 0.0
    saldo_gastos_generales = 0.0
    acumulado_quincena_obligaciones = 0.0
    acumulado_aranceles_mes = 0.0

    # Lógica de quincenas y meses
    hoy = datetime.now()
    if hoy.day <= 15:
        inicio_q, fin_q = datetime(hoy.year, hoy.month, 1), datetime(hoy.year, hoy.month, 15)
    else:
        inicio_q = datetime(hoy.year, hoy.month, 16)
        sig_mes = hoy.month % 12 + 1
        sig_anio = hoy.year if sig_mes > 1 else hoy.year + 1
        fin_q = datetime(sig_anio, sig_mes, 1) - timedelta(days=1)
    
    inicio_mes = datetime(hoy.year, hoy.month, 1)

    for m in movimientos_nube:
        det = str(m.get("detalle", ""))
        efec = float(m.get("efectivo", 0.0))
        
        tot_efectivo_acumulado += efec
        
        if "Fondo ACARA" in det:
            saldo_acara += efec
        elif "Fondo Carcos" in det:
            saldo_carcos += efec
        elif "Gastos Generales" in det:
            saldo_gastos_generales += efec

        try:
            if inicio_q <= datetime.strptime(fecha_actual, "%d/%m/%Y") <= fin_q:
                acumulado_quincena_obligaciones += float(m.get("sellados", 0.0)) + float(m.get("patentes", 0.0))
            if inicio_mes <= datetime.strptime(fecha_actual, "%d/%m/%Y"):
                acumulado_aranceles_mes += float(m.get("aranceles", 0.0))
        except:
            pass

    return {
        "efectivo_acumulado": tot_efectivo_acumulado,
        "acara": saldo_acara,
        "carcos": saldo_carcos,
        "gastos_generales": saldo_gastos_generales,
        "quincena_obligaciones": acumulado_quincena_obligaciones,
        "aranceles_mes": acumulado_aranceles_mes
    }
