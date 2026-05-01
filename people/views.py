from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from people.models import Empresa


@login_required
def companies_list_view(request: HttpRequest) -> HttpResponse:
    companies = Empresa.objects.filter(is_active=True).order_by("name")
    return render(request, "people/companies_list.html", {"companies": companies})
