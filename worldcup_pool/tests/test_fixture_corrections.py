from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

import database
from models import Base, Partido, Pronostico, Usuario


class FixtureCorrectionsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        db_path = Path(self.tmpdir.name) / "test.db"
        self.original_engine = database.engine
        self.original_session = database.SessionLocal
        database.engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        database.SessionLocal = sessionmaker(bind=database.engine, expire_on_commit=False)
        Base.metadata.create_all(database.engine)

    def tearDown(self) -> None:
        database.engine.dispose()
        database.engine = self.original_engine
        database.SessionLocal = self.original_session
        self.tmpdir.cleanup()

    def test_corrige_partidos_que_venian_a_las_cero_horas_del_dia_anterior(self) -> None:
        with database.SessionLocal() as db:
            partido = Partido(
                fecha_hora_utc=database.chile_to_utc_naive("2026-06-13", "00:00"),
                fase="Fase de grupos",
                equipo_local="Australia",
                equipo_visita="Turquía",
            )
            db.add(partido)
            db.commit()
            partido_id = partido.id

        corregidos = database.apply_fixture_date_corrections()

        with database.SessionLocal() as db:
            partido = db.get(Partido, partido_id)

        self.assertEqual(corregidos, 1)
        self.assertEqual(database.utc_to_chile(partido.fecha_hora_utc).strftime("%Y-%m-%d %H:%M"), "2026-06-14 00:00")

    def test_elimina_duplicados_y_conserva_pronosticos(self) -> None:
        with database.SessionLocal() as db:
            usuario = Usuario(nombre="Tester")
            antiguo = Partido(
                fecha_hora_utc=database.chile_to_utc_naive("2026-06-13", "00:00"),
                fase="Fase de grupos",
                equipo_local="Australia",
                equipo_visita="Turquía",
            )
            correcto = Partido(
                fecha_hora_utc=database.chile_to_utc_naive("2026-06-14", "00:00"),
                fase="Fase de grupos",
                equipo_local="Australia",
                equipo_visita="Turquía",
            )
            db.add_all([usuario, antiguo, correcto])
            db.commit()
            db.add(
                Pronostico(
                    usuario_id=usuario.id,
                    partido_id=antiguo.id,
                    goles_local_pronosticado=1,
                    goles_visita_pronosticado=0,
                )
            )
            db.commit()

        eliminados = database.repair_fixture_duplicates()

        with database.SessionLocal() as db:
            partidos = db.scalars(
                select(Partido).where(
                    Partido.fase == "Fase de grupos",
                    Partido.equipo_local == "Australia",
                    Partido.equipo_visita == "Turquía",
                )
            ).all()
            pronosticos = db.scalars(select(Pronostico)).all()

        self.assertEqual(eliminados, 1)
        self.assertEqual(len(partidos), 1)
        self.assertEqual(database.utc_to_chile(partidos[0].fecha_hora_utc).strftime("%Y-%m-%d %H:%M"), "2026-06-14 00:00")
        self.assertEqual(len(pronosticos), 1)
        self.assertEqual(pronosticos[0].partido_id, partidos[0].id)


if __name__ == "__main__":
    unittest.main()
