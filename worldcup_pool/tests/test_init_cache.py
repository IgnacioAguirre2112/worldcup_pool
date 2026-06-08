from __future__ import annotations

import unittest
from unittest.mock import patch

import database


class InitCacheTest(unittest.TestCase):
    def test_init_db_no_resincroniza_en_mismo_proceso(self) -> None:
        original_initialized = database._DB_INITIALIZED_ENGINE_ID
        database._DB_INITIALIZED_ENGINE_ID = None
        try:
            with patch.object(database.Base.metadata, "create_all") as create_all, patch.object(
                database, "ensure_fixture_loaded"
            ) as ensure_fixture_loaded:
                database.init_db()
                database.init_db()

            self.assertEqual(create_all.call_count, 1)
            self.assertEqual(ensure_fixture_loaded.call_count, 1)
        finally:
            database._DB_INITIALIZED_ENGINE_ID = original_initialized


if __name__ == "__main__":
    unittest.main()
