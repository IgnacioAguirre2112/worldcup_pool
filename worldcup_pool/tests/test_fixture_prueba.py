from __future__ import annotations

import unittest

import database
from models import Partido


class FixturePruebaTest(unittest.TestCase):
    def test_fixture_incluye_partido_prueba_chile_brasil(self) -> None:
        database.init_db()

        with database.SessionLocal() as db:
            partido = (
                db.query(Partido)
                .filter(
                    Partido.fase == "Prueba",
                    Partido.equipo_local == "Chile",
                    Partido.equipo_visita == "Brasil",
                )
                .one_or_none()
            )

        self.assertIsNotNone(partido)
        self.assertEqual(database.utc_to_chile(partido.fecha_hora_utc).strftime("%Y-%m-%d %H:%M"), "2026-06-05 18:00")

    def test_fixture_incluye_partido_prueba_brasil_argentina(self) -> None:
        database.init_db()

        with database.SessionLocal() as db:
            partido = (
                db.query(Partido)
                .filter(
                    Partido.fase == "Prueba",
                    Partido.equipo_local == "Brasil",
                    Partido.equipo_visita == "Argentina",
                )
                .one_or_none()
            )

        self.assertIsNotNone(partido)
        self.assertEqual(database.utc_to_chile(partido.fecha_hora_utc).strftime("%Y-%m-%d %H:%M"), "2026-06-09 12:00")


if __name__ == "__main__":
    unittest.main()
