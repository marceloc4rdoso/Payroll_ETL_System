# Software Requirements Specification: Payroll ETL System. 

# Especificação Técnica: Sistema ETL Holerite Multi-Empresa

## 1. Objetivo do Projeto
Desenvolver um sistema web MVP em Django para automação de ETL de folha de pagamento. O sistema deve processar arquivos TXT de posição fixa, converter para uma base estruturada (Web) e gerar um layout de impressão otimizado (Lado A/B) em CSV.
### 1.2. Requisitos de Negócio
- Multi-Empresa: O sistema deve suportar 5 layouts de arquivos TXT distintos.
- Conversão Web: Gerar um CSV 1:1 com os dados extraídos.
- Conversão para Impressão: Gerar um CSV com "dobra" de colunas (Lado A e Lado B) para otimizar o espaço de impressão.
- Portal de Usuário: Interface web para upload de arquivos e seleção da empresa correspondente.

## 2. Escopo Técnico - Especificações Técnicas (Stack)
- Backend: Python 3.10+ / Django 4.2+
- Processamento: Pandas (Engine de transformação)
- Frontend: Django Templates + Bootstrap 5 (Interface para upload e gestão)
- Arquivos: Suporte a 5 ou mais layouts distintos de TXT (um para cada empresa).
- Banco de Dados: SQLite (padrão MVP)

## 3. Fluxo de Trabalho (Pipeline)
### 🔼 Etapa 1: Upload e Identificação
- O usuário acessa o portal web.
 - Se usuário não estiver logado, redireciona para página de login.
 - Após login, redireciona para a página principal.
 - Se usuario Admin:
  - Faz o upload do arquivo .txt.
  - Seleciona em um Dropdown a qual das 5 empresas o arquivo pertence.
- Se usuario Normal:
  - Redireciona para página de upload.
  - A empresa correspondente ja é pré selecionada.
  - Faz o upload do arquivo .txt.
Obs.: O sistema deve validar a empresa selecionada e o arquivo enviado.
O sistema aceita até 10 arquivos .TXT por vez.
### 3.1 Mapeamento e Extração (ETL) 
- Extração (Extract)Leitura de arquivos .txt plaintext.
- Uso de mapeamento manual de posições fixas (Fixed Width) para identificar campos.
- Tratamento de todos os campos como string para preservar zeros à esquerda.

Obs.:  No diretório sample_txt/ estão exemplos de arquivos TXT para cada empresa.

### ⚙️ Etapa 3.2: Extração (Parsing)
- O sistema utiliza um mapeamento de Posições Fixas específico para a empresa selecionada.
- O Pandas lê o arquivo garantindo que todos os campos sejam tratados como string (para preservar zeros à esquerda em CPFs e Contas).
### 🔄 Etapa 3.3: Transformação (The "Fold" Logic)
O sistema deve gerar dois DataFrames distintos:
1. DataFrame Web (1:1): Representação fiel do arquivo original com 40 colunas.
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
🐍 Agente Python/PandasResponsável pela lógica contida em services.py. Deve focar na função de leitura pd.read_fwf e na manipulação de DataFrames para a lógica de dobra A/B. Pandas Specialist: Criar o arquivo services.py com a lógica de read_fwf (fixed width file) e a concatenação horizontal (axis=1).
🎸 Agente Django
Responsável pela arquitetura do projeto, configuração de settings.py, models.py (para gerenciar os uploads) e views.py.
Django Architect: Estruturar models para salvar metadados dos arquivos e views para o fluxo de upload.
🎨 Agente Bootstrap
Responsável pela criação de formulários de upload limpos, tabelas de histórico de arquivos e botões de download. 
Frontend Dev: Criar uma dashboard simples com histórico de uploads e status de processamento.
Agente de Testes unitários
Resposável pelos testes unitários para a lógica de dobra A/B e a manipulação de DataFrames. Também pelas demais partes do sistema, como views, templates e forms.

## 6. Estrutura de Arquivos Sugerida
project_root/
├── core/                   # Configurações globais do projeto (settings.py, urls.py)
├── people/                 # App de cadastro e gestão de clientes
│   ├── models.py           # Modelos de Pessoa Jurídica (Empresas) e Pessoa Física (Contatos/Funcionários)
│   ├── admin.py            # Interface administrativa para gerir as 5 empresas ou mais e contatos
│   ├── views.py            # CRUD de clientes e listagem
│   └── urls.py             # Rotas do módulo de pessoas
├── processor/              # App do Motor ETL (O "Coração" do sistema)
│   ├── layouts.py          # Dicionários com posições fixas de cada empresa
│   ├── services.py         # Motor de processamento (Pandas: TXT -> CSV e Dobra A/B)
│   ├── models.py           # Registro de Uploads (FK para Empresa, Data, Arquivos Gerados)
│   ├── views.py            # Lógica de Upload, Processamento e Download
│   └── urls.py             # Rotas do módulo de processamento
├── templates/              # Interface HTML (Bootstrap 5)
│   ├── base.html           # Layout principal (Navbar/Footer)
│   ├── people/             # Telas de cadastro de clientes
│   └── processor/          # Telas de upload e histórico de holerites
└── media/                  # Repositório de arquivos (TXTs originais e CSVs gerados)

## 7. Implementação Atual (o que já foi feito)

### 7.1 Setup e Convenções do Repositório
- Ambiente virtual criado em `.venv/`.
- Dependências instaladas: `django` e `pandas`.
- Diretório de amostras padronizado como `sample_txt/` (onde ficam os arquivos TXT de exemplo).
- Banco de dados padrão: SQLite (`db.sqlite3`).

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
  - `/` -> upload de TXT (app `processor`)
  - `/uploads/` -> histórico de uploads e links de download (app `processor`)
  - `/people/` -> listagem simples de empresas (app `people`)
  - `/admin/` -> Django Admin
- Tela de login implementada em `templates/registration/login.html`.
- Não existe usuário/senha padrão: o primeiro acesso deve ser feito criando um superusuário.

### 7.4 Modelagem de dados implementada
#### App `people`
- `Empresa`
  - Campos principais: `name`, `cnpj` (somente dígitos, 14, único), `layout_type`, `is_active`, timestamps.
  - `layout_type` (choices): `FOLHAMATIC`, `RMLABORE_DEFAULT`, `RMLABORE_CUSTOM`, `GENESIS`, `CONTIMATIC`.
- `Contato`
  - FK para `Empresa` e campos básicos: `name`, `email`, `phone`, `role`, `is_active`, `created_at`.

#### App `processor`
- `Upload`
  - FK para `Empresa`, referência a usuário (`uploaded_by`), `original_file`.
  - Campos de controle: `status`, `row_count`, `error_message`, `processed_at`, `detected_layout_type`.
  - Saídas geradas: `web_csv` e `print_csv`.

### 7.5 Parsing e processamento de TXT (ETL)
- Implementado em `processor/services.py`.
- Os arquivos de exemplo em `sample_txt/` têm formato de relatório e variações por fornecedor; por isso o parsing foi implementado por layout com regras e posições baseadas nas amostras.
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
- `templates/people/companies_list.html`: listagem simples de empresas.

### 7.8 Admin
- Registro de modelos no Django Admin:
  - `people/admin.py`: `Empresa`, `Contato`
  - `processor/admin.py`: `Upload`

### 7.9 Testes unitários
- Testes básicos em `processor/tests.py`:
  - Parsing do layout GENESIS (amostra Orion)
  - Parsing do layout RM Labore Custom (amostra Vila Boa)
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
  - gera automaticamente um `layout_spec` (JSON) para parsing básico por “colunas” (fixed-width por blocos de texto).
- No cadastro de Empresa, o usuário deve selecionar um **Sistema/Layout pronto** (somente sistemas com `layout_spec` gerado aparecem para seleção).
- No processamento, o layout aplicado ao upload é definido por:
  - `empresa.source_system.code` (preferencial)
  - fallback para `empresa.layout_type` (compatibilidade com registros antigos)
- Diretório de amostras locais (não versionado): `processor/.sample_txt/` (ignorado no Git).

## 8. Comandos de execução (ordem recomendada)

### 8.1 Windows (PowerShell)
1. `python -m venv .venv`
2. `.\.venv\Scripts\Activate.ps1`
3. `pip install django pandas`
4. `python manage.py migrate`
5. `python manage.py createsuperuser`
6. `python manage.py seed_empresas`
7. `python manage.py runserver`

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
