from __future__ import annotations

from pathlib import Path

import pandas as pd
from django.test import SimpleTestCase

from processor.services import fold_dataframe, parse_file


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DIR = PROJECT_ROOT / "sample_txt"


class FixedWidthParsingTests(SimpleTestCase):
    def test_parse_genesis_has_rows_and_expected_columns(self):
        file_path = SAMPLE_DIR / "Cliente_Orion_Arquivo_Sistema_Genesis.txt"
        df = parse_file(file_path, "GENESIS")

        self.assertFalse(df.empty)
        self.assertIn("company_name", df.columns)
        self.assertIn("employee_name", df.columns)
        self.assertTrue(df["company_name"].iloc[0].strip().startswith("ORION"))

    def test_parse_rmlabore_custom_has_rows(self):
        file_path = SAMPLE_DIR / "Cliente_VilaBoa_Arquivo_Sistema_RMLaboreCustom.txt"
        df = parse_file(file_path, "RMLABORE_CUSTOM")
        self.assertFalse(df.empty)
        self.assertIn("event_code", df.columns)

    def test_fold_logic(self):
        df = pd.DataFrame(
            [{"a": "1", "b": "x"}, {"a": "2", "b": "y"}, {"a": "3", "b": "z"}],
            dtype="string",
        )
        folded = fold_dataframe(df)
        self.assertEqual(len(folded), 2)
        self.assertIn("a_A", folded.columns)
        self.assertIn("a_B", folded.columns)
