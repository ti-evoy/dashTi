import pandas as pd
import os
import json
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

ARQUIVO_LOCAL_PROJETOS  = "data/projetos.xlsx"
ARQUIVO_LOCAL_REUNIOES  = "data/reunioes.xlsx"
ARQUIVO_LOCAL_SPRINTS   = "data/sprints_db.xlsx"

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
    return sh.worksheet(aba)

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

def _ler_aba(aba: str) -> pd.DataFrame:
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
def carregar_dados() -> pd.DataFrame:
    try:
        df = _ler_aba(ABA_PROJETOS)
        if df.empty:
            return pd.DataFrame(columns=[
                "Projeto","Responsável","Prioridade","Status","Progresso (%)",
                "Etapas","Início","Prazo","Horas Gastas","Descrição"
            ])
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
        return df
    except Exception as e:
        st.error(f"Erro ao carregar projetos: {e}")
        return pd.DataFrame()

def salvar_projeto(novo: dict):
    df = carregar_dados()
    novo_formatado = novo.copy()
    for col in ["Início","Prazo"]:
        if col in novo_formatado and hasattr(novo_formatado[col], 'strftime'):
            novo_formatado[col] = novo_formatado[col].strftime("%Y-%m-%d")
    df = pd.concat([df, pd.DataFrame([novo_formatado])], ignore_index=True)
    _salvar_aba(ABA_PROJETOS, df)

def atualizar_etapas(idx, etapas):
    df = carregar_dados().reset_index(drop=True)
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
        # Suporta "1,1,0,0" e "11000000"
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
def carregar_reunioes() -> pd.DataFrame:
    try:
        df = _ler_aba(ABA_REUNIOES)
        if df.empty:
            return pd.DataFrame(columns=[
                "Título","Responsável","Participantes","Empresa",
                "Data","Horário","Local","Observações"
            ])
        if "Data" in df.columns:
            df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
        return df.reset_index(drop=True)
    except Exception as e:
        st.error(f"Erro ao carregar reuniões: {e}")
        return pd.DataFrame()

def salvar_reuniao(nova: dict):
    df = carregar_reunioes()
    nova_fmt = nova.copy()
    if "Data" in nova_fmt and hasattr(nova_fmt["Data"], 'strftime'):
        nova_fmt["Data"] = nova_fmt["Data"].strftime("%Y-%m-%d")
    df = pd.concat([df, pd.DataFrame([nova_fmt])], ignore_index=True)
    _salvar_aba(ABA_REUNIOES, df)

def deletar_reuniao(index: int):
    df = carregar_reunioes()
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
    """
    Lê a aba sprints direto do Sheets SEM cache e SEM filtrar linhas.
    Garante todas as colunas existam. Usado pelo fluxo de salvamento.
    """
    ws   = _get_sheet(ABA_SPRINTS)
    data = ws.get_all_records(expected_headers=COLUNAS_SPRINTS)
    if not data:
        return pd.DataFrame(columns=COLUNAS_SPRINTS)
    df = pd.DataFrame(data)
    # Garante que todas as colunas existam
    for col in COLUNAS_SPRINTS:
        if col not in df.columns:
            df[col] = ""
    df = df[COLUNAS_SPRINTS]  # ordena colunas corretamente
    # Remove apenas linhas onde Semana E Responsável estão vazios (lixo real)
    df = df[~((df["Semana"].astype(str).str.strip() == "") &
              (df["Responsável"].astype(str).str.strip() == ""))]
    return df.reset_index(drop=True)

def carregar_sprints() -> pd.DataFrame:
    """
    Lê e prepara sprints para EXIBIÇÃO via cache.
    Normaliza BU e datas sem descartar linhas válidas.
    """
    try:
        df = _ler_aba(ABA_SPRINTS)
        if df.empty:
            return pd.DataFrame(columns=COLUNAS_SPRINTS)

        # Garante todas as colunas
        for col in COLUNAS_SPRINTS:
            if col not in df.columns:
                df[col] = ""

        # Remove linhas onde Semana E Responsável estão vazios
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
        # ✅ Força o formato com horário para o Sheets reconhecer corretamente
        nova["Semana"] = nova["Semana"].strftime("%Y-%m-%d 00:00:00")

    df = _ler_sprints_raw()
    nova_completa = {col: nova.get(col, "") for col in COLUNAS_SPRINTS}
    df = pd.concat([df, pd.DataFrame([nova_completa])], ignore_index=True)
    _salvar_aba(ABA_SPRINTS, df)
    _cache_invalidar(ABA_SPRINTS)