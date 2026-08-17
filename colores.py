def aplicar_colores_pasteles(row):
    """
    Asigna colores de fondo claros y transparentes (rgba) basados en la 
    jerarquía visual solicitada, activándose únicamente si el valor es mayor a cero.
    """
    estilos = [''] * len(row)
    idx = row.index.get_loc
    
    # Nueva Paleta Visual Optimizada (Sutil pero definida)
    c_aranceles = 'background-color: rgba(180, 180, 180, 0.4); color: black;'  # Gris medio transparente
    c_sellados  = 'background-color: rgba(10, 40, 90, 0.35); color: black;'    # Azul oscuro transparente
    c_patentes  = 'background-color: rgba(25, 75, 140, 0.3); color: black;'    # Azul oscuro (un tono más claro)
    c_otros     = 'background-color: rgba(0, 191, 255, 0.35); color: black;'   # Celeste definido transparente
    c_gastos    = 'background-color: rgba(255, 100, 100, 0.35); color: black;' # Rojo claro transparente
    c_efectivo  = 'background-color: rgba(100, 220, 100, 0.35); color: black;' # Verde claro transparente
    c_debito    = 'background-color: rgba(255, 255, 150, 0.45); color: black;' # Amarillo suave transparente
    c_transf    = 'background-color: rgba(255, 140, 0, 0.4); color: black;'    # Naranja más intenso transparente

    try:
        if float(row.get('aranceles') or 0) > 0: estilos[idx('aranceles')] = c_aranceles
        if float(row.get('sellados') or 0) > 0:  estilos[idx('sellados')] = c_sellados
        if float(row.get('patentes') or 0) > 0:  estilos[idx('patentes')] = c_patentes
        if float(row.get('otros') or 0) > 0:     estilos[idx('otros')] = c_otros
        if float(row.get('gastos') or 0) > 0:    estilos[idx('gastos')] = c_gastos
        if float(row.get('efectivo') or 0) > 0:  estilos[idx('efectivo')] = c_efectivo
        if float(row.get('debito') or 0) > 0:    estilos[idx('debito')] = c_debito
        
        # Ambas columnas de transferencia comparten el naranja intensificado
        if float(row.get('transferencia') or 0) > 0:  estilos[idx('transferencia')] = c_transf
        if float(row.get('transferencia2') or 0) > 0: estilos[idx('transferencia2')] = c_transf
    except Exception:
        pass
        
    return estilos
