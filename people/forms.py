from __future__ import annotations

import re

from django import forms
from django.contrib.auth import get_user_model
from django.utils.text import slugify

from people.models import Contato, Empresa
from people.models import UserEmpresaVinculo
from processor.models import SourceSystem


class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ["name", "cnpj", "is_maintainer", "source_system", "logo", "city", "state", "is_active"]

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

    def save(self, commit=True):
        instance: Contato = super().save(commit=False)
        if commit:
            instance.save()
            self.save_m2m()
            self._ensure_user_for_contato(instance)
        return instance

    def _ensure_user_for_contato(self, contato: Contato) -> None:
        if not contato.is_active:
            return
        if contato.user_id:
            if contato.empresa.is_maintainer and not (contato.user.is_staff and contato.user.is_superuser):
                contato.user.is_staff = True
                contato.user.is_superuser = True
                contato.user.save(update_fields=["is_staff", "is_superuser"])
            self._ensure_user_empresa_vinculo(contato.user, contato.empresa)
            return

        User = get_user_model()
        email = (contato.email or "").strip().lower()

        user = None
        if email:
            user = User.objects.filter(email__iexact=email).first()

        if not user:
            username_field = User._meta.get_field(User.USERNAME_FIELD)
            max_len = int(getattr(username_field, "max_length", 150) or 150)

            base = email or (slugify(contato.name) or "user")
            candidate = base[:max_len]
            username = candidate
            i = 1
            while User.objects.filter(username__iexact=username).exists():
                i += 1
                suffix = f"-{i}"
                username = (candidate[: (max_len - len(suffix))] + suffix)[:max_len]

            user = User.objects.create_user(
                username=username,
                email=email,
            )
            user.set_unusable_password()
            if contato.empresa.is_maintainer:
                user.is_staff = True
                user.is_superuser = True
            user.save(update_fields=["password", "is_staff", "is_superuser"])

        contato.user = user
        contato.save(update_fields=["user"])
        self._ensure_user_empresa_vinculo(user, contato.empresa)

    @staticmethod
    def _ensure_user_empresa_vinculo(user, empresa: Empresa) -> None:
        UserEmpresaVinculo.objects.update_or_create(
            user=user,
            defaults={"empresa": empresa, "is_active": True},
        )
