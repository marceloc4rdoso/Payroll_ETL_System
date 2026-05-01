from __future__ import annotations

import re

from django import forms

from people.models import Contato, Empresa
from processor.models import SourceSystem


class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ["name", "cnpj", "source_system", "logo", "city", "state", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["source_system"].queryset = SourceSystem.objects.filter(is_active=True).exclude(layout_spec=None)
        self.fields["source_system"].required = True

    def clean_cnpj(self):
        cnpj = self.cleaned_data["cnpj"]
        return re.sub(r"\D", "", cnpj or "")

    def save(self, commit=True):
        instance: Empresa = super().save(commit=False)
        if instance.source_system:
            instance.layout_type = instance.source_system.code
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class ContatoForm(forms.ModelForm):
    class Meta:
        model = Contato
        fields = ["empresa", "name", "email", "phone", "role", "is_active"]
