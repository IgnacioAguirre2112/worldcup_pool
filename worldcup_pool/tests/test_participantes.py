from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database
from models import Base


class ParticipantesTest(unittest.TestCase):
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

    def test_busca_participante_existente_para_login(self) -> None:
        creado = database.crear_usuario("Ignacio")
        encontrado = database.buscar_usuario_por_nombre("  ignacio  ")

        self.assertIsNotNone(encontrado)
        self.assertEqual(encontrado.id, creado.id)
        self.assertEqual(encontrado.nombre, "Ignacio")

    def test_no_crea_participante_duplicado(self) -> None:
        database.crear_usuario("Ignacio")

        with self.assertRaisesRegex(ValueError, "registrado"):
            database.crear_usuario("ignacio")


if __name__ == "__main__":
    unittest.main()
