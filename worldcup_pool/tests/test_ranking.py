from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database
from models import Base, Partido, Pronostico, Usuario


class RankingTest(unittest.TestCase):
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

    def test_ranking_incluye_cantidad_total_de_goles(self) -> None:
        with database.SessionLocal() as db:
            usuario = Usuario(nombre="Tester")
            partido = Partido(
                fecha_hora_utc=datetime.utcnow() - timedelta(days=1),
                fase="Prueba",
                equipo_local="Brasil",
                equipo_visita="Argentina",
                goles_local=0,
                goles_visita=4,
                resultado_oficial_cargado=True,
            )
            db.add_all([usuario, partido])
            db.commit()
            db.add(Pronostico(usuario_id=usuario.id, partido_id=partido.id, goles_local_pronosticado=3, goles_visita_pronosticado=1))
            db.commit()

        df = database.ranking_dataframe()

        self.assertIn("Cant. goles", df.columns)
        self.assertEqual(int(df.loc[0, "Cant. goles"]), 1)
        self.assertEqual(int(df.loc[0, "Total"]), 1)

    def test_empate_correcto_aplica_solo_despues_del_corte(self) -> None:
        with database.SessionLocal() as db:
            usuario = Usuario(nombre="Empates")
            antes = Partido(
                fecha_hora_utc=database.EMPATE_RULE_EFFECTIVE_UTC - timedelta(minutes=1),
                fase="Prueba",
                equipo_local="Chile",
                equipo_visita="Brasil",
                goles_local=2,
                goles_visita=2,
                resultado_oficial_cargado=True,
            )
            despues = Partido(
                fecha_hora_utc=database.EMPATE_RULE_EFFECTIVE_UTC + timedelta(minutes=1),
                fase="Prueba",
                equipo_local="Argentina",
                equipo_visita="Uruguay",
                goles_local=2,
                goles_visita=2,
                resultado_oficial_cargado=True,
            )
            db.add_all([usuario, antes, despues])
            db.commit()
            db.add_all(
                [
                    Pronostico(
                        usuario_id=usuario.id,
                        partido_id=antes.id,
                        goles_local_pronosticado=1,
                        goles_visita_pronosticado=1,
                    ),
                    Pronostico(
                        usuario_id=usuario.id,
                        partido_id=despues.id,
                        goles_local_pronosticado=1,
                        goles_visita_pronosticado=1,
                    ),
                ]
            )
            db.commit()

        df = database.ranking_dataframe()

        self.assertEqual(int(df.loc[0, "Resultado"]), 1)
        self.assertEqual(int(df.loc[0, "Cant. goles"]), 0)
        self.assertEqual(int(df.loc[0, "Total"]), 3)


if __name__ == "__main__":
    unittest.main()
