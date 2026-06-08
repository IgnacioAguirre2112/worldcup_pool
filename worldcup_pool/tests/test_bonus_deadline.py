from __future__ import annotations

import unittest
from datetime import datetime, timedelta

import database


class BonusDeadlineTest(unittest.TestCase):
    def test_bonus_abierto_antes_del_plazo(self) -> None:
        original_deadline = database.BONUS_DEADLINE_CHILE
        database.BONUS_DEADLINE_CHILE = datetime.now(database.CHILE_TZ) + timedelta(days=1)
        try:
            self.assertFalse(database.bonus_bloqueado())
        finally:
            database.BONUS_DEADLINE_CHILE = original_deadline

    def test_bonus_cerrado_despues_del_plazo(self) -> None:
        original_deadline = database.BONUS_DEADLINE_CHILE
        database.BONUS_DEADLINE_CHILE = datetime.now(database.CHILE_TZ) - timedelta(days=1)
        try:
            self.assertTrue(database.bonus_bloqueado())
        finally:
            database.BONUS_DEADLINE_CHILE = original_deadline


if __name__ == "__main__":
    unittest.main()
