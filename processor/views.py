from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from processor.forms import SourceSystemForm, UploadForm
from processor.layout_builder import generate_fixed_width_spec_from_sample_text, sha256_of_uploaded_file
from processor.models import Upload
from processor.models import SourceSystem
from processor.services import process_upload


@login_required
def dashboard_view(request: HttpRequest) -> HttpResponse:
    status_counts = dict(
        Upload.objects.values("status")
        .annotate(total=Count("id"))
        .values_list("status", "total")
    )

    total_uploads = Upload.objects.count()

    uploads_by_empresa = list(
        Upload.objects.values("empresa__name")
        .annotate(total=Count("id"))
        .order_by("-total", "empresa__name")
    )

    uploads_by_user = list(
        Upload.objects.values("uploaded_by__username")
        .annotate(total=Count("id"))
        .order_by("-total", "uploaded_by__username")
    )

    max_by_empresa = max([r["total"] for r in uploads_by_empresa], default=0)
    for r in uploads_by_empresa:
        r["pct"] = int(round((r["total"] / max_by_empresa) * 100)) if max_by_empresa else 0

    max_by_user = max([r["total"] for r in uploads_by_user], default=0)
    for r in uploads_by_user:
        r["pct"] = int(round((r["total"] / max_by_user) * 100)) if max_by_user else 0

    last_uploads = (
        Upload.objects.select_related("empresa", "uploaded_by")
        .order_by("-created_at")[:10]
    )

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
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
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
        form = UploadForm()

    return render(request, "processor/upload.html", {"form": form})


@login_required
def uploads_list_view(request: HttpRequest) -> HttpResponse:
    uploads = Upload.objects.select_related("empresa", "uploaded_by").all()[:50]
    return render(request, "processor/uploads_list.html", {"uploads": uploads})


class SourceSystemListView(LoginRequiredMixin, ListView):
    model = SourceSystem
    template_name = "processor/system_list.html"
    context_object_name = "systems"
    paginate_by = 50


class SourceSystemCreateView(LoginRequiredMixin, CreateView):
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
            spec = generate_fixed_width_spec_from_sample_text(text)
            self.object.layout_spec = spec
            self.object.generated_at = timezone.now()
            self.object.save(update_fields=["layout_spec", "generated_at", "sample_sha256"])
        return response


class SourceSystemUpdateView(LoginRequiredMixin, UpdateView):
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
            spec = generate_fixed_width_spec_from_sample_text(text)
            self.object.layout_spec = spec
            self.object.generated_at = timezone.now()
            self.object.save(update_fields=["layout_spec", "generated_at", "sample_sha256"])
        return response


class SourceSystemDeleteView(LoginRequiredMixin, DeleteView):
    model = SourceSystem
    template_name = "processor/system_confirm_delete.html"
    success_url = reverse_lazy("processor:system_list")
