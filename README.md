# Payroll ETL System (Django)

Sistema web em Django para processamento de arquivos TXT com layout de “posição fixa”/relatório, gerando:
- CSV Web (1:1) com separador `;`
- CSV de Impressão com lógica de “dobra” A/B (concatenação horizontal)

O projeto é multi-empresa: cada Empresa possui um `layout_type` que define como o TXT será interpretado.

## Requisitos
- Python 3.x
- Git (opcional)

Dependências Python:
- Django
- Pandas

## Estrutura do projeto (resumo)
- `core/`: configurações do Django
- `people/`: cadastro de `Empresa` e `Contato`
- `processor/`: upload/processamento (`Upload`) + layouts + services
- `sample_txt/`: arquivos de exemplo
- `templates/`: templates HTML (login, upload, histórico)
- `media/`: uploads e CSVs gerados (não versionar)

## Instalação e execução (Windows / PowerShell)
No diretório do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install django pandas
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_empresas
python manage.py runserver
```

Abra:
- App: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/
- Login: http://127.0.0.1:8000/accounts/login/

## Instalação e execução (Ubuntu / WSL)
Observação: o `.venv` criado no Windows normalmente não funciona no WSL. Crie a venv no próprio Ubuntu.

```bash
cd /mnt/c/Users/capyb/Documents/trae_projects/Payroll_ETL_System
python3 -m venv .venv
source .venv/bin/activate
pip install django pandas
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_empresas
python manage.py runserver 0.0.0.0:8000
```

Abra no Windows:
- http://localhost:8000/

## Primeiro acesso (usuário e senha)
Não existe usuário/senha padrão.

Crie um superusuário:
```bash
python manage.py createsuperuser
```

Se precisar redefinir senha:
```bash
python manage.py changepassword SEU_USUARIO
```

## Carga automática de empresas/layouts
O comando abaixo cria/atualiza empresas padrão (idempotente):

```bash
python manage.py seed_empresas
```

Para simular sem gravar:
```bash
python manage.py seed_empresas --dry-run
```

Nota: para os 2 arquivos RM Labore Default (Consórcios) que não trazem CNPJ nas amostras, são usados CNPJs placeholder:
- `90000000000001` (Aricanduva)
- `90000000000002` (Cabucu)

## Como usar
1. Faça login.
2. Acesse `/` e envie um arquivo `.txt`, selecionando a Empresa correta.
3. Após processar, acesse `/uploads/` para ver o histórico e baixar:
   - CSV Web (1:1)
   - CSV Impressão (dobra A/B)

Arquivos gerados:
- `media/base_web.csv` (prepend do mais recente)
- `media/base_impressao.csv` (sobrescrito a cada processamento)
- `media/generated/<data>/empresa_<id>/...` (saídas por upload)

## Variáveis de ambiente (opcional)
- `DJANGO_SECRET_KEY`: sobrescreve o `SECRET_KEY` de desenvolvimento.

Exemplo (bash):
```bash
export DJANGO_SECRET_KEY="uma-chave-bem-grande"
```

Exemplo (PowerShell):
```powershell
$env:DJANGO_SECRET_KEY = "uma-chave-bem-grande"
```

## Testes
```bash
python manage.py test
```

