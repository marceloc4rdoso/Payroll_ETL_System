from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, RedirectView, UpdateView

from people.models import Empresa
from people.models import Contato
from people.forms import ContatoForm, EmpresaForm


class StaffOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        return bool(self.request.user.is_staff or self.request.user.is_superuser)


class PeopleHomeView(StaffOnlyMixin, LoginRequiredMixin, RedirectView):
    pattern_name = "people:empresa_list"


class EmpresaListView(StaffOnlyMixin, LoginRequiredMixin, ListView):
    model = Empresa
    template_name = "people/empresa_list.html"
    context_object_name = "empresas"
    paginate_by = 50

    def get_queryset(self):
        return Empresa.objects.select_related("source_system").order_by("name")


class EmpresaCreateView(StaffOnlyMixin, LoginRequiredMixin, CreateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = "people/empresa_form.html"
    success_url = reverse_lazy("people:empresa_list")


class EmpresaUpdateView(StaffOnlyMixin, LoginRequiredMixin, UpdateView):
    model = Empresa
    form_class = EmpresaForm
    template_name = "people/empresa_form.html"
    success_url = reverse_lazy("people:empresa_list")


class EmpresaDeleteView(StaffOnlyMixin, LoginRequiredMixin, DeleteView):
    model = Empresa
    template_name = "people/empresa_confirm_delete.html"
    success_url = reverse_lazy("people:empresa_list")


class ContatoListView(StaffOnlyMixin, LoginRequiredMixin, ListView):
    model = Contato
    template_name = "people/contato_list.html"
    context_object_name = "contatos"
    paginate_by = 50

    def get_queryset(self):
        qs = Contato.objects.select_related("empresa").order_by("empresa__name", "name")
        empresa_id = self.request.GET.get("empresa")
        if empresa_id:
            qs = qs.filter(empresa_id=empresa_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["empresas"] = Empresa.objects.order_by("name")
        ctx["empresa_selected"] = self.request.GET.get("empresa", "")
        return ctx


class ContatoCreateView(StaffOnlyMixin, LoginRequiredMixin, CreateView):
    model = Contato
    form_class = ContatoForm
    template_name = "people/contato_form.html"
    success_url = reverse_lazy("people:contato_list")


class ContatoUpdateView(StaffOnlyMixin, LoginRequiredMixin, UpdateView):
    model = Contato
    form_class = ContatoForm
    template_name = "people/contato_form.html"
    success_url = reverse_lazy("people:contato_list")


class ContatoDeleteView(StaffOnlyMixin, LoginRequiredMixin, DeleteView):
    model = Contato
    template_name = "people/contato_confirm_delete.html"
    success_url = reverse_lazy("people:contato_list")
