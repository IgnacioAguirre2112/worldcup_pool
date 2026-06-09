def signo(goles_local: int, goles_visita: int) -> int:
    if goles_local > goles_visita:
        return 1
    if goles_local < goles_visita:
        return -1
    return 0


def calcular_puntaje(glp: int, gvp: int, glo: int, gvo: int) -> tuple[int, str]:
    """Retorna (puntaje, tipo): exacto, ganador, goles o ninguno."""
    if glp == glo and gvp == gvo:
        return 5, "exacto"
    if signo(glo, gvo) != 0 and signo(glp, gvp) == signo(glo, gvo):
        return 3, "ganador"
    if (glp + gvp) == (glo + gvo):
        return 1, "goles"
    return 0, "ninguno"
