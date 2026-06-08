from __future__ import annotations

import unittest

import database


class DatabaseUrlTest(unittest.TestCase):
    def test_normaliza_url_neon_para_pg8000(self) -> None:
        url = (
            "postgresql://user:pass@ep-demo-pooler.sa-east-1.aws.neon.tech/neondb"
            "?sslmode=require&channel_binding=require"
        )

        normalizada = database.normalize_postgres_url(url)

        self.assertEqual(normalizada, "postgresql+pg8000://user:pass@ep-demo-pooler.sa-east-1.aws.neon.tech/neondb")


if __name__ == "__main__":
    unittest.main()
