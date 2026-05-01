from __future__ import annotations

from dataclasses import dataclass

from django.core.management.base import BaseCommand
from django.db import transaction

from people.models import Empresa


@dataclass(frozen=True)
class EmpresaSeed:
    name: str
    layout_type: str
    cnpj: str | None = None


SEEDS: list[EmpresaSeed] = [
    EmpresaSeed(
        name="ANDRES ROMANO ENGENHARIA LTDA",
        layout_type=Empresa.LayoutType.FOLHAMATIC,
        cnpj="11437239000140",
    ),
    EmpresaSeed(
        name="CONSORCIO CT - ARICANDUVA",
        layout_type=Empresa.LayoutType.RMLABORE_DEFAULT,
        cnpj=None,
    ),
    EmpresaSeed(
        name="CONSORCIO CT - CABUCU",
        layout_type=Empresa.LayoutType.RMLABORE_DEFAULT,
        cnpj=None,
    ),
    EmpresaSeed(
        name="ORION SA",
        layout_type=Empresa.LayoutType.GENESIS,
        cnpj="61082863000573",
    ),
    EmpresaSeed(
        name="VALDEQUIMICA PRODUTOS QUIMICOS LTDA",
        layout_type=Empresa.LayoutType.CONTIMATIC,
        cnpj="43365816000636",
    ),
    EmpresaSeed(
        name="VILA BOA CONSTRUCOES E SERVICOS",
        layout_type=Empresa.LayoutType.RMLABORE_CUSTOM,
        cnpj="02785261000190",
    ),
]


PLACEHOLDER_CNPJS: dict[str, str] = {
    "CONSORCIO CT - ARICANDUVA": "90000000000001",
    "CONSORCIO CT - CABUCU": "90000000000002",
}


class Command(BaseCommand):
    help = "Cria/atualiza Empresas padrão com seus layouts (idempotente)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Mostra o que seria feito, sem gravar no banco.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run: bool = bool(options["dry_run"])

        created = 0
        updated = 0

        for seed in SEEDS:
            desired_cnpj = seed.cnpj or PLACEHOLDER_CNPJS.get(seed.name)
            if not desired_cnpj:
                self.stderr.write(self.style.ERROR(f"Sem CNPJ para '{seed.name}'"))
                continue

            empresa = Empresa.objects.filter(cnpj=desired_cnpj).first()
            if not empresa:
                empresa = Empresa.objects.filter(name__iexact=seed.name).first()

            if not empresa:
                if dry_run:
                    self.stdout.write(f"[DRY] CREATE: {seed.name} ({desired_cnpj}) [{seed.layout_type}]")
                else:
                    empresa = Empresa.objects.create(
                        name=seed.name,
                        cnpj=desired_cnpj,
                        layout_type=seed.layout_type,
                        is_active=True,
                    )
                    self.stdout.write(f"CREATE: {empresa.name} ({empresa.cnpj}) [{empresa.layout_type}]")
                created += 1
                continue

            changed_fields: list[str] = []
            if empresa.layout_type != seed.layout_type:
                empresa.layout_type = seed.layout_type
                changed_fields.append("layout_type")
            if not empresa.is_active:
                empresa.is_active = True
                changed_fields.append("is_active")

            if changed_fields:
                if dry_run:
                    self.stdout.write(f"[DRY] UPDATE: {empresa.name} ({empresa.cnpj}) fields={changed_fields}")
                else:
                    empresa.save(update_fields=changed_fields)
                updated += 1
            else:
                self.stdout.write(f"OK: {empresa.name} ({empresa.cnpj}) [{empresa.layout_type}]")

        if dry_run:
            transaction.set_rollback(True)

        self.stdout.write(self.style.SUCCESS(f"seed_empresas: created={created} updated={updated} dry_run={dry_run}"))

