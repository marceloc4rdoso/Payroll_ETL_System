from __future__ import annotations

import hashlib
import re
import csv
import io
import unicodedata
from pathlib import Path


def sha256_of_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_of_uploaded_file(uploaded_file) -> str:
    h = hashlib.sha256()
    for chunk in uploaded_file.chunks():
        h.update(chunk)
    return h.hexdigest()


def generate_fixed_width_spec_from_sample_text(text: str) -> dict:
    lines = [l.rstrip("\n\r") for l in text.splitlines() if l.strip()]
    if not lines:
        raise ValueError("Arquivo modelo vazio.")

    sample_line = max(lines, key=len)
    sample_line = re.sub(r"[\x00-\x1F]", "", sample_line)

    segments = []
    for m in re.finditer(r"\S+", sample_line):
        segments.append((m.start(), m.end()))

    if not segments:
        raise ValueError("Não foi possível identificar colunas no arquivo modelo.")

    starts = [s for s, _ in segments]
    ends = [e for _, e in segments]

    columns = []
    for i, (s, e) in enumerate(zip(starts, ends), start=1):
        columns.append({"name": f"col_{i:02d}", "start": int(s), "end": int(e), "type": "string"})

    return {
        "mode": "fixed_width",
        "based_on": "whitespace_runs",
        "sample_line_length": len(sample_line),
        "columns": columns,
    }


def parse_with_fixed_width_spec(text: str, spec: dict) -> list[dict[str, str]]:
    cols = spec.get("columns") or []
    if not cols:
        raise ValueError("layout_spec inválido: sem colunas.")

    rows = []
    for raw in text.splitlines():
        line = raw.rstrip("\n\r")
        if not line.strip():
            continue
        row = {}
        for c in cols:
            start = int(c["start"])
            end = int(c["end"])
            value = line[start:end] if start < len(line) else ""
            row[c["name"]] = value.strip()
        row["raw_line"] = line
        rows.append(row)
    return rows


DEFAULT_PAYROLL_FIELDS_V2 = {
    "head": [
        "head_competence",
        "head_company",
        "head_cnpj",
        "head_idemploye",
        "head_nameemploye",
    ],
    "detail": [
        "detail_cod",
        "detail_description",
        "detail_ref",
        "detail_hours",
        "detail_credit",
        "detail_debit",
    ],
    "bottom": [
        "bottom_salarybase",
        "bottom_baseinss",
        "bottom_basefgts",
        "bottom_fgtsmonth",
        "bottom_totalcredit",
        "bottom_totaldebit",
        "bottom_totalliquid",
    ],
}


def generate_payroll_layout_spec_v2_from_sample_text(text: str) -> dict:
    lines = [l.rstrip("\n\r") for l in text.splitlines() if l.strip()]
    if not lines:
        raise ValueError("Arquivo modelo vazio.")

    sample_line = max(lines, key=len)
    sample_line = re.sub(r"[\x00-\x1F]", "", sample_line)

    segments = [(m.start(), m.end()) for m in re.finditer(r"\S+", sample_line)]

    detail_positions = []
    if len(segments) >= len(DEFAULT_PAYROLL_FIELDS_V2["detail"]):
        for name, (s, e) in zip(DEFAULT_PAYROLL_FIELDS_V2["detail"], segments[: len(DEFAULT_PAYROLL_FIELDS_V2["detail"])]):
            detail_positions.append({"name": name, "start": int(s), "end": int(e), "enabled": True})
    else:
        detail_positions = [{"name": name, "start": 0, "end": 0, "enabled": True} for name in DEFAULT_PAYROLL_FIELDS_V2["detail"]]

    def _mk(fields: list[str]) -> list[dict]:
        return [{"name": n, "start": 0, "end": 0, "enabled": True, "line_offset": 0} for n in fields]

    return {
        "version": 2,
        "mode": "payroll_record",
        "encoding": "latin1",
        "record_marker": {"type": "regex", "pattern": r"^\s*1"},
        "detail": {
            "start_line_offset": 1,
            "max_lines": 0,
            "pad_to_max": False,
            "index_format": "{base}{i}",
            "fields": detail_positions,
        },
        "head": {"fields": _mk(DEFAULT_PAYROLL_FIELDS_V2["head"])},
        "bottom": {
            "fields": _mk(DEFAULT_PAYROLL_FIELDS_V2["bottom"]),
            "marker": {"type": "regex", "pattern": ""},
            "base_line": "bottom",
        },
    }


def parse_with_payroll_layout_spec_v2(text: str, spec: dict) -> list[dict[str, str]]:
    if (spec or {}).get("version") != 2 or spec.get("mode") != "payroll_record":
        raise ValueError("layout_spec inválido: esperado version=2, mode=payroll_record.")

    marker = (spec.get("record_marker") or {})
    if marker.get("type") != "regex" or not marker.get("pattern"):
        raise ValueError("layout_spec inválido: record_marker deve ser regex com pattern.")
    marker_re = re.compile(str(marker["pattern"]))

    raw_lines = [l.rstrip("\n\r") for l in text.splitlines()]

    start_indices: list[int] = []
    for i, line in enumerate(raw_lines):
        if marker_re.search(line):
            start_indices.append(i)

    if not start_indices:
        raise ValueError("Nenhum holerite encontrado: marcador não encontrado no arquivo.")

    head_fields = (spec.get("head") or {}).get("fields") or []
    bottom_spec = spec.get("bottom") or {}
    bottom_fields = bottom_spec.get("fields") or []
    bottom_marker = bottom_spec.get("marker") or {}
    bottom_marker_re = None
    if bottom_marker.get("type") == "regex" and str(bottom_marker.get("pattern") or "").strip():
        bottom_marker_re = re.compile(str(bottom_marker["pattern"]))
    bottom_start_offset = bottom_spec.get("start_line_offset")
    bottom_start_offset = int(bottom_start_offset) if bottom_start_offset is not None else None
    bottom_base_line = str(bottom_spec.get("base_line") or "record").strip().lower()
    detail_spec = spec.get("detail") or {}
    detail_fields = detail_spec.get("fields") or []
    detail_start = int(detail_spec.get("start_line_offset") or 0)
    max_detail_lines = int(detail_spec.get("max_lines") or 0) or 0
    pad_to_max = bool(detail_spec.get("pad_to_max", True))
    index_format = str(detail_spec.get("index_format") or "{base}{i}")

    def _slice(line: str, start: int, end: int) -> str:
        if start < 0 or end < 0:
            return ""
        if end <= start:
            return ""
        if start >= len(line):
            return ""
        return line[start:min(end, len(line))].strip()

    def _read_fields(record_lines: list[str], fields: list[dict]) -> dict[str, str]:
        out: dict[str, str] = {}
        for f in fields:
            if not f or not f.get("enabled", True):
                continue
            name = str(f.get("name") or "").strip()
            if not name:
                continue
            start = int(f.get("start") or 0)
            end = int(f.get("end") or 0)
            line_offset = int(f.get("line_offset") or 0)
            line = record_lines[line_offset] if 0 <= line_offset < len(record_lines) else ""
            out[name] = _slice(line, start, end)
        return out

    rows: list[dict[str, str]] = []
    for idx, start_idx in enumerate(start_indices):
        end_idx = start_indices[idx + 1] if idx + 1 < len(start_indices) else len(raw_lines)
        record_lines = raw_lines[start_idx:end_idx]

        bottom_idx = len(record_lines)
        if bottom_marker_re:
            for j, ln in enumerate(record_lines):
                if bottom_marker_re.search(ln):
                    bottom_idx = j
                    break
        elif bottom_start_offset is not None:
            bottom_idx = min(max(bottom_start_offset, 0), len(record_lines))

        row: dict[str, str] = {}
        row.update(_read_fields(record_lines, head_fields))
        if bottom_base_line == "bottom":
            bottom_lines = record_lines[bottom_idx:] if bottom_idx < len(record_lines) else []
            row.update(_read_fields(bottom_lines, bottom_fields))
        else:
            row.update(_read_fields(record_lines, bottom_fields))

        detail_lines_raw = record_lines[detail_start:bottom_idx] if detail_start < len(record_lines) else []
        if max_detail_lines > 0:
            detail_lines = detail_lines_raw[:max_detail_lines]
            if pad_to_max and len(detail_lines) < max_detail_lines:
                detail_lines = detail_lines + ([""] * (max_detail_lines - len(detail_lines)))
        else:
            detail_lines = detail_lines_raw

        for i_line, dline in enumerate(detail_lines, start=1):
            for f in detail_fields:
                if not f or not f.get("enabled", True):
                    continue
                base = str(f.get("name") or "").strip()
                if not base:
                    continue
                start = int(f.get("start") or 0)
                end = int(f.get("end") or 0)
                try:
                    key = index_format.format(base=base, i=i_line)
                except Exception:
                    key = f"{base}{i_line}"
                row[key] = _slice(dline, start, end)

        row["record_index"] = str(idx + 1)
        rows.append(row)

    return rows


def infer_payroll_layout_spec_v2_from_raw_and_expected_csv(raw_text: str, expected_csv_text: str) -> dict:
    def _norm(s: str) -> str:
        s = (s or "").replace("�", "")
        s = unicodedata.normalize("NFKD", s)
        s = "".join([c for c in s if not unicodedata.combining(c)])
        return s.upper()

    def _norm_with_map(s: str) -> tuple[str, list[int]]:
        out = []
        mapping: list[int] = []
        for i, ch in enumerate(s or ""):
            if ch == "�":
                continue
            decomp = unicodedata.normalize("NFKD", ch)
            decomp = "".join([c for c in decomp if not unicodedata.combining(c)])
            decomp = decomp.upper()
            for c in decomp:
                out.append(c)
                mapping.append(i)
        return "".join(out), mapping

    def _find_span(haystack: str, needle: str) -> tuple[int, int] | None:
        if not haystack or not needle:
            return None
        direct = haystack.find(needle)
        if direct >= 0:
            return direct, direct + len(needle)
        nh, mapping = _norm_with_map(haystack)
        nn = _norm(needle)
        if not nn:
            return None
        pos = nh.find(nn)
        if pos < 0:
            return None
        start = mapping[pos]
        end = mapping[pos + len(nn) - 1] + 1
        return start, end

    reader = csv.reader(io.StringIO(expected_csv_text), delimiter=";", quotechar='"')
    rows = list(reader)
    if len(rows) < 2:
        raise ValueError("CSV esperado deve conter header e pelo menos 1 linha de dados.")
    header = [h.strip().strip('"').strip("'") for h in rows[0]]
    first = rows[1]
    data = {h: (first[i] if i < len(first) else "") for i, h in enumerate(header)}

    head_cols = [h for h in header if h.startswith("head_")]
    bottom_cols = [h for h in header if h.startswith("bottom_")]
    detail_cols = [h for h in header if h.startswith("detail_")]

    max_i = 0
    detail_bases: list[str] = []
    for c in detail_cols:
        m = re.match(r"^(detail_[a-zA-Z_]+)(\d+)$", c)
        if not m:
            continue
        base, idx = m.group(1), int(m.group(2))
        max_i = max(max_i, idx)
        if base not in detail_bases:
            detail_bases.append(base)

    company = data.get("head_company", "").strip()
    competence = data.get("head_competence", "").strip()
    if company and competence:
        marker_pattern = r"^" + re.escape(company) + r".*" + re.escape(competence) + r"\s*$"
    elif company:
        marker_pattern = r"^" + re.escape(company)
    else:
        marker_pattern = r"^\s*\S"

    marker_re = re.compile(marker_pattern)
    raw_lines = [l.rstrip("\n\r") for l in raw_text.splitlines()]
    starts = [i for i, ln in enumerate(raw_lines) if marker_re.search(ln)]
    if not starts:
        starts = [0]
    start0 = starts[0]
    end0 = starts[1] if len(starts) > 1 else len(raw_lines)
    record_lines = raw_lines[start0:end0]

    bottom_marker_pattern = r"^PAR.*FOLHA"
    for ln in record_lines:
        if "FOLHA" in _norm(ln) and "PAG" in _norm(ln):
            bottom_marker_pattern = r"^" + re.escape(ln.strip().split("  ")[0].strip()) + r".*FOLHA"
            break

    bottom_marker_re = re.compile(bottom_marker_pattern, flags=re.IGNORECASE)
    bottom_idx = len(record_lines)
    for j, ln in enumerate(record_lines):
        if bottom_marker_re.search(ln) or bottom_marker_re.search(_norm(ln)):
            bottom_idx = j
            break

    head_fields: list[dict] = []
    for col in head_cols:
        val = data.get(col, "")
        if not val:
            continue
        found = None
        for li, ln in enumerate(record_lines):
            span = _find_span(ln, val)
            if span:
                found = (li, span[0], span[1])
                break
        if found:
            li, s, e = found
            head_fields.append({"name": col, "start": s, "end": e, "enabled": True, "line_offset": li})
        else:
            head_fields.append({"name": col, "start": 0, "end": 0, "enabled": True, "line_offset": 0})

    detail_fields: list[dict] = [{"name": base, "start": 0, "end": 0, "enabled": True} for base in detail_bases]
    detail_start_line_offset = 1
    if max_i > 0 and "detail_cod1" in data and data.get("detail_cod1"):
        code1 = data.get("detail_cod1", "")
        for li, ln in enumerate(record_lines):
            if _find_span(ln, code1):
                detail_start_line_offset = li
                break

    base_pos: dict[str, tuple[int, int]] = {}
    detail_line_by_i: dict[int, int] = {}
    for i in range(1, max_i + 1):
        code = data.get(f"detail_cod{i}", "")
        if not code:
            continue
        for li in range(detail_start_line_offset, bottom_idx):
            if _find_span(record_lines[li], code):
                detail_line_by_i[i] = li
                break

    for base in detail_bases:
        for i, li in detail_line_by_i.items():
            col = f"{base}{i}"
            val = data.get(col, "")
            if not val:
                continue
            span = _find_span(record_lines[li], val)
            if not span:
                continue
            if base not in base_pos:
                base_pos[base] = span
            else:
                s0, e0 = base_pos[base]
                base_pos[base] = (min(s0, span[0]), max(e0, span[1]))

    for f in detail_fields:
        base = f["name"]
        if base in base_pos:
            f["start"], f["end"] = base_pos[base]

    bottom_base_line = "bottom"
    bottom_fields: list[dict] = []
    for col in bottom_cols:
        val = data.get(col, "")
        if not val:
            continue
        found = None
        for li in range(bottom_idx, len(record_lines)):
            span = _find_span(record_lines[li], val)
            if span:
                found = (li, span[0], span[1])
                break
        if found:
            li, s, e = found
            bottom_fields.append(
                {"name": col, "start": s, "end": e, "enabled": True, "line_offset": max(li - bottom_idx, 0)}
            )
        else:
            bottom_fields.append({"name": col, "start": 0, "end": 0, "enabled": True, "line_offset": 0})

    return {
        "version": 2,
        "mode": "payroll_record",
        "encoding": "latin1",
        "record_marker": {"type": "regex", "pattern": marker_pattern},
        "detail": {
            "start_line_offset": int(detail_start_line_offset),
            "max_lines": int(max_i or 35),
            "pad_to_max": True,
            "index_format": "{base}{i}",
            "fields": detail_fields,
        },
        "head": {"fields": head_fields},
        "bottom": {"fields": bottom_fields, "marker": {"type": "regex", "pattern": bottom_marker_pattern}, "base_line": bottom_base_line},
    }
