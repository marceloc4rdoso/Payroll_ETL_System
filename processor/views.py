from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from processor.forms import UploadForm
from processor.models import Upload
from processor.services import process_upload


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
