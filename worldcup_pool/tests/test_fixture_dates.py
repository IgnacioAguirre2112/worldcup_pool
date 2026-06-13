from __future__ import annotations

import csv
import unittest

import database


class FixtureDatesTest(unittest.TestCase):
    def test_fechas_de_partidos_a_medianoche_estan_en_el_dia_correcto(self) -> None:
        expected = {
            ("Australia", "Turquía"): ("2026-06-14", "00:00"),
            ("Austria", "Jordania"): ("2026-06-17", "00:00"),
            ("Túnez", "Japón"): ("2026-06-21", "00:00"),
        }

        with database.FIXTURE_PATH.open(encoding="utf-8", newline="") as f:
            rows = {(row["local"], row["visita"]): row for row in csv.DictReader(f)}

        for teams, (fecha, hora) in expected.items():
            self.assertEqual(rows[teams]["fecha"], fecha)
            self.assertEqual(rows[teams]["hora_chile"], hora)


if __name__ == "__main__":
    unittest.main()
