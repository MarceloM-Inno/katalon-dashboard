# Katalon Dashboard

Dashboard Streamlit para visualização de resultados de testes automatizados do **Katalon Studio**. Os dados são extraídos de relatórios JUnit XML e armazenados no **Supabase** (PostgreSQL).

## URLs

| Ambiente | URL |
|----------|-----|
| **Online** | https://katalon-dashboard-orvytfbxpxpsk2rntjc8ke.streamlit.app/ |
| **Local** | http://localhost:8501 |
| **Supabase** | https://supabase.com/dashboard/project/rodqhwzivsnxkfdenirx |
| **GitHub** | https://github.com/VictorOney/katalon-dashboard |

## Funcionalidades

- KPIs: total de execuções, testes passados/falhos, taxa de sucesso
- Gráfico de tendência de testes passados por suite
- Gráfico de falhas ao longo do tempo
- Distribuição por suite (barras agrupadas com percentuais)
- Pizza de status (PASSED / FAILED / ERROR / SKIPPED)
- Tabela detalhada com filtros (período, suites, status)
- Página "Execuções Diárias" com barras empilhadas por suite

## Stack

| Camada | Tecnologia |
|--------|------------|
| Frontend | Streamlit |
| Gráficos | Plotly |
| Dados | pandas |
| Banco | Supabase (PostgreSQL) |
| Ingestão | Python + requests |

## Estrutura do Projeto

```
katalon-dashboard/
├── app.py                      # Dashboard principal
├── config.py                   # Configuração (variáveis de ambiente)
├── db.py                       # Conexão com Supabase
├── visualizations.py           # Funções de renderização dos gráficos
├── schema.sql                  # DDL das tabelas no PostgreSQL
├── requirements.txt            # Dependências do dashboard
├── start.bat                   # Atalho para iniciar localmente
├── .env                        # Credenciais (IGNORADO pelo git)
├── .gitignore
│
├── pages/
│   └── 1_Execucoes_Diarias.py  # Página extra: execuções diárias
│
├── scripts/
│   ├── parse_and_send.py       # Script de ingestão dos XML → Supabase
│   ├── requirements.txt        # Dependências do script de ingestão
│   ├── run_scheduled.bat       # Batch para Task Scheduler (ingestão)
│   ├── watch_reports.py        # FileSystemWatcher (monitora novos XML)
│   ├── start_watcher.bat       # Atalho para iniciar o watcher manualmente
│   ├── install_watcher.ps1     # Instala o watcher como tarefa do Windows
│   ├── processed_state.json    # Controle de arquivos já processados
│   └── .env.example            # Exemplo de .env
```

## Banco de Dados (Supabase)

### Tabelas

**`test_executions`** — uma linha por execução de suite:
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | BIGSERIAL | PK |
| suite_name | TEXT | Nome da suite |
| execution_date | TIMESTAMPTZ | Data/hora da execução |
| total_tests | INTEGER | Total de testes |
| total_failures | INTEGER | Falhas |
| total_errors | INTEGER | Erros |
| total_skipped | INTEGER | Pulados |
| total_time_sec | DOUBLE | Duração total |
| hostname | TEXT | Máquina que executou |
| os | TEXT | Sistema operacional |
| browser | TEXT | Navegador |
| katalon_version | TEXT | Versão do Katalon |
| user_full_name | TEXT | Usuário |
| project_name | TEXT | Nome do projeto |

**`test_cases`** — cada caso de teste dentro de uma execução:
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | BIGSERIAL | PK |
| execution_id | BIGSERIAL | FK → test_executions.id |
| test_name | TEXT | Nome do caso de teste |
| duration_sec | DOUBLE | Duração |
| status | TEXT | PASSED / FAILED / ERROR / SKIPPED |
| failure_type | TEXT | Tipo da falha |
| failure_message | TEXT | Mensagem de erro |

## Como Rodar Localmente

### 1. Pré-requisitos
- Python 3.11+
- Git

### 2. Setup

```powershell
cd E:\Victor\Dashboard\katalon-dashboard
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Configurar credenciais

O arquivo `.env` já está configurado com a `service_role key` do Supabase.
Para novos ambientes, criar `.env` na raiz:

```
SUPABASE_URL=https://rodqhwzivsnxkfdenirx.supabase.co
SUPABASE_KEY=sua_chave_service_role
```

### 4. Executar

```powershell
streamlit run app.py --server.port 8501
```

Ou clique duas vezes em `start.bat`.

Acessar: http://localhost:8501

## Ingestão de Dados

### Origem

Os relatórios XML do Katalon ficam em:
```
E:\Pipeline-Report\[Suite-Data]\JUnit_Report.xml
```

### Ingestão Manual

```powershell
.venv\Scripts\Activate.ps1
python scripts/parse_and_send.py
```

O script é **idempotente**: verifica duplicados no banco e no `processed_state.json`, processando apenas arquivos novos.

### Automação (FileSystemWatcher)

O watcher monitora `E:\Pipeline-Report` em tempo real e executa a ingestão automaticamente:

- **Tarefa no Windows:** `KatalonDashboardWatcher` (inicia com o sistema)
- **Log:** `scripts/watcher.log`
- **Para iniciar manualmente:** `scripts\start_watcher.bat`

#### Fluxo:
```
Katalon finaliza teste → cria XML
       ↓ (segundos)
watch_reports.py detecta
       ↓ (5s de tolerância)
parse_and_send.py → Supabase
       ↓ (60s cache)
Dashboard atualiza
```

## Deploy (Streamlit Cloud)

O dashboard online está hospedado no **Streamlit Community Cloud**, conectado ao repositório GitHub.

O fluxo para atualizar:

```powershell
git add -A
git commit -m "Descrição das alterações"
git push origin main
```

O Streamlit Cloud auto-deploya automaticamente (geralmente leva 1-2 minutos).

### Credenciais no Online

As credenciais do Supabase no ambiente online estão configuradas em:

**https://share.streamlit.io/** → katalon-dashboard → Settings → Secrets

```toml
supabase_url = "https://rodqhwzivsnxkfdenirx.supabase.co"
supabase_key = "service_role_key"
```

## Cores Padrão

| Status | Cor |
|--------|-----|
| PASSED | `#2ecc71` (verde) |
| FAILED | `#e74c3c` (vermelho) |
| ERROR | `#f39c12` (laranja) |
| SKIPPED | `#95a5a6` (cinza) |
