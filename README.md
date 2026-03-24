# dashTi

Dashboard interno em Streamlit para acompanhamento operacional de TI, com persistencia em Google Sheets.

## Objetivo

O `dashTi` centraliza o acompanhamento de:

- projetos de TI;
- reunioes e agenda operacional;
- sprints semanais;
- chamados e historico de acompanhamento.

O projeto foi pensado para uso interno, com foco em rapidez de implantacao e simplicidade de operacao.

## Funcionalidades

- Dashboard executivo com indicadores e graficos de projetos.
- Cadastro, edicao, exclusao e acompanhamento de projetos.
- Controle de etapas com calculo automatico de progresso.
- Agenda de reunioes com calendario visual.
- Registro e historico de sprints semanais.
- Cadastro e acompanhamento de chamados.
- Persistencia em Google Sheets.

## Estrutura do Projeto

- [app.py](C:/Users/matheus.batista/Documents/GitHub/dashTi/app.py)
  Interface Streamlit e regras de interacao da tela.
- [utils.py](C:/Users/matheus.batista/Documents/GitHub/dashTi/utils.py)
  Regras de acesso a dados, cache, validacoes basicas e integracao com Google Sheets.
- [requirements.txt](C:/Users/matheus.batista/Documents/GitHub/dashTi/requirements.txt)
  Dependencias Python do projeto.
- [dashti.png](C:/Users/matheus.batista/Documents/GitHub/dashTi/dashti.png)
  Imagem usada na interface.
- [evoy.png](C:/Users/matheus.batista/Documents/GitHub/dashTi/evoy.png)
  Imagem usada na interface.
- [PLANO_SEGURANCA_E_MELHORIAS.md](C:/Users/matheus.batista/Documents/GitHub/dashTi/PLANO_SEGURANCA_E_MELHORIAS.md)
  Documento formal com riscos, prioridades e roadmap recomendado.

## Arquitetura Atual

### Aplicacao

- Frontend e backend no mesmo processo com Streamlit.
- Regras de tela implementadas em `app.py`.
- Regras de dados e integracao com Google Sheets implementadas em `utils.py`.

### Persistencia

- Fonte de dados principal: Google Sheets.
- A aplicacao cria/usa abas separadas para:
  - `projetos`
  - `reunioes`
  - `sprints`
  - `chamados`

### Seguranca atual

- Acesso por token em query string, se `TOKEN_ACESSO` estiver configurado.
- Credenciais da service account lidas via `st.secrets`.

Observacao:
Esse modelo atende cenario interno simples, mas nao deve ser considerado autenticacao corporativa robusta.

## Modelo de Dados

### Projetos

Campos principais:

- `ID`
- `Projeto`
- `Responsavel`
- `Prioridade`
- `Status`
- `Progresso (%)`
- `Etapas`
- `Inicio`
- `Prazo`
- `Horas Gastas`
- `Descricao`

### Reunioes

Campos principais:

- `Titulo`
- `Responsavel`
- `Participantes`
- `Empresa`
- `Data`
- `Horario`
- `Local`
- `Observacoes`

### Sprints

Campos principais:

- `Semana`
- `BU`
- `Responsavel`
- `Progressos`
- `Desafios`
- `Proxima Sprint`
- `Meta`
- `Realizado`

### Chamados

Campos principais:

- `ID`
- `Tipo`
- `Chave`
- `Resumo`
- `Criado`
- `Solicitante`
- `Fechado`
- `Situacao`
- `Fornecedor`
- `Onde Impacta`
- `Obs`

## Requisitos

- Python 3.11 ou superior
- Conta Google com acesso a uma planilha compartilhada
- Service account com permissao na planilha
- Arquivo de secrets configurado no Streamlit

## Dependencias

Dependencias atuais do projeto:

- `streamlit`
- `pandas`
- `plotly`
- `openpyxl`
- `streamlit-calendar`
- `gspread`
- `google-auth`
- `openai`
- `pymupdf`

Observacao:
`openai` e `pymupdf` nao estao sendo usados no fluxo principal atual e podem ser revisados futuramente.

## Configuracao

O projeto depende de secrets do Streamlit. Exemplo esperado em `.streamlit/secrets.toml`:

```toml
SHEET_ID = "ID_DA_PLANILHA"
TOKEN_ACESSO = "token-interno-opcional"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

Importante:

- Nunca commitar o arquivo de secrets.
- Compartilhar a planilha com o `client_email` da service account.

## Como Executar Localmente

Instale as dependencias:

```bash
pip install -r requirements.txt
```

Suba a aplicacao:

```bash
streamlit run app.py
```

## Fluxo Operacional Recomendado

### Projetos

- Cadastrar projeto com responsavel, prazo e etapas iniciais.
- Atualizar etapas conforme a execucao.
- Revisar atrasos semanalmente no dashboard.

### Reunioes

- Registrar reunioes no calendario.
- Usar observacoes para pauta e pendencias.

### Sprints

- Registrar uma sprint por responsavel e BU por semana.
- Atualizar historico ao final da semana.

### Chamados

- Cadastrar chamados com chave e resumo padronizados.
- Usar observacoes para historico cronologico.

## Melhorias Ja Aplicadas

- Projetos agora usam `ID` estavel para evitar edicao/exclusao do registro errado em listas filtradas.
- Chamados passaram a usar IDs unicos mais seguros para reduzir colisao.
- Escritas passaram a ler a planilha sem cache antes de salvar, reduzindo risco de sobrescrever visao desatualizada.
- Funcoes utilitarias foram documentadas com docstrings.

## Riscos Conhecidos

- Google Sheets nao e banco transacional; alteracoes simultaneas ainda podem causar conflito.
- O token na URL nao substitui login corporativo.
- O `devcontainer` atual sobe o Streamlit com CORS e XSRF desabilitados, adequado apenas para ambiente controlado.

## Recomendacoes Imediatas

- Fazer backup da planilha antes de mudancas estruturais.
- Restringir compartilhamento da planilha.
- Revisar dependencias nao utilizadas.
- Adotar versoes fixas em `requirements.txt`.
- Avaliar autenticacao corporativa no futuro.

## Documentacao Complementar

Consulte [PLANO_SEGURANCA_E_MELHORIAS.md](C:/Users/matheus.batista/Documents/GitHub/dashTi/PLANO_SEGURANCA_E_MELHORIAS.md) para o plano recomendado de seguranca, governanca e evolucao tecnica.
