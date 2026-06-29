# Dashboard de Testes - Katalon

Dashboard interativo para visualização de resultados de testes automatizados do **Katalon Studio**, construído com **Streamlit** e **Supabase**.

Suporta múltiplos projetos (ONEY e BNPL), com dados armazenados no mesmo banco e filtrados por projeto.

---

## Arquitetura

```
Pipeline-Report/  (JUnit XML gerado pelo Katalon)
       ↓
parse_and_send.py  (lê XMLs e envia via REST API)
       ↓
    Supabase  (PostgreSQL: test_executions + test_cases)
       ↑
  Streamlit App  (app.py + pages/)
```

---

## Estrutura do Projeto

```
katalon-dashboard/
├── app.py                    # Landing page + navegação entre páginas
├── config.py                 # Configurações (SUPABASE_URL, SUPABASE_KEY)
├── db.py                     # Conexão com Supabase e queries
├── visualizations.py         # Gráficos com Plotly
├── schema.sql                # DDL do banco de dados
├── requirements.txt          # Dependências do dashboard
├── start.bat                 # Atalho para iniciar o servidor
├── .env                      # Credenciais (NÃO versionado)
├── .gitignore
├── pages/
│   ├── 2_Inicio.py           # Seleção de projeto (ONEY / BNPL)
│   ├── 0_Graficos.py         # Dashboard geral com gráficos
│   └── 1_Execucoes_Diarias.py# Execuções diárias por suite
├── scripts/
│   ├── parse_and_send.py     # Parser JUnit XML → Supabase
│   ├── watch_reports.py      # Watcher em tempo real (opcional)
│   ├── executar_parse.bat    # Batch para Task Scheduler
│   ├── agendar_task.ps1      # Script para criar tarefa agendada
│   ├── install_watcher.ps1   # Script para instalar watcher
│   ├── start_watcher.bat     # Atalho para iniciar watcher manual
│   ├── .env.example          # Exemplo de .env para scripts
│   └── requirements.txt      # Dependências do parser
├── .streamlit/
│   └── config.toml           # Configurações do Streamlit
└── .devcontainer/
    └── devcontainer.json     # Configuração para GitHub Codespaces
```

---

## Banco de Dados (Supabase)

### Tabelas

**`test_executions`** — cada execução de uma suite de testes:
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | `BIGSERIAL PK` | ID único |
| `suite_name` | `TEXT` | Nome da suite |
| `execution_date` | `TIMESTAMPTZ` | Data da execução |
| `project` | `TEXT` | Projeto (ONEY / BNPL) |
| `total_tests` | `INTEGER` | Total de testes |
| `total_failures` | `INTEGER` | Total de falhas |
| `total_errors` | `INTEGER` | Total de erros |
| `total_skipped` | `INTEGER` | Testes ignorados |
| `total_time_sec` | `DOUBLE PRECISION` | Duração total |
| `hostname` | `TEXT` | Máquina que executou |
| `os`, `browser` | `TEXT` | SO e navegador |
| `katalon_version` | `TEXT` | Versão do Katalon |
| `project_name` | `TEXT` | Nome do projeto Katalon |
| `created_at` | `TIMESTAMPTZ` | Data de inserção |

**`test_cases`** — cada caso de teste individual:
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | `BIGSERIAL PK` | ID único |
| `execution_id` | `BIGINT FK` | Referência à execução |
| `project` | `TEXT` | Projeto (ONEY / BNPL) |
| `test_name` | `TEXT` | Nome do caso de teste |
| `duration_sec` | `DOUBLE PRECISION` | Duração em segundos |
| `status` | `TEXT` | PASSED, FAILED, ERROR, SKIPPED |
| `failure_type` | `TEXT` | Tipo da falha |
| `failure_message` | `TEXT` | Mensagem de erro |
| `created_at` | `TIMESTAMPTZ` | Data de inserção |

### Migração para adicionar projeto em dados existentes

```sql
ALTER TABLE test_executions ADD COLUMN project TEXT NOT NULL DEFAULT '';
ALTER TABLE test_cases ADD COLUMN project TEXT NOT NULL DEFAULT '';
UPDATE test_executions SET project = 'ONEY' WHERE project = '';
UPDATE test_cases SET project = 'ONEY' WHERE project = '';
```

---

## Fluxo do Parser (`parse_and_send.py`)

O script percorre a pasta `REPORT_PATH` procurando arquivos `JUnit_Report.xml` e envia os dados ao Supabase.

### Funcionamento

1. Lê `PROJECT_NAME` do `.env` (ONEY ou BNPL)
2. Busca todos `JUnit_Report.xml` recursivamente em `REPORT_PATH`
3. Para cada XML:
   - Extrai dados da suite (nome, data, totais)
   - Extrai propriedades (OS, browser, versão Katalon)
   - Extrai casos de teste (nome, status, duração, falha)
   - Envia via REST API para o Supabase
4. Controla duplicados via `processed_state.json` e consulta ao banco

### `.env` de exemplo

```ini
SUPABASE_URL=https://rodqhwzivsnxkfdenirx.supabase.co
SUPABASE_KEY=sb_publishable__...
REPORT_PATH=E:\Pipeline-Report
PROJECT_NAME=ONEY
```

---

## Dashboard Streamlit

### Páginas

| Página | Descrição |
|--------|-----------|
| **Início** | Cards para selecionar ONEY ou BNPL |
| **Gráficos** | KPIs, tendências por suite, falhas, distribuição por status, tabela detalhada |
| **Execuções Diárias** | Barras empilhadas (passados/falhas/erros) por suite ao longo do tempo |

### Filtros (sidebar)

- **Período** — date range
- **Suites** — checkbox por suite
- **Status** — PASSED / FAILED / ERROR / SKIPPED

---

## Setup

### 1. Clonar o repositório

```bash
git clone https://github.com/VictorOney/katalon-dashboard.git
cd katalon-dashboard
```

### 2. Criar arquivo `.env`

```ini
SUPABASE_URL=https://rodqhwzivsnxkfdenirx.supabase.co
SUPABASE_KEY=sb_publishable__...
```

### 3. Instalar dependências

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Criar as tabelas no Supabase

Acesse o SQL Editor do Supabase e execute o conteúdo de `schema.sql`.

### 5. Executar o parser (enviar dados)

```bash
cd scripts
python parse_and_send.py
```

### 6. Iniciar o dashboard

```bash
streamlit run app.py --server.port 8501
```

Acesse: http://localhost:8501

---

## VM02 — Projeto BNPL

Na segunda máquina virtual (VM02), configure o parser para enviar dados como `BNPL`:

1. Copie `scripts/parse_and_send.py` e `scripts/requirements.txt`
2. Crie `scripts/.env`:
   ```ini
   SUPABASE_URL=https://rodqhwzivsnxkfdenirx.supabase.co
   SUPABASE_KEY=sb_publishable__...
   REPORT_PATH=E:\Pipeline-Report
   PROJECT_NAME=BNPL
   ```
3. Instale dependências: `pip install -r scripts\requirements.txt`
4. Teste: `python scripts\parse_and_send.py`

### Agendar tarefa no Windows

**PowerShell como Administrador:**

```powershell
Set-ExecutionPolicy Bypass -Scope Process
.\scripts\agendar_task.ps1
```

Isso cria uma tarefa que executa o parser **todos os dias às 06:00**.

---

## Opcional — Watcher em Tempo Real

O `watch_reports.py` monitora a pasta de relatórios e executa o parser automaticamente quando novos XMLs são criados.

```bash
python scripts\watch_reports.py
```

Para instalar como serviço de inicialização:

```powershell
.\scripts\install_watcher.ps1
```

---

## Tecnologias

- **Python 3.11+**
- **Streamlit** — interface web
- **Plotly** — gráficos interativos
- **Supabase** — banco PostgreSQL + REST API
- **Pandas** — manipulação de dados
- **Watchdog** — monitoramento de arquivos (opcional)
