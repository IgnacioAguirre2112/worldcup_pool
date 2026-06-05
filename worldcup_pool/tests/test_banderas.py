from __future__ import annotations

import unittest

from ui import flag_data_uri


class BanderasTest(unittest.TestCase):
    def test_bandera_rd_de_congo_resuelve(self) -> None:
        self.assertTrue(flag_data_uri("RD de Congo"))

    def test_bandera_escocia_resuelve(self) -> None:
        self.assertTrue(flag_data_uri("Escocia"))

    def test_bandera_suecia_resuelve(self) -> None:
        self.assertTrue(flag_data_uri("Suecia"))

    def test_bandera_chile_resuelve(self) -> None:
        self.assertTrue(flag_data_uri("Chile"))


if __name__ == "__main__":
    unittest.main()
