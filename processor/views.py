from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Count
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from processor.forms import LayoutFieldFormSet, LayoutMetaForm, SourceSystemForm, UploadForm
from processor.layout_builder import (
    generate_payroll_layout_spec_v2_from_sample_text,
    infer_payroll_layout_spec_v2_from_raw_and_expected_csv,
    parse_with_payroll_layout_spec_v2,
    sha256_of_uploaded_file,
)
from processor.models import Upload
from processor.models import SourceSystem
from processor.services import process_upload


def _get_restricted_empresa_id_for_user(user) -> int | None:
    if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
        return None
    vinculo = getattr(user, "empresa_vinculo", None)
    if vinculo and getattr(vinculo, "is_active", False) and getattr(vinculo.empresa, "is_active", False):
        return vinculo.empresa_id
    contato = getattr(user, "contato", None)
    if contato and getattr(contato, "is_active", False) and getattr(contato.empresa, "is_active", False):
        return contato.empresa_id
    return -1


@login_required
def dashboard_view(request: HttpRequest) -> HttpResponse:
    empresa_id = _get_restricted_empresa_id_for_user(request.user)
    uploads_qs = Upload.objects.all() if empresa_id is None else Upload.objects.filter(empresa_id=empresa_id)

    status_counts = dict(
        uploads_qs.values("status")
        .annotate(total=Count("id"))
        .values_list("status", "total")
    )

    total_uploads = uploads_qs.count()

    uploads_by_empresa = list(
        uploads_qs.values("empresa__name")
        .annotate(total=Count("id"))
        .order_by("-total", "empresa__name")
    )

    uploads_by_user = list(
        uploads_qs.values("uploaded_by__username")
        .annotate(total=Count("id"))
        .order_by("-total", "uploaded_by__username")
    )

    max_by_empresa = max([r["total"] for r in uploads_by_empresa], default=0)
    for r in uploads_by_empresa:
        r["pct"] = int(round((r["total"] / max_by_empresa) * 100)) if max_by_empresa else 0

    max_by_user = max([r["total"] for r in uploads_by_user], default=0)
    for r in uploads_by_user:
        r["pct"] = int(round((r["total"] / max_by_user) * 100)) if max_by_user else 0

    last_uploads = uploads_qs.select_related("empresa", "uploaded_by").order_by("-created_at")[:10]

    status_order = [
        ("DONE", "Concluídos", "#22c55e"),
        ("PROCESSING", "Processando", "#3b82f6"),
        ("PENDING", "Pendentes", "#f59e0b"),
        ("FAILED", "Falhas", "#ef4444"),
    ]

    segments = []
    cursor = 0.0
    for key, label, color in status_order:
        value = int(status_counts.get(key, 0) or 0)
        pct = (value / total_uploads * 100.0) if total_uploads else 0.0
        start = cursor
        end = cursor + pct
        segments.append(
            {
                "key": key,
                "label": label,
                "value": value,
                "color": color,
                "start": start,
                "end": end,
                "pct": pct,
            }
        )
        cursor = end

    if total_uploads == 0:
        conic = "conic-gradient(#e5e7eb 0% 100%)"
    else:
        parts = [f"{s['color']} {s['start']:.3f}% {s['end']:.3f}%" for s in segments if s["pct"] > 0]
        conic = "conic-gradient(" + ", ".join(parts) + ")"

    context = {
        "total_uploads": total_uploads,
        "status_counts": status_counts,
        "status_segments": segments,
        "status_conic": conic,
        "uploads_by_empresa": uploads_by_empresa,
        "uploads_by_user": uploads_by_user,
        "last_uploads": last_uploads,
    }
    return render(request, "processor/dashboard.html", context)


@login_required
def upload_view(request: HttpRequest) -> HttpResponse:
    empresa_id = _get_restricted_empresa_id_for_user(request.user)
    if empresa_id == -1:
        messages.error(request, "Seu usuário não está vinculado a uma empresa ativa. Contate o administrador.")
        return redirect("processor:dashboard")

    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            empresa = form.cleaned_data["empresa"]
            arquivo = form.cleaned_data["arquivo"]

            upload = Upload.objects.create(
                empresa=empresa,
                uploaded_by=request.user,
                original_file=arquivo,
            )

            try:
                process_upload(upload)
                messages.success(request, "Arquivo processado com sucesso.")
            except Exception:
                messages.error(request, "Falha ao processar o arquivo. Verifique o histórico.")

            return redirect("processor:uploads")
    else:
        form = UploadForm(user=request.user)

    return render(request, "processor/upload.html", {"form": form})


@login_required
def uploads_list_view(request: HttpRequest) -> HttpResponse:
    empresa_id = _get_restricted_empresa_id_for_user(request.user)
    uploads_qs = Upload.objects.all() if empresa_id is None else Upload.objects.filter(empresa_id=empresa_id)
    uploads = uploads_qs.select_related("empresa", "uploaded_by").order_by("-created_at")[:50]
    return render(request, "processor/uploads_list.html", {"uploads": uploads})


class StaffOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        return bool(self.request.user.is_staff or self.request.user.is_superuser)


class SourceSystemListView(StaffOnlyMixin, LoginRequiredMixin, ListView):
    model = SourceSystem
    template_name = "processor/system_list.html"
    context_object_name = "systems"
    paginate_by = 50


class SourceSystemCreateView(StaffOnlyMixin, LoginRequiredMixin, CreateView):
    model = SourceSystem
    form_class = SourceSystemForm
    template_name = "processor/system_form.html"
    success_url = reverse_lazy("processor:system_list")

    def form_valid(self, form):
        sample_file = form.cleaned_data.get("sample_file")
        if sample_file:
            sha = sha256_of_uploaded_file(sample_file)
            existing = SourceSystem.objects.filter(sample_sha256=sha).exclude(layout_spec=None).first()
            if existing:
                form.add_error("sample_file", f"Este arquivo modelo já está associado ao sistema: {existing.name} ({existing.code}).")
                return self.form_invalid(form)
            form.instance.sample_sha256 = sha
        response = super().form_valid(form)
        if sample_file:
            self.object.sample_file.open("rb")
            try:
                text = self.object.sample_file.read().decode("latin1", errors="replace")
            finally:
                self.object.sample_file.close()
            spec = generate_payroll_layout_spec_v2_from_sample_text(text)
            self.object.layout_spec = spec
            self.object.generated_at = timezone.now()
            self.object.save(update_fields=["layout_spec", "generated_at", "sample_sha256"])
        return response


class SourceSystemUpdateView(StaffOnlyMixin, LoginRequiredMixin, UpdateView):
    model = SourceSystem
    form_class = SourceSystemForm
    template_name = "processor/system_form.html"
    success_url = reverse_lazy("processor:system_list")

    def form_valid(self, form):
        sample_file = form.cleaned_data.get("sample_file")
        if sample_file:
            sha = sha256_of_uploaded_file(sample_file)
            existing = SourceSystem.objects.filter(sample_sha256=sha).exclude(pk=self.object.pk).exclude(layout_spec=None).first()
            if existing:
                form.add_error("sample_file", f"Este arquivo modelo já está associado ao sistema: {existing.name} ({existing.code}).")
                return self.form_invalid(form)
            form.instance.sample_sha256 = sha
        response = super().form_valid(form)
        if sample_file:
            self.object.sample_file.open("rb")
            try:
                text = self.object.sample_file.read().decode("latin1", errors="replace")
            finally:
                self.object.sample_file.close()
            spec = generate_payroll_layout_spec_v2_from_sample_text(text)
            self.object.layout_spec = spec
            self.object.generated_at = timezone.now()
            self.object.save(update_fields=["layout_spec", "generated_at", "sample_sha256"])
        return response


class SourceSystemDeleteView(StaffOnlyMixin, LoginRequiredMixin, DeleteView):
    model = SourceSystem
    template_name = "processor/system_confirm_delete.html"
    success_url = reverse_lazy("processor:system_list")


class SourceSystemLayoutDesignerView(StaffOnlyMixin, LoginRequiredMixin, View):
    template_name = "processor/system_layout.html"

    @staticmethod
    def _to_spec_start_end(start_ui: int | None, end_ui: int | None) -> tuple[int, int]:
        if start_ui is None or end_ui is None:
            return 0, 0
        start_ui = int(start_ui)
        end_ui = int(end_ui)
        if start_ui <= 0 or end_ui <= 0:
            return 0, 0
        start = max(start_ui - 1, 0)
        end = end_ui
        if end <= start:
            return 0, 0
        return start, end

    @staticmethod
    def _to_spec_line_offset(line_ui: int | None) -> int:
        if line_ui is None:
            return 0
        line_ui = int(line_ui)
        if line_ui <= 0:
            return 0
        return max(line_ui - 1, 0)

    @staticmethod
    def _to_ui_start_end(field: dict) -> dict:
        start = int(field.get("start") or 0)
        end = int(field.get("end") or 0)
        if end <= 0:
            field["start"] = None
            field["end"] = None
            return field
        field["start"] = start + 1
        field["end"] = end
        return field

    @staticmethod
    def _to_ui_line_offset(field: dict) -> dict:
        if int(field.get("end") or 0) <= 0:
            field["line_offset"] = None
            return field
        line_offset = int(field.get("line_offset") or 0)
        field["line_offset"] = line_offset + 1
        return field

    def _spec_to_form_initial(self, spec: dict) -> tuple[dict, list[dict], list[dict], list[dict]]:
        meta_initial = {
            "record_marker_regex": ((spec.get("record_marker") or {}).get("pattern") or r"^\s*1"),
            "detail_start_line_offset": int((spec.get("detail") or {}).get("start_line_offset") or 0) + 1,
            "detail_max_lines": int((spec.get("detail") or {}).get("max_lines") or 0),
            "detail_pad_to_max": bool((spec.get("detail") or {}).get("pad_to_max", True)),
            "detail_index_format": (spec.get("detail") or {}).get("index_format") or "{base}{i}",
            "bottom_marker_regex": ((spec.get("bottom") or {}).get("marker") or {}).get("pattern") or "",
            "bottom_start_line_offset": (
                (int((spec.get("bottom") or {}).get("start_line_offset")) + 1)
                if (spec.get("bottom") or {}).get("start_line_offset") is not None
                else None
            ),
            "bottom_base_line": (spec.get("bottom") or {}).get("base_line") or "bottom",
        }

        head_fields = [dict(f) for f in ((spec.get("head") or {}).get("fields") or [])]
        detail_fields = [dict(f) for f in ((spec.get("detail") or {}).get("fields") or [])]
        bottom_fields = [dict(f) for f in ((spec.get("bottom") or {}).get("fields") or [])]

        for f in head_fields:
            self._to_ui_start_end(f)
            self._to_ui_line_offset(f)
        for f in detail_fields:
            self._to_ui_start_end(f)
        for f in bottom_fields:
            self._to_ui_start_end(f)
            self._to_ui_line_offset(f)

        return meta_initial, head_fields, detail_fields, bottom_fields

    def _samples_dir(self):
        from pathlib import Path

        return Path(__file__).resolve().parent / ".sample_txt"

    def _available_samples(self) -> list[dict[str, str]]:
        d = self._samples_dir()
        if not d.exists():
            return []
        files = sorted([p.name for p in d.glob("*_raw_*.txt")])
        files += sorted([p.name for p in d.glob("*_raw_after_insertline_*.txt") if p.name not in files])
        return [{"value": name, "label": name} for name in files]

    def _read_sample_from_dir(self, filename: str) -> str:
        from pathlib import Path

        name = (filename or "").strip()
        if not name:
            return ""
        p = Path(self._samples_dir()) / name
        if not p.exists():
            return ""
        return p.read_text(encoding="latin1", errors="replace")

    def _expected_csv_headers(self, raw_filename: str) -> list[str]:
        from pathlib import Path

        name = (raw_filename or "").strip()
        if not name:
            return []
        expected = name.replace("_raw_after_insertline_", "_csv_").replace("_raw_", "_csv_")
        expected = expected.rsplit(".", 1)[0] + ".csv"
        p = Path(self._samples_dir()) / expected
        if not p.exists():
            return []
        header_line = p.read_text(encoding="utf-8", errors="replace").splitlines()[0:1]
        if not header_line:
            return []
        raw = header_line[0]
        cols = [c.strip().strip('"').strip("'") for c in raw.split(";")]
        return [c for c in cols if c]

    def _expected_csv_text(self, raw_filename: str) -> str:
        from pathlib import Path

        name = (raw_filename or "").strip()
        if not name:
            return ""
        expected = name.replace("_raw_after_insertline_", "_csv_").replace("_raw_", "_csv_")
        expected = expected.rsplit(".", 1)[0] + ".csv"
        p = Path(self._samples_dir()) / expected
        if not p.exists():
            return ""
        return p.read_text(encoding="utf-8", errors="replace")

    def _read_sample_text(self, system: SourceSystem) -> str:
        if not system.sample_file:
            return ""
        system.sample_file.open("rb")
        try:
            return system.sample_file.read().decode("latin1", errors="replace")
        finally:
            system.sample_file.close()

    def _initial_spec(self, system: SourceSystem) -> dict:
        if system.layout_spec:
            return system.layout_spec
        text = self._read_sample_text(system)
        if text:
            return generate_payroll_layout_spec_v2_from_sample_text(text)
        return generate_payroll_layout_spec_v2_from_sample_text("1")

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        system = get_object_or_404(SourceSystem, pk=pk)
        spec = self._initial_spec(system)

        samples = self._available_samples()
        selected_sample = (request.GET.get("sample") or "").strip()
        sample_text = self._read_sample_from_dir(selected_sample) if selected_sample else self._read_sample_text(system)

        meta_initial, head_fields, detail_fields, bottom_fields = self._spec_to_form_initial(spec)
        meta_form = LayoutMetaForm(initial=meta_initial)

        head_formset = LayoutFieldFormSet(prefix="head", initial=head_fields)
        detail_formset = LayoutFieldFormSet(prefix="detail", initial=detail_fields)
        bottom_formset = LayoutFieldFormSet(prefix="bottom", initial=bottom_fields)

        preview = None
        preview_error = ""
        expected_headers = self._expected_csv_headers(selected_sample) if selected_sample else []
        missing: list[str] = []
        extra: list[str] = []

        ctx = {
            "system": system,
            "meta_form": meta_form,
            "head_formset": head_formset,
            "detail_formset": detail_formset,
            "bottom_formset": bottom_formset,
            "preview": preview,
            "preview_error": preview_error,
            "samples": samples,
            "selected_sample": selected_sample,
            "expected_headers": expected_headers,
            "missing_headers": missing,
            "extra_headers": extra,
        }
        return render(request, self.template_name, ctx)

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        system = get_object_or_404(SourceSystem, pk=pk)
        selected_sample = (request.POST.get("sample") or "").strip()
        meta_form = LayoutMetaForm(request.POST)
        head_formset = LayoutFieldFormSet(request.POST, prefix="head")
        detail_formset = LayoutFieldFormSet(request.POST, prefix="detail")
        bottom_formset = LayoutFieldFormSet(request.POST, prefix="bottom")

        preview = None
        preview_error = ""
        expected_headers = self._expected_csv_headers(selected_sample) if selected_sample else []
        missing: list[str] = []
        extra: list[str] = []

        if meta_form.is_valid() and head_formset.is_valid() and detail_formset.is_valid() and bottom_formset.is_valid():
            spec = {
                "version": 2,
                "mode": "payroll_record",
                "encoding": "latin1",
                "record_marker": {"type": "regex", "pattern": meta_form.cleaned_data["record_marker_regex"]},
                "detail": {
                    "start_line_offset": max(int(meta_form.cleaned_data["detail_start_line_offset"]) - 1, 0),
                    "max_lines": int(meta_form.cleaned_data["detail_max_lines"]),
                    "pad_to_max": bool(meta_form.cleaned_data.get("detail_pad_to_max", False)),
                    "index_format": meta_form.cleaned_data["detail_index_format"],
                    "fields": [],
                },
                "head": {"fields": []},
                "bottom": {"fields": [], "marker": {"type": "regex", "pattern": ""}},
            }

            def _normalize_fields(rows, include_line_offset: bool) -> list[dict]:
                out = []
                for r in rows:
                    if not r:
                        continue
                    name = (r.get("name") or "").strip()
                    enabled = bool(r.get("enabled", False))
                    if not name:
                        continue
                    start, end = self._to_spec_start_end(r.get("start"), r.get("end"))
                    item = {
                        "name": name,
                        "start": start,
                        "end": end,
                        "enabled": enabled,
                    }
                    if include_line_offset:
                        item["line_offset"] = self._to_spec_line_offset(r.get("line_offset"))
                    out.append(item)
                return out

            spec["head"]["fields"] = _normalize_fields(head_formset.cleaned_data, include_line_offset=True)
            spec["detail"]["fields"] = _normalize_fields(detail_formset.cleaned_data, include_line_offset=False)
            spec["bottom"]["fields"] = _normalize_fields(bottom_formset.cleaned_data, include_line_offset=True)
            bottom_marker_regex = (meta_form.cleaned_data.get("bottom_marker_regex") or "").strip()
            if bottom_marker_regex:
                spec["bottom"]["marker"]["pattern"] = bottom_marker_regex
            bottom_start_offset = meta_form.cleaned_data.get("bottom_start_line_offset")
            if bottom_start_offset is not None and bottom_start_offset != "":
                spec["bottom"]["start_line_offset"] = max(int(bottom_start_offset) - 1, 0)
            spec["bottom"]["base_line"] = meta_form.cleaned_data.get("bottom_base_line") or "bottom"

            sample_text = self._read_sample_from_dir(selected_sample) if selected_sample else self._read_sample_text(system)

            if "autofill" in request.POST and selected_sample:
                expected_text = self._expected_csv_text(selected_sample)
                if expected_text and sample_text:
                    inferred = infer_payroll_layout_spec_v2_from_raw_and_expected_csv(sample_text, expected_text)

                    def _merge_fields(current: list[dict], inferred_fields: list[dict], include_line_offset: bool) -> list[dict]:
                        by_name: dict[str, dict] = {}
                        order: list[str] = []
                        for f in current:
                            name = (f.get("name") or "").strip()
                            if not name:
                                continue
                            by_name[name] = dict(f)
                            order.append(name)

                        for inf in inferred_fields:
                            name = (inf.get("name") or "").strip()
                            if not name:
                                continue
                            if name in by_name:
                                cur = by_name[name]
                                if int(cur.get("end") or 0) == 0 and int(inf.get("end") or 0) > 0:
                                    cur["start"] = int(inf.get("start") or 0)
                                    cur["end"] = int(inf.get("end") or 0)
                                if include_line_offset:
                                    if int(cur.get("end") or 0) == 0 and int(inf.get("line_offset") or 0) > 0:
                                        cur["line_offset"] = int(inf.get("line_offset") or 0)
                                by_name[name] = cur
                            else:
                                new_item = dict(inf)
                                new_item["enabled"] = False
                                if include_line_offset and "line_offset" not in new_item:
                                    new_item["line_offset"] = 0
                                order.append(name)
                                by_name[name] = new_item

                        return [by_name[n] for n in order if n in by_name]

                    if int(spec["detail"].get("start_line_offset") or 0) == 0 and int((inferred.get("detail") or {}).get("start_line_offset") or 0) > 0:
                        spec["detail"]["start_line_offset"] = int((inferred.get("detail") or {}).get("start_line_offset") or 0)

                    current_marker = ((spec.get("record_marker") or {}).get("pattern") or "").strip()
                    inferred_marker = ((inferred.get("record_marker") or {}).get("pattern") or "").strip()
                    if current_marker in ("", r"^\s*1") and inferred_marker:
                        spec["record_marker"]["pattern"] = inferred_marker

                    if not (spec.get("bottom") or {}).get("marker", {}).get("pattern"):
                        inf_bottom = inferred.get("bottom") or {}
                        spec["bottom"]["marker"]["pattern"] = ((inf_bottom.get("marker") or {}).get("pattern") or "").strip()

                    spec["head"]["fields"] = _merge_fields(
                        spec["head"]["fields"],
                        (inferred.get("head") or {}).get("fields") or [],
                        include_line_offset=True,
                    )
                    spec["detail"]["fields"] = _merge_fields(
                        spec["detail"]["fields"],
                        (inferred.get("detail") or {}).get("fields") or [],
                        include_line_offset=False,
                    )
                    spec["bottom"]["fields"] = _merge_fields(
                        spec["bottom"]["fields"],
                        (inferred.get("bottom") or {}).get("fields") or [],
                        include_line_offset=True,
                    )

                    meta_initial, head_init, detail_init, bottom_init = self._spec_to_form_initial(spec)
                    meta_form = LayoutMetaForm(initial=meta_initial)
                    head_formset = LayoutFieldFormSet(prefix="head", initial=head_init)
                    detail_formset = LayoutFieldFormSet(prefix="detail", initial=detail_init)
                    bottom_formset = LayoutFieldFormSet(prefix="bottom", initial=bottom_init)

            try:
                if sample_text:
                    preview_rows = parse_with_payroll_layout_spec_v2(sample_text, spec)
                    preview = preview_rows[0] if preview_rows else None
            except Exception as exc:
                preview_error = str(exc)

            preview_keys = list(preview.keys()) if preview else []
            missing = [h for h in expected_headers if h not in preview_keys]
            extra = [k for k in preview_keys if k not in expected_headers] if expected_headers else []

            if "save" in request.POST:
                system.layout_spec = spec
                system.generated_at = timezone.now()
                system.save(update_fields=["layout_spec", "generated_at"])
                if preview_error:
                    messages.warning(request, f"Layout salvo, mas o preview falhou: {preview_error}")
                else:
                    messages.success(request, "Layout salvo com sucesso.")
                return redirect("processor:system_layout", pk=system.pk)

        ctx = {
            "system": system,
            "meta_form": meta_form,
            "head_formset": head_formset,
            "detail_formset": detail_formset,
            "bottom_formset": bottom_formset,
            "preview": preview,
            "preview_error": preview_error,
            "samples": self._available_samples(),
            "selected_sample": selected_sample,
            "expected_headers": expected_headers,
            "missing_headers": missing,
            "extra_headers": extra,
        }
        return render(request, self.template_name, ctx)
