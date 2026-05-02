# Payroll ETL System (Django)

Sistema web em Django para processamento de arquivos TXT com layout de “posição fixa”/relatório, gerando:
- CSV Web (1:1) com separador `;`
- CSV de Impressão com lógica de “dobra” A/B (concatenação horizontal)

O projeto é multi-empresa: cada Empresa aponta para um Sistema de origem (`SourceSystem`) e o parsing usa o `layout_spec` configurado para esse Sistema.

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
- `processor/.sample_txt/`: amostras locais para validação do designer de layout (ignorado no git)
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

## Perfis de acesso (admin x cliente)
- Admin (staff/superuser): acesso total (Sistemas, Empresas, Contatos, Upload para qualquer empresa).
- Cliente (não-admin): acesso restrito à sua empresa (Dashboard/Upload/Histórico).

Todo usuário cliente é um `Contato` vinculado a uma `Empresa`. Ao criar/editar um Contato ativo, o sistema cria automaticamente um usuário e o vínculo Usuário → Empresa.

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

### Primeiro acesso / Definir senha (clientes)
Usuários criados automaticamente para Contatos são criados sem senha (senha inválida). O primeiro acesso é via:
- http://127.0.0.1:8000/accounts/password_reset/

Em desenvolvimento, o link de redefinição é impresso no console (EMAIL_BACKEND console).

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
2. Acesse `/upload/` e envie um arquivo `.txt`.
   - Admin escolhe a Empresa no formulário.
   - Cliente usa a Empresa vinculada automaticamente.
3. Após processar, acesse `/uploads/` para ver o histórico e baixar:
   - CSV Web (1:1)
   - CSV Impressão (dobra A/B)

Arquivos gerados:
- `media/base_web.csv` (prepend do mais recente)
- `media/base_impressao.csv` (sobrescrito a cada processamento)
- `media/generated/<data>/empresa_<id>/...` (saídas por upload)

## Layouts dinâmicos (Designer)
1. Cadastre um Sistema em `/sistemas/` e envie um arquivo modelo `.txt`.
2. Abra o Designer em `/sistemas/<id>/layout/`.
3. Ajuste:
   - Marcador de início do holerite (Regex)
   - Detail: linha inicial
   - Campos Head/Detail/Bottom com Start/End e Linha (quando aplicável)
4. Use Preview para validar extração.

Convenção do Designer:
- Linha e colunas são preenchidas em 1-based (linha 1, coluna 1..N).

### Samples locais (.sample_txt)
O Designer suporta comparar o Preview com um CSV esperado usando arquivos em `processor/.sample_txt/`:
- Raw: `N_raw_<Sistema>.txt`
- Raw intermediário: `N_raw_after_insertline_<Sistema>.txt`
- Esperado: `N_csv_<Sistema>.csv`

## Comandos úteis
Criar/vincular usuários para contatos já existentes:
```bash
python manage.py sync_contato_users
python manage.py sync_contato_users --names Ana Edilson
```

## Variáveis de ambiente (opcional)
- `DJANGO_SECRET_KEY`: sobrescreve o `SECRET_KEY` de desenvolvimento.
- `DJANGO_EMAIL_BACKEND`: sobrescreve o backend de e-mail (default: console).
- `DJANGO_DEFAULT_FROM_EMAIL`: remetente padrão de e-mail.

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

