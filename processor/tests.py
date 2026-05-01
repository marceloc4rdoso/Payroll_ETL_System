from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
from django.test import SimpleTestCase

from processor.services import fold_dataframe, parse_file


class FixedWidthParsingTests(SimpleTestCase):
    def test_parse_genesis_has_rows_and_expected_columns(self):
        header = (
            "1"
            + "032026"
            + "ORION SA".ljust(40)
            + "61.082.863/0005-73".ljust(18)
            + "  "
            + "040424"
            + "JOSINO PEREIRA DA SILVA".ljust(40)
            + "100233-ADMINISTRATIVO - FILIAL".ljust(60)
            + "06/04/2026"
            + "    "
            + "2.249,820000".ljust(16)
        )
        event = (
            "2"
            + "0001"
            + "  30 dia".ljust(12)
            + "SALARIO".ljust(38)
            + " " * 8
            + "2.249,82".rjust(22)
        )

        with tempfile.TemporaryDirectory() as tmp:
            file_path = Path(tmp) / "genesis.txt"
            file_path.write_text("\n".join([header, event]), encoding="latin1")
            df = parse_file(file_path, "GENESIS")

        self.assertFalse(df.empty)
        self.assertIn("company_name", df.columns)
        self.assertIn("employee_name", df.columns)
        self.assertTrue(df["company_name"].iloc[0].strip().startswith("ORION"))

    def test_parse_rmlabore_custom_has_rows(self):
        header = "VILA BOA CONSTRUCOES E SERVICOS".ljust(60) + "Mar/2026".ljust(10)
        employee = "01516".ljust(5) + " ALINE DE KASSIA SILVA".ljust(40) + "ENCARREGADO ADMINISTRATIVO".ljust(35)
        event = " 0002 DIAS TRABALHADOS".ljust(47) + "30,00".ljust(6) + " " + "00:00".ljust(5) + " " + "3.685,55".rjust(12)

        with tempfile.TemporaryDirectory() as tmp:
            file_path = Path(tmp) / "rmlabore_custom.txt"
            file_path.write_text("\n".join([header, employee, event]), encoding="latin1")
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
