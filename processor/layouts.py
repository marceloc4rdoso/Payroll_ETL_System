"""
Mapeamento de layouts (posição fixa) por "empresa/sistema".

Cada layout define "tipos de linha" e os campos (nome, início, fim, tipo e default).
As posições abaixo são baseadas nos arquivos em sample_txt/.

Convenção:
- start/end são baseados em índice 0 (Python). "end" é exclusivo (slice padrão).
- todos os campos são lidos como string no parsing; conversões numéricas são opcionais
  e ficam por conta do services.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


FieldType = Literal["string", "numeric", "date"]


@dataclass(frozen=True)
class FieldSpec:
    name: str
    start: int
    end: int
    type: FieldType = "string"
    default: Any | None = None


LayoutName = Literal[
    "FOLHAMATIC",
    "RMLABORE_DEFAULT",
    "RMLABORE_CUSTOM",
    "GENESIS",
    "CONTIMATIC",
]


LAYOUTS: dict[LayoutName, dict[str, list[FieldSpec]]] = {
    "GENESIS": {
        "header": [
            FieldSpec("record_type", 0, 1, "string"),
            FieldSpec("period_mmyyyy", 1, 7, "string"),
            FieldSpec("company_name", 7, 47, "string"),
            FieldSpec("company_cnpj", 47, 65, "string"),
            FieldSpec("employee_registration", 67, 73, "string"),
            FieldSpec("employee_name", 73, 113, "string"),
            FieldSpec("employee_role", 113, 173, "string"),
            FieldSpec("payment_date", 173, 183, "date"),
            FieldSpec("base_salary", 183, 199, "numeric"),
        ],
        "event": [
            FieldSpec("record_type", 0, 1, "string"),
            FieldSpec("event_code", 1, 5, "string"),
            FieldSpec("reference", 5, 17, "string", default=""),
            FieldSpec("description", 17, 55, "string", default=""),
            FieldSpec("amount", 45, 67, "numeric", default=""),
        ],
        "totals": [
            FieldSpec("record_type", 0, 1, "string"),
            FieldSpec("bank_code", 1, 6, "string", default=""),
            FieldSpec("account", 6, 30, "string", default=""),
            FieldSpec("gross", 30, 43, "numeric", default=""),
            FieldSpec("discounts", 43, 56, "numeric", default=""),
            FieldSpec("net", 56, 67, "numeric", default=""),
        ],
        "bases": [
            FieldSpec("record_type", 0, 1, "string"),
            FieldSpec("raw", 1, 250, "string", default=""),
        ],
    },
    "RMLABORE_DEFAULT": {
        "employee": [
            FieldSpec("employee_registration", 5, 12, "string", default=""),
            FieldSpec("employee_name", 14, 70, "string", default=""),
        ],
        "event": [
            FieldSpec("event_code", 0, 3, "string"),
            FieldSpec("description", 4, 34, "string", default=""),
            FieldSpec("reference", 34, 42, "string", default=""),
            FieldSpec("amount", 42, 54, "numeric", default=""),
            FieldSpec("sign", 54, 55, "string", default=""),
        ],
        "header": [
            FieldSpec("company_name", 1, 40, "string", default=""),
            FieldSpec("period_label", 40, 67, "string", default=""),
        ],
    },
    "RMLABORE_CUSTOM": {
        "header": [
            FieldSpec("company_name", 0, 60, "string", default=""),
            FieldSpec("period_label", 60, 75, "string", default=""),
        ],
        "employee": [
            FieldSpec("employee_registration", 0, 6, "string", default=""),
            FieldSpec("employee_name", 6, 45, "string", default=""),
            FieldSpec("employee_role", 45, 80, "string", default=""),
        ],
        "event": [
            FieldSpec("event_code", 1, 5, "string"),
            FieldSpec("description", 6, 47, "string", default=""),
            FieldSpec("quantity", 47, 53, "numeric", default=""),
            FieldSpec("hours", 54, 59, "string", default=""),
            FieldSpec("proventos", 60, 72, "numeric", default=""),
            FieldSpec("descontos", 72, 83, "numeric", default=""),
        ],
        "totals": [
            FieldSpec("proventos_total", 60, 72, "numeric", default=""),
            FieldSpec("descontos_total", 72, 85, "numeric", default=""),
        ],
    },
    "CONTIMATIC": {
        "header": [
            FieldSpec("company_name", 0, 60, "string", default=""),
            FieldSpec("period_label", 60, 80, "string", default=""),
        ],
        "employee": [
            FieldSpec("employee_registration", 0, 5, "string", default=""),
            FieldSpec("employee_name", 5, 35, "string", default=""),
            FieldSpec("employee_cbo", 35, 45, "string", default=""),
        ],
        "event": [
            FieldSpec("event_code", 0, 5, "string", default=""),
            FieldSpec("description", 5, 32, "string", default=""),
            FieldSpec("rate", 32, 42, "numeric", default=""),
            FieldSpec("proventos", 42, 57, "numeric", default=""),
            FieldSpec("descontos", 57, 70, "numeric", default=""),
        ],
    },
    "FOLHAMATIC": {
        "header": [
            FieldSpec("company_code_and_name", 0, 80, "string", default=""),
            FieldSpec("title", 80, 140, "string", default=""),
        ],
        "employee": [
            FieldSpec("employee_registration", 0, 15, "string", default=""),
            FieldSpec("employee_name", 15, 60, "string", default=""),
            FieldSpec("employee_cbo", 60, 75, "string", default=""),
        ],
        "event": [
            FieldSpec("event_code", 0, 8, "string", default=""),
            FieldSpec("description", 8, 78, "string", default=""),
            FieldSpec("reference", 78, 95, "string", default=""),
            FieldSpec("proventos", 95, 112, "numeric", default=""),
            FieldSpec("descontos", 112, 140, "numeric", default=""),
        ],
    },
}


def get_layout(name: LayoutName) -> dict[str, list[FieldSpec]]:
    return LAYOUTS[name]

