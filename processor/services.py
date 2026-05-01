from __future__ import annotations

import math
import re
from pathlib import Path

import pandas as pd
from django.core.files import File
from django.utils import timezone

from processor.layouts import LayoutName, get_layout
from processor.models import Upload


DEFAULT_TXT_ENCODING = "latin1"


def _safe_slice(line: str, start: int, end: int) -> str:
    if start >= len(line):
        return ""
    return line[start:min(end, len(line))]


def _extract_fields(line: str, specs: list[FieldSpec]) -> dict[str, str]:
    data: dict[str, str] = {}
    for spec in specs:
        raw = _safe_slice(line, spec.start, spec.end)
        value = raw.rstrip("\n\r")
        value = value if value != "" else ("" if spec.default is None else str(spec.default))
        data[spec.name] = value.strip()
    return data


def _cleanup_control_chars(line: str) -> str:
    return re.sub(r"[\x00-\x1F]", "", line)


def _read_lines(file_path: str | Path, encoding: str = DEFAULT_TXT_ENCODING) -> list[str]:
    return Path(file_path).read_text(encoding=encoding, errors="replace").splitlines()


def parse_genesis(file_path: str | Path) -> pd.DataFrame:
    layout = get_layout("GENESIS")
    lines = _read_lines(file_path)

    header_ctx: dict[str, str] = {}
    rows: list[dict[str, str]] = []

    for line in lines:
        if not line:
            continue
        record_type = line[0:1]
        if record_type == "1":
            header_ctx = _extract_fields(line, layout["header"])
            continue
        if record_type == "2":
            event = _extract_fields(line, layout["event"])
            rows.append(
                {
                    "layout_type": "GENESIS",
                    **{k: header_ctx.get(k, "") for k in ("period_mmyyyy", "company_name", "company_cnpj", "employee_registration", "employee_name", "employee_role", "payment_date")},
                    **event,
                    "raw_line": line,
                }
            )

    return pd.DataFrame(rows, dtype="string")


def parse_rmlabore_default(file_path: str | Path) -> pd.DataFrame:
    layout = get_layout("RMLABORE_DEFAULT")
    lines = _read_lines(file_path)

    company_name = ""
    period_label = ""
    employee_registration = ""
    employee_name = ""

    rows: list[dict[str, str]] = []

    employee_re = re.compile(r"^\s+\d{2,5}-\d")
    event_re = re.compile(r"^\d{3}\s")

    for raw_line in lines:
        line = raw_line.rstrip("\n\r")
        if not line.strip():
            continue

        if "Mensal" in line and "/" in line and not company_name:
            header = _extract_fields(line, layout["header"])
            company_name = header.get("company_name", "")
            period_label = header.get("period_label", "")
            continue

        if employee_re.match(line):
            emp = _extract_fields(line, layout["employee"])
            employee_registration = emp.get("employee_registration", "")
            employee_name = emp.get("employee_name", "")
            continue

        if event_re.match(line):
            ev = _extract_fields(line, layout["event"])
            sign = (ev.get("sign") or "+").strip()
            amount = (ev.get("amount") or "").strip()
            rows.append(
                {
                    "layout_type": "RMLABORE_DEFAULT",
                    "company_name": company_name.strip(),
                    "period_label": period_label.strip(),
                    "employee_registration": employee_registration.strip(),
                    "employee_name": employee_name.strip(),
                    "event_code": (ev.get("event_code") or "").strip(),
                    "description": (ev.get("description") or "").strip(),
                    "reference": (ev.get("reference") or "").strip(),
                    "amount": amount,
                    "sign": sign,
                    "raw_line": line,
                }
            )

    return pd.DataFrame(rows, dtype="string")


def parse_rmlabore_custom(file_path: str | Path) -> pd.DataFrame:
    layout = get_layout("RMLABORE_CUSTOM")
    lines = _read_lines(file_path)

    company_name = ""
    period_label = ""
    employee_registration = ""
    employee_name = ""
    employee_role = ""

    rows: list[dict[str, str]] = []

    header_re = re.compile(r".+\s+\w{3}/\d{4}\s*$")
    employee_re = re.compile(r"^\d{4,6}\s")
    event_re = re.compile(r"^\s\d{4}\s")

    for raw_line in lines:
        line = raw_line.rstrip("\n\r")
        if not line.strip():
            continue

        if not company_name and header_re.match(line):
            header = _extract_fields(line, layout["header"])
            company_name = header.get("company_name", "")
            period_label = header.get("period_label", "")
            continue

        if employee_re.match(line) and " " in line:
            employee_registration = line[0:5].strip()
            employee_name = line[5:45].strip()
            employee_role = line[45:80].strip()
            continue

        if event_re.match(line):
            ev = _extract_fields(line, layout["event"])
            proventos = (ev.get("proventos") or "").strip()
            descontos = (ev.get("descontos") or "").strip()
            amount = proventos if proventos else descontos
            sign = "+" if proventos else "-"
            rows.append(
                {
                    "layout_type": "RMLABORE_CUSTOM",
                    "company_name": company_name.strip(),
                    "period_label": period_label.strip(),
                    "employee_registration": employee_registration.strip(),
                    "employee_name": employee_name.strip(),
                    "employee_role": employee_role.strip(),
                    "event_code": (ev.get("event_code") or "").strip(),
                    "description": (ev.get("description") or "").strip(),
                    "quantity": (ev.get("quantity") or "").strip(),
                    "hours": (ev.get("hours") or "").strip(),
                    "amount": amount,
                    "sign": sign,
                    "raw_line": line,
                }
            )

    return pd.DataFrame(rows, dtype="string")


def parse_contimatic(file_path: str | Path) -> pd.DataFrame:
    lines = [_cleanup_control_chars(l) for l in _read_lines(file_path)]

    company_name = lines[0].strip() if lines else ""
    period_label = ""
    employee_registration = ""
    employee_name = ""

    rows: list[dict[str, str]] = []

    employee_re = re.compile(r"^\d\s{2,}")
    event_re = re.compile(r"^\d{1,4}\s+.+R\$\s")

    for raw_line in lines:
        line = raw_line.rstrip("\n\r")
        if not line.strip():
            continue

        if not period_label and re.search(r"\b[A-Z]{3,}/\d{4}\b", line):
            period_label = re.search(r"\b[A-Z]{3,}/\d{4}\b", line).group(0)  # type: ignore[union-attr]

        if employee_re.match(line) and "ADMISS" not in line.upper() and "R$" not in line:
            employee_registration = line[0:5].strip()
            employee_name = line[5:35].strip()
            continue

        if event_re.match(line):
            event_code = line[0:5].strip()
            description = line[5:32].strip()
            numbers = re.findall(r"R\$\s*([\d\.,]+)", line)
            rate = numbers[0] if len(numbers) >= 1 else ""
            amount = numbers[-1] if len(numbers) >= 2 else (numbers[0] if numbers else "")
            rows.append(
                {
                    "layout_type": "CONTIMATIC",
                    "company_name": company_name,
                    "period_label": period_label,
                    "employee_registration": employee_registration,
                    "employee_name": employee_name,
                    "event_code": event_code,
                    "description": description,
                    "rate": rate,
                    "amount": amount,
                    "raw_line": line,
                }
            )

    return pd.DataFrame(rows, dtype="string")


def parse_folhamatic(file_path: str | Path) -> pd.DataFrame:
    lines = _read_lines(file_path)

    company_name = ""
    period_label = ""
    employee_registration = ""
    employee_name = ""
    employee_role = ""

    rows: list[dict[str, str]] = []

    header_re = re.compile(r"^\\s*\\d{3,4}-.+Demonstrativo", flags=re.IGNORECASE)
    period_re = re.compile(r"\\b\\d{2}/\\d{4}\\b")
    employee_re = re.compile(r"^\\s*\\d{1,6}\\s+\\S")
    event_re = re.compile(r"^\\s*\\d{1,4}\\s+\\S")

    for raw_line in lines:
        line = raw_line.rstrip("\n\r")
        if not line.strip():
            continue

        if header_re.match(line):
            company_name = line[0:60].strip()
            continue

        if not period_label:
            m = period_re.search(line)
            if m:
                period_label = m.group(0)

        if "Nome do Funcion" in line:
            continue

        if employee_re.match(line) and "Ev" not in line:
            employee_registration = line[0:15].strip()
            employee_name = line[15:60].strip()
            employee_role = ""
            continue

        if event_re.match(line) and "Total" not in line:
            event_code = line[0:8].strip()
            description = line[8:78].strip()
            reference = line[78:95].strip()
            proventos = line[95:112].strip()
            descontos = line[112:140].strip()
            amount = proventos if proventos else descontos
            sign = "+" if proventos else "-"
            rows.append(
                {
                    "layout_type": "FOLHAMATIC",
                    "company_name": company_name,
                    "period_label": period_label,
                    "employee_registration": employee_registration,
                    "employee_name": employee_name,
                    "employee_role": employee_role,
                    "event_code": event_code,
                    "description": description,
                    "reference": reference,
                    "amount": amount,
                    "sign": sign,
                    "raw_line": line,
                }
            )

    return pd.DataFrame(rows, dtype="string")


def parse_file(file_path: str | Path, layout_type: str) -> pd.DataFrame:
    if layout_type == "GENESIS":
        return parse_genesis(file_path)
    if layout_type == "RMLABORE_DEFAULT":
        return parse_rmlabore_default(file_path)
    if layout_type == "RMLABORE_CUSTOM":
        return parse_rmlabore_custom(file_path)
    if layout_type == "CONTIMATIC":
        return parse_contimatic(file_path)
    if layout_type == "FOLHAMATIC":
        return parse_folhamatic(file_path)
    from processor.layout_builder import parse_with_fixed_width_spec
    from processor.models import SourceSystem

    system = SourceSystem.objects.filter(code=layout_type).exclude(layout_spec=None).first()
    if not system:
        raise ValueError(f"Layout não suportado: {layout_type}")

    text = Path(file_path).read_text(encoding=DEFAULT_TXT_ENCODING, errors="replace")
    rows = parse_with_fixed_width_spec(text, system.layout_spec)
    for r in rows:
        r["layout_type"] = layout_type
        r["system_name"] = system.name
    return pd.DataFrame(rows, dtype="string")


def fold_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Implementa a "dobra" A/B:
    - divide o dataframe no meio (ceil)
    - renomeia colunas com sufixo _A e _B
    - concatena horizontalmente.
    """

    if df.empty:
        return df.copy()

    total = len(df)
    mid = int(math.ceil(total / 2))

    a = df.iloc[:mid].reset_index(drop=True)
    b = df.iloc[mid:].reset_index(drop=True)

    a = a.add_suffix("_A")
    b = b.add_suffix("_B")

    return pd.concat([a, b], axis=1)


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_semicolon_csv(df: pd.DataFrame, path: str | Path) -> None:
    path = Path(path)
    _ensure_parent(path)
    df.to_csv(path, sep=";", index=False, encoding="utf-8")


def _prepend_to_csv(new_df: pd.DataFrame, csv_path: Path) -> None:
    if not csv_path.exists():
        write_semicolon_csv(new_df, csv_path)
        return

    old_df = pd.read_csv(csv_path, sep=";", dtype="string", encoding="utf-8")
    merged = pd.concat([new_df, old_df], ignore_index=True)
    write_semicolon_csv(merged, csv_path)


def process_upload(upload: Upload) -> None:
    """
    Processa um Upload:
    - detecta layout via Empresa.layout_type
    - gera dataframe Web (1:1) e Impressão (dobra)
    - escreve base_web.csv (prepend) e base_impressao.csv (overwrite)
    - anexa os arquivos gerados nos FileFields do Upload.
    """

    layout_type = upload.empresa.source_system.code if upload.empresa.source_system else upload.empresa.layout_type
    upload.detected_layout_type = layout_type
    upload.save(update_fields=["detected_layout_type"])
    upload.mark_processing()

    try:
        df_web = parse_file(upload.original_file.path, layout_type)  # type: ignore[arg-type]
        df_print = fold_dataframe(df_web)

        dt = timezone.localdate()
        output_dir = Path(upload.original_file.storage.location) / "generated" / f"{dt:%Y-%m-%d}" / f"empresa_{upload.empresa_id}"
        web_path = output_dir / f"upload_{upload.pk}_web.csv"
        print_path = output_dir / f"upload_{upload.pk}_impressao.csv"

        base_web_path = Path(upload.original_file.storage.location) / "base_web.csv"
        base_print_path = Path(upload.original_file.storage.location) / "base_impressao.csv"

        write_semicolon_csv(df_web, web_path)
        write_semicolon_csv(df_print, print_path)
        _prepend_to_csv(df_web, base_web_path)
        write_semicolon_csv(df_print, base_print_path)

        storage_root = Path(upload.original_file.storage.location)
        web_rel = str(web_path.relative_to(storage_root))
        print_rel = str(print_path.relative_to(storage_root))

        with web_path.open("rb") as f:
            upload.web_csv.save(web_rel, File(f), save=False)
        with print_path.open("rb") as f:
            upload.print_csv.save(print_rel, File(f), save=False)

        upload.save(update_fields=["web_csv", "print_csv"])
        upload.mark_done(row_count=len(df_web))
    except Exception as exc:
        upload.mark_failed(str(exc))
        raise
