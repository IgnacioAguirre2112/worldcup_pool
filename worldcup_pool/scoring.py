def signo(goles_local: int, goles_visita: int) -> int:
    if goles_local > goles_visita:
        return 1
    if goles_local < goles_visita:
        return -1
    return 0


def calcular_puntaje(glp: int, gvp: int, glo: int, gvo: int) -> tuple[int, str]:
    """Retorna (puntaje, tipo): exacto, parcial, diferencia o ninguno."""
    if glp == glo and gvp == gvo:
        return 5, "exacto"
    puntos = 0
    tipo = "ninguno"
    if signo(glp, gvp) == signo(glo, gvo):
        puntos = 3
        tipo = "parcial"
    if (glp - gvp) == (glo - gvo):
        puntos += 1
        tipo = "diferencia" if tipo == "ninguno" else "parcial+diferencia"
    return puntos, tipo
