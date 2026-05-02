from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from people.models import Contato, UserEmpresaVinculo


class Command(BaseCommand):
    help = "Cria/vincula usuários para Contatos (clientes) e sincroniza o vínculo Usuário → Empresa."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Simula sem gravar no banco.")
        parser.add_argument("--names", nargs="*", default=[], help="Filtra por nomes de Contato (contém, case-insensitive).")
        parser.add_argument("--empresa", default="", help="Filtra por nome de Empresa (contém, case-insensitive).")

    def handle(self, *args: Any, **options: Any):
        dry_run: bool = bool(options["dry_run"])
        names: list[str] = list(options["names"] or [])
        empresa_filter: str = (options["empresa"] or "").strip()

        qs = Contato.objects.select_related("empresa", "user").filter(is_active=True)

        if names:
            for n in names:
                qs = qs.filter(name__icontains=n)
        if empresa_filter:
            qs = qs.filter(empresa__name__icontains=empresa_filter)

        contatos = list(qs.order_by("empresa__name", "name"))
        if not contatos:
            self.stdout.write(self.style.WARNING("Nenhum contato encontrado com os filtros informados."))
            return

        User = get_user_model()

        def _unique_username(base: str) -> str:
            username_field = User._meta.get_field(User.USERNAME_FIELD)
            max_len = int(getattr(username_field, "max_length", 150) or 150)
            candidate = (base or "user")[:max_len]
            username = candidate[:max_len]
            i = 1
            while User.objects.filter(username__iexact=username).exists():
                i += 1
                suffix = f"-{i}"
                username = (candidate[: (max_len - len(suffix))] + suffix)[:max_len]
            return username

        def _ensure_user(contato: Contato):
            if contato.user_id:
                if contato.empresa.is_maintainer and not (contato.user.is_staff and contato.user.is_superuser):
                    contato.user.is_staff = True
                    contato.user.is_superuser = True
                    contato.user.save(update_fields=["is_staff", "is_superuser"])
                return contato.user
            email = (contato.email or "").strip().lower()
            user = None
            if email:
                user = User.objects.filter(email__iexact=email).first()

            if not user:
                base = email or slugify(contato.name)
                username = _unique_username(base)
                user = User.objects.create_user(username=username, email=email)
                user.set_unusable_password()
                if contato.empresa.is_maintainer:
                    user.is_staff = True
                    user.is_superuser = True
                user.save(update_fields=["password", "is_staff", "is_superuser"])
            elif contato.empresa.is_maintainer and not (user.is_staff and user.is_superuser):
                user.is_staff = True
                user.is_superuser = True
                user.save(update_fields=["is_staff", "is_superuser"])
            contato.user = user
            contato.save(update_fields=["user"])
            return user

        def _ensure_vinculo(user, contato: Contato):
            UserEmpresaVinculo.objects.update_or_create(
                user=user,
                defaults={"empresa": contato.empresa, "is_active": True},
            )

        self.stdout.write(f"Contatos selecionados: {len(contatos)}")

        ctx = transaction.atomic() if not dry_run else _noop()
        with ctx:
            for contato in contatos:
                user = _ensure_user(contato)
                _ensure_vinculo(user, contato)
                self.stdout.write(f"- OK: {contato.name} ({contato.empresa.name}) -> {user.username}")

            if dry_run:
                self.stdout.write(self.style.WARNING("DRY-RUN: nenhuma alteração foi persistida."))


class _noop:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False
