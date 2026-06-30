from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database
from models import Base, Partido, Pronostico, Usuario


class PronosticosPublicosTest(unittest.TestCase):
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

    def test_oculta_pronostico_de_partido_abierto(self) -> None:
        with database.SessionLocal() as db:
            usuario = Usuario(nombre="Tester")
            partido = Partido(
                fecha_hora_utc=datetime.utcnow() + timedelta(hours=1),
                fase="Prueba",
                equipo_local="Chile",
                equipo_visita="Brasil",
            )
            db.add_all([usuario, partido])
            db.commit()
            db.add(Pronostico(usuario_id=usuario.id, partido_id=partido.id, goles_local_pronosticado=2, goles_visita_pronosticado=1))
            db.commit()

        df = database.pronosticos_publicos_dataframe()

        self.assertEqual(df.iloc[0]["Pronóstico"], "Oculto hasta el inicio")
        self.assertEqual(df.iloc[0]["Estado"], "Abierto")

    def test_muestra_pronostico_de_partido_cerrado(self) -> None:
        with database.SessionLocal() as db:
            usuario = Usuario(nombre="Tester")
            partido = Partido(
                fecha_hora_utc=datetime.utcnow() - timedelta(minutes=1),
                fase="Prueba",
                equipo_local="Chile",
                equipo_visita="Brasil",
            )
            db.add_all([usuario, partido])
            db.commit()
            db.add(Pronostico(usuario_id=usuario.id, partido_id=partido.id, goles_local_pronosticado=2, goles_visita_pronosticado=1))
            db.commit()

        df = database.pronosticos_publicos_dataframe()

        self.assertEqual(df.iloc[0]["Pronóstico"], "2 - 1")
        self.assertEqual(df.iloc[0]["Estado"], "Cerrado")

    def test_ultimos_cerrados_muestra_solo_dos_partidos_mas_recientes(self) -> None:
        with database.SessionLocal() as db:
            usuario = Usuario(nombre="Tester")
            partidos = [
                Partido(
                    fecha_hora_utc=datetime.utcnow() - timedelta(hours=3),
                    fase="Prueba",
                    equipo_local="Chile",
                    equipo_visita="Brasil",
                ),
                Partido(
                    fecha_hora_utc=datetime.utcnow() - timedelta(hours=2),
                    fase="Prueba",
                    equipo_local="Argentina",
                    equipo_visita="Uruguay",
                ),
                Partido(
                    fecha_hora_utc=datetime.utcnow() - timedelta(hours=1),
                    fase="Prueba",
                    equipo_local="México",
                    equipo_visita="Canadá",
                ),
            ]
            db.add_all([usuario, *partidos])
            db.commit()
            for partido in partidos:
                db.add(
                    Pronostico(
                        usuario_id=usuario.id,
                        partido_id=partido.id,
                        goles_local_pronosticado=1,
                        goles_visita_pronosticado=0,
                    )
                )
            db.commit()

        df = database.ultimos_pronosticos_cerrados_dataframe(limit=2)

        self.assertEqual(set(df["Partido"]), {"Argentina vs Uruguay", "México vs Canadá"})
        self.assertNotIn("Chile vs Brasil", set(df["Partido"]))
        self.assertTrue((df["Estado"] == "Cerrado").all())


if __name__ == "__main__":
    unittest.main()
