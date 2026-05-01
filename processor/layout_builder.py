from __future__ import annotations

import hashlib
import re
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

