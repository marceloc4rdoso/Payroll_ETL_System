# Software Requirements Specification: Payroll ETL System. 

# Especificação Técnica: Sistema ETL Holerite Multi-Empresa

## 1. Objetivo do Projeto
Desenvolver um sistema web MVP em Django para automação de ETL de folha de pagamento. O sistema deve processar arquivos TXT de posição fixa, converter para uma base estruturada (Web) e gerar um layout de impressão otimizado (Lado A/B) em CSV.
### 1.2. Requisitos de Negócio
- Multi-Empresa: O sistema deve suportar múltiplos layouts de arquivos TXT distintos (built-in e/ou dinâmicos via cadastro de Sistemas).
- Conversão Web: Gerar um CSV 1:1 com os dados extraídos.
- Conversão para Impressão: Gerar um CSV com "dobra" de colunas (Lado A e Lado B) para otimizar o espaço de impressão.
- Portal de Usuário: Interface web para upload de arquivos e seleção automática da empresa correspondente (para usuários clientes).
- Os usuários da Capybird Maker Labs serão os usuários admin que podem fazer upload de arquivos e gerar layouts de qualquer empresa.
- Os usuários não admin podem fazer upload de arquivos e gerar layouts apenas para a empresa vinculada.
- Todo usuário do portal de cliente é um Contato, e todo Contato está vinculado a uma Empresa.
- Ao cadastrar um Contato (ativo), o sistema cria automaticamente um Usuário e faz o vínculo Usuário → Empresa.
 - O usuário é criado sem senha (password inválido) e deve definir a senha no fluxo "Primeiro acesso / Esqueci minha senha" da tela de login.
  
## 2. Escopo Técnico - Especificações Técnicas (Stack)
- Backend: Python 3.10+ / Django 4.2+
- Processamento: Pandas (Engine de transformação)
- Frontend: Django Templates + CSS leve (sem dependências)
- Arquivos: Suporte a 5 ou mais layouts distintos de TXT (um para cada empresa).
- Banco de Dados: SQLite (padrão MVP)

## 3. Fluxo de Trabalho (Pipeline)
### 🔼 Etapa 1: Upload e Identificação
- O usuário acessa o portal web.
 - Se o usuário não estiver logado, redireciona para a página de login.
 - Após login, redireciona para a página principal (dashboard).
- O usuário acessa `/upload/` e faz upload de um arquivo `.txt` por vez.
 - Usuário admin (staff/superuser): seleciona a Empresa (ativa) no formulário.
 - Usuário não-admin: a Empresa é definida automaticamente conforme o vínculo Usuário → Empresa.
- O sistema valida a extensão do arquivo (`.txt`) e a Empresa selecionada.
### 3.1 Mapeamento e Extração (ETL) 
- Extração (Extract)Leitura de arquivos .txt plaintext.
- Uso de mapeamento manual de posições fixas (Fixed Width) para identificar campos.
- Tratamento de todos os campos como string para preservar zeros à esquerda.

Obs.: os arquivos modelo de referência não são versionados no GitHub. Use o diretório local `processor/.sample_txt/` (ignorado no Git) para armazenar amostras/modelos.
Obs.: há também um diretório local `processor/.sample_txt/` usado para validação (raw + CSV esperado) do designer de layouts, seguindo o padrão:
- Raw: `N_raw_<Sistema>.txt`
- Raw intermediário (após inserção de linhas em branco): `N_raw_after_insertline_<Sistema>.txt`
- Esperado: `N_csv_<Sistema>.csv`

### ⚙️ Etapa 3.2: Extração (Parsing)
- O sistema utiliza um mapeamento de Posições Fixas específico para a empresa selecionada.
- O Pandas lê o arquivo garantindo que todos os campos sejam tratados como string (para preservar zeros à esquerda em CPFs e Contas).
### 🔄 Etapa 3.3: Transformação (The "Fold" Logic)
O sistema deve gerar dois DataFrames distintos:
1. DataFrame Web (1:1): Representação fiel do arquivo original (quantidade de colunas varia por layout).
2. DataFrame Impressão (Dobra A/B):
 1. Calcula o ponto médio: \(M = ceil(TotalLinhas / 2)\).
 2. Divide os dados em Bloco A (linhas 1 a \(M\)) e Bloco B (linhas \(M+1\) até o fim).
 3. Renomeia as colunas de A (ex: Nome_A, Salario_A) e B (ex: Nome_B, Salario_B).
 4. Concatena horizontalmente, resultando em um arquivo de 80 colunas. (Exemplo, pode ser masi ou menos colunad. Isso pode variar de acordo com cada arquivo de uma determinada empresa)
### 🔽 Etapa 3.4: Entrega
- Geração de arquivo base_web.csv. (O base_web.csv sempre terá um append do mais recente acima para o mais antigo abaixo a cada nova carga.)
- Geração de arquivo base_impressao.csv. Sempre subscrever o arquivo existente caso exista um anteriormente gerado. (Para evitar duplicatas).
- Armazenamento dos arquivos gerados no diretório media/. organizado por data ou empresa.
- Disponibilização de links de download para o CSV Web e o CSV de Impressão.
Obs.: Os arquivos csv devem ter campos separados por ";" (semicolon). Em uma continuação do desenvolvimento esses arquivos base_printer.csv serão usados para alimentar um arquivo jxml (Jaspersoft)que posteriormente será processado para geração de PDFs para posterior impressao.
## 5. Estrutura de Especialistas (Prompts para Agentes Trae)
🐍 Agente Python/Pandas
- Responsável pela lógica do ETL em `processor/services.py` (parsing, geração de CSV, dobra A/B).
- Deve garantir leitura como string, preservando zeros à esquerda, e separador `;` nos CSVs.

🎸 Agente Django
- Responsável pela arquitetura do projeto, configuração de `settings.py`, `urls.py`, models, views e rotas.
- Deve manter boas práticas de auth (login/logout), uploads em `media/` e migrações consistentes.

🧩 Agente Layout/Parser (Layouts Dinâmicos)
- Responsável pelo cadastro de Sistemas (`SourceSystem`), geração de `layout_spec` a partir de arquivos modelo e ajuste manual no Designer de Layout.
- Deve garantir deduplicação por hash (SHA-256) e fallback para layouts “built-in” quando aplicável.
- Deve manter compatibilidade com `layout_spec` v2 (modo holerite: head/detail/bottom, marcador de registro e padding de detail).

🎨 Agente UI/UX (CSS leve)
- Responsável por melhorar a UX sem aumentar complexidade: cards, navegação, tabelas, formulários.
- Deve manter o tema consistente e reutilizar `templates/base.html`.

🧪 Agente de Testes Unitários
- Responsável por testes de parsing (built-in e dinâmico), dobra A/B, e smoke tests de rotas principais.

## 6. Estrutura de Arquivos Sugerida
project_root/
├── core/                   # Configurações globais do projeto (settings.py, urls.py)
├── people/                 # App de cadastro e gestão de clientes
│   ├── models.py           # Modelos de Pessoa Jurídica (Empresas) e Pessoa Física (Contatos/Funcionários)
│   ├── admin.py            # Interface administrativa para gerir as 5 empresas ou mais e contatos
│   ├── views.py            # CRUD de clientes e listagem
│   └── urls.py             # Rotas do módulo de pessoas
├── processor/              # App do Motor ETL (O "Coração" do sistema)
│   ├── layouts.py          # Layouts built-in (quando existirem)
│   ├── layout_builder.py   # Geração de layout_spec + parsing genérico (layouts dinâmicos)
│   ├── services.py         # Motor de processamento (TXT -> CSV e Dobra A/B)
│   ├── models.py           # Registro de Uploads (FK para Empresa, Data, Arquivos Gerados)
│   ├── views.py            # Lógica de Upload, Processamento e Download
│   └── urls.py             # Rotas do módulo de processamento
├── templates/              # Interface HTML (Django Templates + CSS leve)
│   ├── base.html           # Layout principal (Navbar/Footer)
│   ├── people/             # Telas de cadastro de clientes
│   └── processor/          # Telas de upload e histórico de holerites
├── static/                 # Assets do sistema (logo da Capybird, etc.)
└── media/                  # Repositório de arquivos (TXTs originais e CSVs gerados)

## 7. Implementação Atual (o que já foi feito)

### 7.1 Setup e Convenções do Repositório
- Ambiente virtual criado em `.venv/`.
- Dependências instaladas: `django` e `pandas`.
- Diretório de amostras/modelos local (não versionado): `processor/.sample_txt/` (ignorado no Git).
- Banco de dados padrão: SQLite (`db.sqlite3`).
 - Assets do sistema: `static/` (servindo em `/static/`).

### 7.2 Estrutura Django criada
- Projeto Django: `core` (na raiz do repositório).
- Apps criados: `people` e `processor`.
- Apps adicionados em `INSTALLED_APPS`.
- Templates globais habilitados via `TEMPLATES['DIRS'] = [BASE_DIR / 'templates']`.
- Configuração de mídia: `MEDIA_URL=/media/` e `MEDIA_ROOT=BASE_DIR/'media'`.
- Internacionalização: `LANGUAGE_CODE='pt-br'` e `TIME_ZONE='America/Sao_Paulo'`.

### 7.3 Rotas e autenticação
- Autenticação padrão do Django habilitada em `accounts/` via `django.contrib.auth.urls`.
- Rotas principais:
  - `/` -> dashboard (requer login)
  - `/upload/` -> upload de TXT (app `processor`)
  - `/uploads/` -> histórico de uploads e links de download
  - `/sistemas/` -> CRUD de Sistemas (cadastro do sistema de origem + arquivo modelo)
  - `/sistemas/<id>/layout/` -> Designer de Layout (admin/staff) para ajustar `layout_spec`
  - `/people/empresas/` -> CRUD de Empresas
  - `/people/contatos/` -> CRUD de Contatos
  - `/admin/` -> Django Admin
- Tela de login implementada em `templates/registration/login.html`.
- Tela de logout elegante implementada em `templates/registration/logged_out.html`.
- Logout é efetuado via POST (por segurança) e não por GET.
- Não existe usuário/senha padrão: o primeiro acesso deve ser feito criando um superusuário.
- Permissões:
 - Usuários admin (staff/superuser): acesso total (CRUDs + upload para qualquer empresa).
 - Usuários não-admin: acesso a Dashboard/Upload/Histórico restritos à empresa vinculada.
- Primeiro acesso / senha:
 - O fluxo de definição de senha utiliza as rotas padrão do Django em `/accounts/password_reset/` (link disponível na tela de login).

### 7.4 Modelagem de dados implementada
#### App `people`
- `Empresa`
  - Campos principais: `name`, `cnpj` (somente dígitos, 14, único), `is_maintainer`, `source_system`, `layout_type` (sincronizado), `logo`, `is_active`, timestamps.
  - `logo` é armazenado em `media/company_logos/<cnpj>/...`.
  - `is_maintainer=True` indica empresa mantenedora (Capybird): usuários vinculados a Contatos dessa empresa são admin.
- `Contato`
  - FK para `Empresa` e campos básicos: `name`, `email`, `phone`, `role`, `is_active`, `created_at`.
  - `user` (1:1): Usuário do portal (quando aplicável).
- `Vínculo Usuário → Empresa` (`UserEmpresaVinculo`)
  - Define a Empresa padrão/restrita para usuários não-admin (portal do cliente).

#### App `processor`
- `Sistema` (`SourceSystem`)
  - Campos principais: `code`, `name`, `is_active`, `sample_file`, `sample_sha256`, `layout_spec`, `generated_at`.
  - `sample_file` é armazenado em `media/layout_samples/<code>/...`.
  - `layout_spec` é gerado automaticamente a partir do arquivo modelo e pode ser ajustado no Designer.

#### App `processor`
- `Upload`
  - FK para `Empresa`, referência a usuário (`uploaded_by`), `original_file`.
  - Campos de controle: `status`, `row_count`, `error_message`, `processed_at`, `detected_layout_type`.
  - Saídas geradas: `web_csv` e `print_csv`.

### 7.5 Parsing e processamento de TXT (ETL)
- Implementado em `processor/services.py`.
- O sistema suporta:
  - layouts built-in (por `code` conhecido)
  - layouts dinâmicos (via `layout_spec` armazenado no banco, criado a partir do arquivo modelo e/ou ajustado no Designer)
- Saídas geradas:
  - CSV Web (1:1) com `;` como separador.
  - CSV Impressão (dobra A/B) aplicando o split no meio (ceil) e concatenação horizontal.
  - `base_web.csv`: é atualizado com prepend (mais recente acima).
  - `base_impressao.csv`: é sobrescrito a cada processamento.

### 7.6 Layouts (posições fixas)
- Mapeamentos centralizados em `processor/layouts.py` com:
  - Nome do campo
  - Posição inicial e final (base 0, end exclusivo)
  - Tipo (string/numeric/date)
  - Default quando aplicável

### 7.7 Interface mínima (templates)
- `templates/base.html`: layout básico e navegação.
- `templates/processor/upload.html`: formulário de upload + empresa.
- `templates/processor/uploads_list.html`: histórico e links de download.
- `templates/people/empresa_list.html`: listagem simples de empresas.

### 7.8 Admin
- Registro de modelos no Django Admin:
  - `people/admin.py`: `Empresa`, `Contato`
  - `processor/admin.py`: `Upload`, `SourceSystem`

### 7.9 Testes unitários
- Testes básicos em `processor/tests.py`:
  - Parsing do layout GENESIS (amostra inline)
  - Parsing do layout RM Labore Custom (amostra inline)
  - Validação do algoritmo de dobra A/B (`fold_dataframe`)

### 7.10 Seed automático de Empresas (carga inicial)
- Management command criado: `python manage.py seed_empresas`
- Objetivo: criar/atualizar automaticamente as empresas/layouts padrões com base nos exemplos.
- Observação: dois arquivos RM Labore Default (Consórcios) não trazem CNPJ nas amostras; foram usados CNPJs “placeholder”:
  - `90000000000001` (Aricanduva)
  - `90000000000002` (Cabucu)
- Dry-run disponível: `python manage.py seed_empresas --dry-run`

### 7.11 CRUD de cadastros e Dashboard pós-login
- Dashboard central em `/` (requer login) com KPIs:
  - Total de uploads
  - Contagem por status (Pendente/Processando/Concluído/Falhou)
  - Uploads por empresa
  - Uploads por usuário
  - Últimos uploads
- CRUD de Empresas:
  - Listar: `/people/empresas/`
  - Criar: `/people/empresas/novo/`
  - Editar: `/people/empresas/<id>/editar/`
  - Excluir: `/people/empresas/<id>/excluir/`
- CRUD de Contatos:
  - Listar: `/people/contatos/` (com filtro por empresa via querystring)
  - Criar: `/people/contatos/novo/`
  - Editar: `/people/contatos/<id>/editar/`
  - Excluir: `/people/contatos/<id>/excluir/`
- Menu superior (maintop) atualizado para navegar entre Dashboard, Upload, Histórico, Empresas e Contatos.

### 7.12 Sistemas de origem e geração de layouts (novo fluxo)
- Entidade `Sistema` (SourceSystem) representa o “sistema de origem” dos arquivos (ex.: RM Labore, Folhamatic, Genesis).
- Cadastro de sistemas em `/sistemas/` com CRUD completo.
- Ao criar/editar um Sistema, é possível enviar um **arquivo modelo TXT**; ao salvar:
  - o sistema calcula o SHA-256 do arquivo
  - impede duplicidade (se o mesmo arquivo modelo já estiver associado a outro sistema com layout pronto)
-  gera automaticamente um `layout_spec` (JSON) no formato v2 (modo holerite: head/detail/bottom), que deve ser ajustado no Designer quando necessário.
- Designer de Layout (`/sistemas/<id>/layout/`):
  - Permite configurar `record_marker` (regex do início do holerite) e a separação de seções (detail x bottom).
  - Permite cadastrar/ajustar campos com posições (Start/End) e linha (Head/Bottom).
  - UI usa valores 1-based (linha 1 / coluna 1), e o sistema converte internamente para índices do parser.
  - Possui Preview com sample local de `processor/.sample_txt/`.
  - Possui Auto preencher (raw + CSV esperado) para sugerir um layout inicial sem ativar campos novos automaticamente.
- No cadastro de Empresa, o usuário deve selecionar um **Sistema/Layout pronto** (somente sistemas com `layout_spec` gerado aparecem para seleção).
- No processamento, o layout aplicado ao upload é definido por:
  - `empresa.source_system.code` (preferencial)
  - fallback para `empresa.layout_type` (compatibilidade com registros antigos)
- Diretório de amostras locais (não versionado): `processor/.sample_txt/` (ignorado no Git).

### 7.13 Branding e logos (Capybird Maker Labs + clientes)
- Logo do sistema (Capybird Maker Labs) em `static/brand/capybird-maker-labs.svg` (servido em `/static/...`).
- Aplicação do logo no topo, login e logout (templates):
  - `templates/base.html`
  - `templates/registration/login.html`
  - `templates/registration/logged_out.html`
- Logo do cliente por Empresa via upload (`Empresa.logo`) com exibição na listagem de Empresas.

## 8. Comandos de execução (ordem recomendada)

### 8.1 Windows (PowerShell)
1. `python -m venv .venv`
2. `.\.venv\Scripts\Activate.ps1`
3. `pip install django pandas`
4. `python manage.py migrate`
5. `python manage.py createsuperuser`
6. `python manage.py seed_empresas`
7. `python manage.py runserver`

### 8.3 Comandos auxiliares
- Sincronizar/criar usuários para contatos existentes:
  - `python manage.py sync_contato_users`
  - `python manage.py sync_contato_users --names Ana Edilson`

### 8.2 Ubuntu (WSL)
- Atenção: a `.venv` criada no Windows geralmente não funciona no WSL; crie uma venv própria no Ubuntu caso necessário.
1. `cd /mnt/c/Users/capyb/Documents/trae_projects/Payroll_ETL_System`
2. `python3 -m venv .venv`
3. `source .venv/bin/activate`
4. `pip install django pandas`
5. `python manage.py migrate`
6. `python manage.py createsuperuser`
7. `python manage.py seed_empresas`
8. `python manage.py runserver 0.0.0.0:8000`
