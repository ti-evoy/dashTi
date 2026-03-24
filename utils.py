import pandas as pd
import os
import json
import uuid
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date, timedelta
import streamlit as st

# ── Google Sheets config ──────────────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

ABA_PROJETOS  = "projetos"
ABA_REUNIOES  = "reunioes"
ABA_SPRINTS   = "sprints"
ABA_CHAMADOS  = "chamados"

ARQUIVO_LOCAL_PROJETOS  = "data/projetos.xlsx"
ARQUIVO_LOCAL_REUNIOES  = "data/reunioes.xlsx"
ARQUIVO_LOCAL_SPRINTS   = "data/sprints_db.xlsx"

COLUNAS_PROJETOS = [
    "ID", "Projeto", "Responsável", "Prioridade", "Status", "Progresso (%)",
    "Etapas", "Início", "Prazo", "Horas Gastas", "Descrição"
]

COLUNAS_REUNIOES = [
    "Título", "Responsável", "Participantes", "Empresa",
    "Data", "Horário", "Local", "Observações"
]

# ── Checkboxes de progresso ───────────────────────────────────────────────────
ETAPAS_PROJETO = [
    "Levantamento de requisitos",
    "Aprovação do escopo",
    "Desenvolvimento / Execução",
    "Testes e validação",
    "Homologação com cliente",
    "Documentação",
    "Deploy / Entrega",
    "Encerramento e lições aprendidas",
]

BUS_VALIDAS = ["Estratégia & Projetos", "Governança & Sustentação"]

COLUNAS_SPRINTS = [
    "Semana", "BU", "Responsável", "Progressos",
    "Desafios", "Próxima Sprint", "Meta", "Realizado"
]

COLUNAS_CHAMADOS = [
    "ID", "Tipo", "Chave", "Resumo", "Criado", "Solicitante",
    "Fechado", "Situação", "Fornecedor", "Onde Impacta", "Obs"
]

SITUACOES_CHAMADO = ["Aberto", "Em Andamento", "Atendido", "Cancelado", "Aguardando"]

def _normalizar_bu(bu):
    if pd.isna(bu): return bu
    bu_str = str(bu).strip()
    if bu_str in BUS_VALIDAS:
        return bu_str
    bu_lower = (bu_str.lower()
        .replace("ã", "a").replace("â", "a").replace("á", "a")
        .replace("ç", "c").replace("ê", "e").replace("é", "e")
        .replace("õ", "o").replace("ó", "o").replace("ú", "u")
        .replace("í", "i").strip()
    )
    if "govern" in bu_lower or "sustent" in bu_lower:
        return "Governança & Sustentação"
    if "estrat" in bu_lower or "projeto" in bu_lower:
        return "Estratégia & Projetos"
    return bu_str

def calcular_progresso(etapas_concluidas):
    return round((sum(etapas_concluidas) / len(ETAPAS_PROJETO)) * 100)

def _gerar_id(prefixo: str) -> str:
    return f"{prefixo}-{uuid.uuid4().hex[:8].upper()}"

def _garantir_colunas(df: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
    df2 = df.copy()
    for col in colunas:
        if col not in df2.columns:
            df2[col] = ""
    return df2[colunas]

# ── Conexão Google Sheets ─────────────────────────────────────────────────────
@st.cache_resource
def _get_client():
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)

def _get_sheet(aba: str):
    client = _get_client()
    sheet_id = st.secrets["SHEET_ID"]
    sh = client.open_by_key(sheet_id)
    try:
        return sh.worksheet(aba)
    except gspread.exceptions.WorksheetNotFound:
        # Cria a aba se não existir
        ws = sh.add_worksheet(title=aba, rows=1000, cols=20)
        return ws

# ── Cache com session_state ───────────────────────────────────────────────────
_CACHE_TTL_SEGUNDOS = 30
_CACHE_POS_SAVE_TTL = 20

def _cache_key(aba):
    return f"__aba_cache_{aba}"

def _cache_ts_key(aba):
    return f"__aba_cache_ts_{aba}"

def _cache_get(aba: str):
    key    = _cache_key(aba)
    ts_key = _cache_ts_key(aba)
    if key in st.session_state and ts_key in st.session_state:
        idade = (datetime.now() - st.session_state[ts_key]).total_seconds()
        if idade < _CACHE_TTL_SEGUNDOS:
            return st.session_state[key]
    return None

def _cache_set(aba: str, df: pd.DataFrame, ttl: int = _CACHE_TTL_SEGUNDOS):
    st.session_state[_cache_key(aba)]    = df.copy()
    st.session_state[_cache_ts_key(aba)] = datetime.now()

def _cache_invalidar(aba: str):
    if _cache_key(aba) in st.session_state:
        del st.session_state[_cache_key(aba)]
    if _cache_ts_key(aba) in st.session_state:
        del st.session_state[_cache_ts_key(aba)]

def _ler_aba(aba: str, use_cache: bool = True) -> pd.DataFrame:
    if use_cache:
        cached = _cache_get(aba)
        if cached is not None:
            return cached
    ws   = _get_sheet(aba)
    data = ws.get_all_records()
    df   = pd.DataFrame(data) if data else pd.DataFrame()
    _cache_set(aba, df)
    return df

def _salvar_aba(aba: str, df: pd.DataFrame):
    ws  = _get_sheet(aba)
    df2 = df.copy()
    for col in df2.columns:
        if pd.api.types.is_datetime64_any_dtype(df2[col]):
            df2[col] = df2[col].dt.strftime("%Y-%m-%d").fillna("")
    df2 = df2.fillna("").astype(str)
    ws.clear()
    ws.update([df2.columns.tolist()] + df2.values.tolist())
    _cache_set(aba, df, ttl=_CACHE_POS_SAVE_TTL)

# ── Projetos ──────────────────────────────────────────────────────────────────
def carregar_dados(use_cache: bool = True) -> pd.DataFrame:
    try:
        df = _ler_aba(ABA_PROJETOS, use_cache=use_cache)
        if df.empty:
            return pd.DataFrame(columns=COLUNAS_PROJETOS)

        mudou_schema = False
        if "ID" not in df.columns:
            df["ID"] = [f"PRJ-{i+1:04d}" for i in range(len(df))]
            mudou_schema = True

        df = _garantir_colunas(df, COLUNAS_PROJETOS)

        for col in ["Início","Prazo"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        if "Progresso (%)" in df.columns:
            df["Progresso (%)"] = pd.to_numeric(df["Progresso (%)"], errors="coerce").fillna(0)
        if "Prioridade" not in df.columns: df["Prioridade"] = "Média"
        if "Etapas"     not in df.columns: df["Etapas"] = ""

        def _recalc(row):
            val = str(row.get("Etapas",""))
            if val and val not in ("nan","") and int(row.get("Progresso (%)", 0)) == 0:
                if "," in val:
                    bits = val.split(",")
                else:
                    bits = list(val.strip())
                feitas = sum(1 for b in bits if b.strip() == "1")
                total  = len(ETAPAS_PROJETO)
                return round((feitas / total) * 100)
            return row.get("Progresso (%)", 0)

        df["Progresso (%)"] = df.apply(_recalc, axis=1)
        if mudou_schema:
            _salvar_aba(ABA_PROJETOS, df)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar projetos: {e}")
        return pd.DataFrame()

def salvar_projeto(novo: dict):
    df = carregar_dados(use_cache=False)
    novo_formatado = novo.copy()
    if "ID" not in novo_formatado or not novo_formatado["ID"]:
        novo_formatado["ID"] = _gerar_id("PRJ")
    for col in ["Início","Prazo"]:
        if col in novo_formatado and hasattr(novo_formatado[col], 'strftime'):
            novo_formatado[col] = novo_formatado[col].strftime("%Y-%m-%d")
    novo_formatado = {col: novo_formatado.get(col, "") for col in COLUNAS_PROJETOS}
    df = _garantir_colunas(df, COLUNAS_PROJETOS)
    df = pd.concat([df, pd.DataFrame([novo_formatado])], ignore_index=True)
    _salvar_aba(ABA_PROJETOS, df)

def atualizar_projeto(projeto_id: str, dados: dict):
    """Atualiza campos de um projeto existente pelo ID."""
    df = carregar_dados(use_cache=False).reset_index(drop=True)
    mask = df["ID"].astype(str) == str(projeto_id)
    if not mask.any():
        return
    idx = df.index[mask][0]
    for campo, valor in dados.items():
        if campo in df.columns:
            df.at[idx, campo] = valor
    _salvar_aba(ABA_PROJETOS, df)

def deletar_projeto(projeto_id: str):
    """Remove um projeto pelo ID."""
    df = carregar_dados(use_cache=False).reset_index(drop=True)
    df = df[df["ID"].astype(str) != str(projeto_id)].reset_index(drop=True)
    _salvar_aba(ABA_PROJETOS, df)

def atualizar_etapas(projeto_id: str, etapas):
    df = carregar_dados(use_cache=False).reset_index(drop=True)
    mask = df["ID"].astype(str) == str(projeto_id)
    if not mask.any():
        return
    idx = df.index[mask][0]
    etapas_str = ",".join(["1" if e else "0" for e in etapas])
    progresso  = calcular_progresso(etapas)
    df.at[idx, "Etapas"]        = etapas_str
    df.at[idx, "Progresso (%)"] = progresso
    if progresso == 100:
        df.at[idx, "Status"] = "Concluído"
    _salvar_aba(ABA_PROJETOS, df)

def get_etapas(row):
    val = str(row.get("Etapas",""))
    if val and val != "nan":
        if "," in val:
            bits = val.split(",")
        else:
            bits = list(val.strip())
        result = [b.strip() == "1" for b in bits]
        while len(result) < len(ETAPAS_PROJETO): result.append(False)
        return result[:len(ETAPAS_PROJETO)]
    return [False] * len(ETAPAS_PROJETO)

def projetos_atrasados(df):
    hoje = pd.Timestamp(datetime.today().date())
    mask = (df["Prazo"] < hoje) & (df["Status"] != "Concluído")
    return df[mask]

# ── Reuniões ──────────────────────────────────────────────────────────────────
def carregar_reunioes(use_cache: bool = True) -> pd.DataFrame:
    try:
        df = _ler_aba(ABA_REUNIOES, use_cache=use_cache)
        if df.empty:
            return pd.DataFrame(columns=COLUNAS_REUNIOES)
        df = _garantir_colunas(df, COLUNAS_REUNIOES)
        if "Data" in df.columns:
            df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        return df.reset_index(drop=True)
    except Exception as e:
        st.error(f"Erro ao carregar reuniões: {e}")
        return pd.DataFrame()

def salvar_reuniao(nova: dict):
    df = carregar_reunioes(use_cache=False)
    nova_fmt = nova.copy()
    if "Data" in nova_fmt and hasattr(nova_fmt["Data"], 'strftime'):
        nova_fmt["Data"] = nova_fmt["Data"].strftime("%Y-%m-%d")
    nova_fmt = {col: nova_fmt.get(col, "") for col in COLUNAS_REUNIOES}
    df = _garantir_colunas(df, COLUNAS_REUNIOES)
    df = pd.concat([df, pd.DataFrame([nova_fmt])], ignore_index=True)
    _salvar_aba(ABA_REUNIOES, df)

def deletar_reuniao(index: int):
    df = carregar_reunioes(use_cache=False)
    df = df.drop(index=index).reset_index(drop=True)
    _salvar_aba(ABA_REUNIOES, df)

# ── Sprints ───────────────────────────────────────────────────────────────────
def segunda_da_semana():
    hoje = date.today()
    return hoje - timedelta(days=hoje.weekday())

def proxima_segunda():
    hoje = date.today()
    dias = (7 - hoje.weekday()) % 7
    return hoje + timedelta(days=dias if dias != 0 else 7)

def _ler_sprints_raw() -> pd.DataFrame:
    ws   = _get_sheet(ABA_SPRINTS)
    data = ws.get_all_records(expected_headers=COLUNAS_SPRINTS)
    if not data:
        return pd.DataFrame(columns=COLUNAS_SPRINTS)
    df = pd.DataFrame(data)
    for col in COLUNAS_SPRINTS:
        if col not in df.columns:
            df[col] = ""
    df = df[COLUNAS_SPRINTS]
    df = df[~((df["Semana"].astype(str).str.strip() == "") &
              (df["Responsável"].astype(str).str.strip() == ""))]
    return df.reset_index(drop=True)

def carregar_sprints(use_cache: bool = True) -> pd.DataFrame:
    try:
        df = _ler_aba(ABA_SPRINTS, use_cache=use_cache)
        if df.empty:
            return pd.DataFrame(columns=COLUNAS_SPRINTS)
        for col in COLUNAS_SPRINTS:
            if col not in df.columns:
                df[col] = ""
        df = df[~((df["Semana"].astype(str).str.strip() == "") &
                  (df["Responsável"].astype(str).str.strip() == ""))]
        if "Semana" in df.columns:
            df["Semana"] = pd.to_datetime(df["Semana"], errors="coerce")
            df = df.dropna(subset=["Semana"])
        if "BU" in df.columns:
            df["BU"] = df["BU"].apply(_normalizar_bu)
        return df.reset_index(drop=True)
    except Exception as e:
        st.error(f"Erro ao carregar sprints: {e}")
        return pd.DataFrame()

def salvar_sprint(nova: dict):
    if "BU" in nova:
        nova["BU"] = _normalizar_bu(nova["BU"])
    if "Semana" in nova and hasattr(nova["Semana"], 'strftime'):
        nova["Semana"] = nova["Semana"].strftime("%Y-%m-%d 00:00:00")
    df = carregar_sprints(use_cache=False)
    nova_completa = {col: nova.get(col, "") for col in COLUNAS_SPRINTS}
    df = pd.concat([df, pd.DataFrame([nova_completa])], ignore_index=True)
    _salvar_aba(ABA_SPRINTS, df)
    _cache_invalidar(ABA_SPRINTS)

def atualizar_sprint(idx: int, dados: dict):
    """Atualiza campos de uma sprint existente pelo índice (no df carregado)."""
    df = carregar_sprints(use_cache=False)
    if idx >= len(df):
        return
    for campo, valor in dados.items():
        if campo in df.columns:
            df.at[idx, campo] = valor
    _salvar_aba(ABA_SPRINTS, df)
    _cache_invalidar(ABA_SPRINTS)

# ── Chamados ──────────────────────────────────────────────────────────────────
def _gerar_id_chamado(df: pd.DataFrame) -> str:
    while True:
        novo_id = _gerar_id("CHM")
        if df.empty or "ID" not in df.columns:
            return novo_id
        if not (df["ID"].astype(str) == novo_id).any():
            return novo_id

def carregar_chamados(use_cache: bool = True) -> pd.DataFrame:
    try:
        df = _ler_aba(ABA_CHAMADOS, use_cache=use_cache)
        if df.empty:
            return pd.DataFrame(columns=COLUNAS_CHAMADOS)
        for col in COLUNAS_CHAMADOS:
            if col not in df.columns:
                df[col] = ""
        for col in ["Criado", "Fechado"]:
            if col in df.columns:
                df[col] = df[col].astype(str)
        return df.reset_index(drop=True)
    except Exception as e:
        st.error(f"Erro ao carregar chamados: {e}")
        return pd.DataFrame()

def salvar_chamado(novo: dict):
    df = carregar_chamados(use_cache=False)
    if "ID" not in novo or not novo["ID"]:
        novo["ID"] = _gerar_id_chamado(df)
    novo_completo = {col: novo.get(col, "") for col in COLUNAS_CHAMADOS}
    df = pd.concat([df, pd.DataFrame([novo_completo])], ignore_index=True)
    _salvar_aba(ABA_CHAMADOS, df)
    _cache_invalidar(ABA_CHAMADOS)

def atualizar_chamado(idx: int, dados: dict):
    df = carregar_chamados(use_cache=False)
    for campo, valor in dados.items():
        if campo in df.columns:
            df.at[idx, campo] = valor
    _salvar_aba(ABA_CHAMADOS, df)
    _cache_invalidar(ABA_CHAMADOS)

def deletar_chamado(idx: int):
    df = carregar_chamados(use_cache=False)
    df = df.drop(index=idx).reset_index(drop=True)
    _salvar_aba(ABA_CHAMADOS, df)
    _cache_invalidar(ABA_CHAMADOS)
