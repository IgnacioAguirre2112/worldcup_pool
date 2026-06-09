from __future__ import annotations

import unittest

from scoring import calcular_puntaje


class ScoringTest(unittest.TestCase):
    def test_marcador_exacto_suma_cinco(self) -> None:
        self.assertEqual(calcular_puntaje(2, 1, 2, 1), (5, "exacto"))

    def test_ganador_correcto_suma_tres_sin_sumar_goles(self) -> None:
        self.assertEqual(calcular_puntaje(4, 0, 3, 1), (3, "ganador"))

    def test_cantidad_total_de_goles_suma_uno_si_no_acierta_ganador(self) -> None:
        self.assertEqual(calcular_puntaje(3, 1, 0, 4), (1, "goles"))

    def test_empate_pronosticado_no_suma_ganador_si_resultado_tiene_ganador(self) -> None:
        self.assertEqual(calcular_puntaje(2, 2, 3, 1), (1, "goles"))

    def test_empate_oficial_no_suma_tres_por_ganador(self) -> None:
        self.assertEqual(calcular_puntaje(2, 0, 1, 1), (1, "goles"))

    def test_sin_acierto_suma_cero(self) -> None:
        self.assertEqual(calcular_puntaje(2, 0, 0, 1), (0, "ninguno"))


if __name__ == "__main__":
    unittest.main()
