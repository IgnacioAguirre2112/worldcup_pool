from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

import database
from models import Base, Partido, Pronostico, Usuario


class BloqueoPartidosTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        db_path = Path(self.tmpdir.name) / "test.db"
        self.original_engine = database.engine
        self.original_session = database.SessionLocal
        database.engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        database.SessionLocal = sessionmaker(bind=database.engine, expire_on_commit=False)
        Base.metadata.create_all(database.engine)

        with database.SessionLocal() as db:
            self.usuario = Usuario(nombre="Tester")
            self.partido_pasado = Partido(
                fecha_hora_utc=datetime.utcnow() - timedelta(minutes=1),
                fase="Test",
                equipo_local="México",
                equipo_visita="Escocia",
            )
            self.partido_futuro = Partido(
                fecha_hora_utc=datetime.utcnow() + timedelta(minutes=10),
                fase="Test",
                equipo_local="RD de Congo",
                equipo_visita="Brasil",
            )
            db.add_all([self.usuario, self.partido_pasado, self.partido_futuro])
            db.commit()
            self.usuario_id = self.usuario.id
            self.partido_pasado_id = self.partido_pasado.id
            self.partido_futuro_id = self.partido_futuro.id

    def tearDown(self) -> None:
        database.engine.dispose()
        database.engine = self.original_engine
        database.SessionLocal = self.original_session
        self.tmpdir.cleanup()

    def test_no_permite_pronostico_despues_del_inicio(self) -> None:
        with self.assertRaisesRegex(ValueError, "Pronóstico cerrado"):
            database.guardar_pronostico(self.usuario_id, self.partido_pasado_id, 1, 0)

        with database.SessionLocal() as db:
            total = db.scalar(select(func.count(Pronostico.id))) or 0
        self.assertEqual(total, 0)

    def test_permite_pronostico_antes_del_inicio(self) -> None:
        database.guardar_pronostico(self.usuario_id, self.partido_futuro_id, 2, 1)

        with database.SessionLocal() as db:
            total = db.scalar(select(func.count(Pronostico.id))) or 0
        self.assertEqual(total, 1)


if __name__ == "__main__":
    unittest.main()
