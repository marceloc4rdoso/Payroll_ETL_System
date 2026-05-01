from __future__ import annotations

from django import forms

from people.models import Empresa


class UploadForm(forms.Form):
    """
    Form simples para upload de TXT + seleção de empresa/layout.

    A seleção de Empresa é parte do fluxo descrito na spec.md.
    """

    empresa = forms.ModelChoiceField(queryset=Empresa.objects.filter(is_active=True))
    arquivo = forms.FileField()

    def clean_arquivo(self):
        f = self.cleaned_data["arquivo"]
        if not f.name.lower().endswith(".txt"):
            raise forms.ValidationError("Envie um arquivo .txt.")
        return f

