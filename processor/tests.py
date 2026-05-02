from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
from django.test import SimpleTestCase

from processor.layout_builder import parse_with_payroll_layout_spec_v2
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


class PayrollLayoutV2ParsingTests(SimpleTestCase):
    def test_parse_payroll_layout_v2_records_and_padding(self):
        header_1 = "1" + "EMPRESA X".ljust(20) + "12345678000199" + "00001" + "JOAO DA SILVA".ljust(20)
        header_2 = "1" + "EMPRESA Y".ljust(20) + "98765432000100" + "00002" + "MARIA OLIVEIRA".ljust(20)
        text = "\n".join(
            [
                header_1,
                " 001SALARIO                 30  1000,00     ",
                " 002INSS                    00            100,00",
                "9BASES                    1000,00 900,00 900,00  90,00 1000,00 100,00 900,00",
                header_2,
                " 010SALARIO                 30  2000,00     ",
                "9BASES                    2000,00 1800,00 1800,00 180,00 2000,00 200,00 1800,00",
            ]
        )

        spec = {
            "version": 2,
            "mode": "payroll_record",
            "record_marker": {"type": "regex", "pattern": r"^1"},
            "detail": {
                "start_line_offset": 1,
                "max_lines": 3,
                "pad_to_max": True,
                "index_format": "{base}{i}",
                "fields": [
                    {"name": "detail_cod", "start": 1, "end": 4, "enabled": True},
                    {"name": "detail_description", "start": 4, "end": 30, "enabled": True},
                ],
            },
            "head": {
                "fields": [
                    {"name": "head_company", "start": 1, "end": 21, "enabled": True, "line_offset": 0},
                    {"name": "head_cnpj", "start": 21, "end": 35, "enabled": True, "line_offset": 0},
                ]
            },
            "bottom": {
                "fields": [
                    {"name": "bottom_salarybase", "start": 10, "end": 17, "enabled": True, "line_offset": 3},
                ]
                ,
                "marker": {"type": "regex", "pattern": r"^9"}
            },
        }

        rows = parse_with_payroll_layout_spec_v2(text, spec)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["head_company"].strip(), "EMPRESA X")
        self.assertEqual(rows[0]["head_cnpj"], "12345678000199")
        self.assertEqual(rows[0]["detail_cod1"], "001")
        self.assertEqual(rows[0]["detail_cod2"], "002")
        self.assertIn("detail_cod3", rows[0])
        self.assertEqual(rows[0]["detail_cod3"], "")
