import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from utils import (
    carregar_dados, salvar_projeto, projetos_atrasados,
    atualizar_etapas, get_etapas, ETAPAS_PROJETO,
    carregar_reunioes, salvar_reuniao, deletar_reuniao,
    carregar_sprints, salvar_sprint, segunda_da_semana, proxima_segunda,
)

st.set_page_config(page_title="Dashboard TI · Evoy", page_icon="🟢", layout="wide")

# ── Proteção por token ────────────────────────────────────────────────────────
_token_valido = st.secrets.get("TOKEN_ACESSO", "")
_token_url    = st.query_params.get("token", "")
if _token_valido and _token_url != _token_valido:
    st.error("🔒 Acesso não autorizado. Verifique o link com sua equipe.")
    st.stop()

# ── CSS Evoy Brand ────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Roboto', sans-serif;
    background-color: #051a0e !important;
    color: #e8f5ec !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #051a0e; }
::-webkit-scrollbar-thumb { background: #00d23c; border-radius: 4px; }

/* ── Main container ── */
.block-container {
    padding: 1.5rem 2rem 3rem 2rem !important;
    max-width: 100% !important;
}

/* ── Header ── */
header[data-testid="stHeader"] {
    background: #051a0e !important;
    border-bottom: 1px solid rgba(0,210,60,0.15);
}

/* ── Sidebar ── */
div[data-testid="stSidebar"] {
    background: #020f07 !important;
    border-right: 1px solid rgba(0,210,60,0.12);
}
div[data-testid="stSidebar"] * { color: #b8d4bf !important; }
div[data-testid="stSidebar"] .stTextInput input,
div[data-testid="stSidebar"] .stMultiSelect div {
    background: #0a2214 !important;
    border-color: rgba(0,210,60,0.2) !important;
    color: #e8f5ec !important;
}
div[data-testid="stSidebar"] h1 {
    color: #00d23c !important;
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
}
div[data-testid="stSidebar"] .stButton button {
    background: rgba(0,210,60,0.1) !important;
    border: 1px solid rgba(0,210,60,0.3) !important;
    color: #00d23c !important;
    border-radius: 2px !important;
}
div[data-testid="stSidebar"] .stButton button:hover {
    background: #00d23c !important;
    color: #020f07 !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid rgba(0,210,60,0.15) !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #6b8f74 !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    padding: 0.6rem 1.2rem !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    transition: all 0.2s !important;
}
.stTabs [aria-selected="true"] {
    color: #00d23c !important;
    border-bottom: 2px solid #00d23c !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab"]:hover { color: #00d23c !important; }

/* ── Inputs & Forms ── */
.stTextInput input, .stTextArea textarea, .stNumberInput input,
.stSelectbox div[data-baseweb="select"] > div,
.stMultiSelect div[data-baseweb="select"] > div {
    background: #071f10 !important;
    border: 1px solid rgba(0,210,60,0.2) !important;
    border-radius: 2px !important;
    color: #e8f5ec !important;
    font-family: 'Roboto', sans-serif !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #00d23c !important;
    box-shadow: 0 0 0 1px #00d23c !important;
}

/* ── Date input ── */
.stDateInput input {
    background: #071f10 !important;
    border: 1px solid rgba(0,210,60,0.2) !important;
    color: #e8f5ec !important;
    border-radius: 2px !important;
}

/* ── Buttons ── */
.stButton button, .stFormSubmitButton button {
    background: #00d23c !important;
    color: #020f07 !important;
    border: none !important;
    border-radius: 2px !important;
    font-weight: 700 !important;
    font-family: 'Roboto', sans-serif !important;
    letter-spacing: 0.04em !important;
    transition: all 0.2s !important;
    clip-path: polygon(0 0, calc(100% - 10px) 0, 100% 100%, 10px 100%) !important;
}
.stButton button:hover, .stFormSubmitButton button:hover {
    background: #00f545 !important;
    transform: translateY(-1px) !important;
}
button[kind="secondary"] {
    background: transparent !important;
    border: 1px solid rgba(0,210,60,0.3) !important;
    color: #00d23c !important;
    clip-path: polygon(0 0, calc(100% - 8px) 0, 100% 100%, 8px 100%) !important;
}

/* ── Metrics ── */
div[data-testid="stMetric"] {
    background: #071f10 !important;
    border: 1px solid rgba(0,210,60,0.12) !important;
    border-left: 3px solid #00d23c !important;
    padding: 1rem 1.2rem !important;
    border-radius: 0 2px 2px 0 !important;
    position: relative;
    overflow: hidden;
}
div[data-testid="stMetric"]::before {
    content: '';
    position: absolute;
    top: 0; right: 0;
    width: 40px; height: 100%;
    background: linear-gradient(135deg, transparent 50%, rgba(0,210,60,0.05) 50%);
}
div[data-testid="stMetric"] label {
    color: #6b8f74 !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #e8f5ec !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
}

/* ── Expanders ── */
.streamlit-expanderHeader {
    background: #071f10 !important;
    border: 1px solid rgba(0,210,60,0.12) !important;
    border-left: 3px solid rgba(0,210,60,0.4) !important;
    color: #e8f5ec !important;
    border-radius: 0 2px 2px 0 !important;
    font-size: 0.85rem !important;
}
.streamlit-expanderHeader:hover {
    border-left-color: #00d23c !important;
    background: #0a2214 !important;
}
.streamlit-expanderContent {
    background: #071f10 !important;
    border: 1px solid rgba(0,210,60,0.08) !important;
    border-top: none !important;
}

/* ── Progress bar ── */
.stProgress > div > div {
    background: #0a2214 !important;
    border-radius: 0 !important;
    height: 4px !important;
}
.stProgress > div > div > div {
    background: linear-gradient(90deg, #00d23c, #beff00) !important;
    border-radius: 0 !important;
    clip-path: polygon(0 0, calc(100% - 4px) 0, 100% 100%, 0 100%) !important;
}

/* ── Checkboxes ── */
.stCheckbox label { color: #b8d4bf !important; font-size: 0.85rem !important; }
.stCheckbox input:checked + div { background: #00d23c !important; border-color: #00d23c !important; }

/* ── Alerts ── */
.stSuccess { background: rgba(0,210,60,0.1) !important; border-color: #00d23c !important; color: #00d23c !important; }
.stError   { background: rgba(255,30,50,0.08) !important; border-color: #ff1e32 !important; }
.stWarning { background: rgba(190,255,0,0.08) !important; border-color: #beff00 !important; }
.stInfo    { background: rgba(0,200,210,0.08) !important; border-color: #00c8d2 !important; }

/* ── Divider ── */
hr { border-color: rgba(0,210,60,0.1) !important; }

/* ── Download button ── */
.stDownloadButton button {
    background: transparent !important;
    border: 1px solid rgba(0,210,60,0.3) !important;
    color: #00d23c !important;
}

/* ── Slider ── */
.stSlider [data-baseweb="slider"] [role="slider"] { background: #00d23c !important; }
.stSlider [data-baseweb="slider"] div[class*="Track"] { background: #0a2214 !important; }
.stSlider [data-baseweb="slider"] div[class*="Track"]:last-child { background: #00d23c !important; }

/* ── Selectbox dropdown ── */
[data-baseweb="popover"] { background: #071f10 !important; border: 1px solid rgba(0,210,60,0.2) !important; }
[data-baseweb="menu"] { background: #071f10 !important; }
[data-baseweb="menu"] li { color: #e8f5ec !important; }
[data-baseweb="menu"] li:hover { background: rgba(0,210,60,0.1) !important; }

/* ── Toast ── */
[data-testid="toastContainer"] { background: #071f10 !important; border: 1px solid #00d23c !important; }

/* ── Evoy Components ── */
.evoy-page-title {
    font-size: 1.6rem;
    font-weight: 700;
    color: #e8f5ec;
    letter-spacing: -0.01em;
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 1.2rem;
    padding-bottom: 0.8rem;
    border-bottom: 1px solid rgba(0,210,60,0.15);
}
.evoy-page-title span.accent {
    color: #00d23c;
}
.evoy-page-title::before {
    content: '';
    display: inline-block;
    width: 14px;
    height: 14px;
    background: #00d23c;
    clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%);
}

.evoy-kpi-row {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 10px;
    margin-bottom: 1.5rem;
}

.evoy-section-label {
    font-size: 0.7rem;
    font-weight: 700;
    color: #00d23c;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 0.6rem;
    display: flex;
    align-items: center;
    gap: 6px;
}
.evoy-section-label::before {
    content: '/';
    color: rgba(0,210,60,0.4);
}

.evoy-sprint-card {
    background: #071f10;
    border: 1px solid rgba(0,210,60,0.1);
    border-left: 3px solid #00d23c;
    padding: 1rem 1.2rem;
    margin-bottom: 0.6rem;
    position: relative;
    overflow: hidden;
}
.evoy-sprint-card::after {
    content: '';
    position: absolute;
    bottom: 0; right: 0;
    width: 30px; height: 30px;
    border-right: 2px solid rgba(0,210,60,0.15);
    border-bottom: 2px solid rgba(0,210,60,0.15);
}
.evoy-sprint-card h4 { margin: 0 0 0.3rem 0; color: #e8f5ec; font-size: 0.88rem; font-weight: 600; }
.evoy-sprint-card p  { margin: 0.1rem 0; color: #6b8f74; font-size: 0.78rem; }

.evoy-tag {
    display: inline-block;
    padding: 1px 8px;
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    border-radius: 1px;
    clip-path: polygon(0 0, calc(100% - 6px) 0, 100% 100%, 6px 100%);
}
.evoy-tag-alta   { background: rgba(255,30,50,0.15); color: #ff4060; }
.evoy-tag-media  { background: rgba(190,255,0,0.12); color: #beff00; }
.evoy-tag-baixa  { background: rgba(0,210,60,0.12); color: #00d23c; }

.evoy-reunion-row {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    padding: 0.8rem 0;
    border-bottom: 1px solid rgba(0,210,60,0.07);
}
.evoy-reunion-date {
    min-width: 52px;
    text-align: center;
    background: #0a2214;
    border: 1px solid rgba(0,210,60,0.15);
    padding: 0.4rem;
    font-size: 0.7rem;
    color: #6b8f74;
}
.evoy-reunion-date strong { display: block; font-size: 1.2rem; color: #00d23c; font-weight: 700; }

.evoy-proj-bar-wrap {
    margin-bottom: 10px;
}
.evoy-proj-bar-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 3px;
    font-size: 0.8rem;
}
.evoy-proj-bar-header .proj-name { color: #e8f5ec; font-weight: 500; }
.evoy-proj-bar-header .proj-pct  { font-weight: 700; font-size: 0.72rem; }
.evoy-prog-track {
    height: 3px;
    background: #0a2214;
    position: relative;
}
.evoy-prog-fill {
    height: 100%;
    clip-path: polygon(0 0, calc(100% - 3px) 0, 100% 100%, 0 100%);
}
</style>
""", unsafe_allow_html=True)

# ── Dados globais ─────────────────────────────────────────────────────────────
df = carregar_dados()

CORES_STATUS = {
    "Em andamento": "#00d23c",
    "Concluído":    "#beff00",
    "Atrasado":     "#ff1e32",
    "Pausado":      "#f59e0b",
}
PRIO_ORDEM = {"Alta": 0, "Média": 1, "Baixa": 2}

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Roboto", color="#6b8f74", size=11),
    margin=dict(t=10, b=10, l=10, r=10),
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding: 0.8rem 0 1rem 0;'>
      <div style='font-size:1.3rem;font-weight:900;color:#00d23c;letter-spacing:-0.02em;line-height:1'>
        ev<span style='color:#beff00'>oy</span>
      </div>
      <div style='font-size:0.62rem;color:#3d6647;letter-spacing:0.15em;text-transform:uppercase;margin-top:2px'>
        Dashboard TI
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    st.markdown('<div class="evoy-section-label">Filtros</div>', unsafe_allow_html=True)
    busca = st.text_input("", placeholder="🔍  Pesquisar projeto...")
    responsaveis = st.multiselect(
        "Responsável",
        options=sorted(df["Responsável"].dropna().unique()) if not df.empty else [],
    )
    status_filtro = st.multiselect(
        "Status", options=["Em andamento", "Concluído", "Atrasado", "Pausado"],
    )
    prio_filtro = st.multiselect("Prioridade", options=["Alta", "Média", "Baixa"])
    progresso_range = st.slider("Progresso (%)", 0, 100, (0, 100))
    st.divider()
    st.button("↺  Atualizar", use_container_width=True)

# ── Aplica filtros ────────────────────────────────────────────────────────────
df_filtrado = df.copy()
if busca:
    df_filtrado = df_filtrado[df_filtrado["Projeto"].str.contains(busca, case=False, na=False)]
if responsaveis:
    df_filtrado = df_filtrado[df_filtrado["Responsável"].isin(responsaveis)]
if status_filtro:
    df_filtrado = df_filtrado[df_filtrado["Status"].isin(status_filtro)]
if prio_filtro:
    df_filtrado = df_filtrado[df_filtrado["Prioridade"].isin(prio_filtro)]
if "Progresso (%)" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["Progresso (%)"].between(progresso_range[0], progresso_range[1])]

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_dash, tab_projetos, tab_novo, tab_cal, tab_sprint = st.tabs([
    "📈  Visão Geral", "📋  Projetos", "＋  Novo Projeto", "📅  Calendário", "🏃  Sprint"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
with tab_dash:
    st.markdown('<div class="evoy-page-title">Visão <span class="accent">Geral</span></div>', unsafe_allow_html=True)

    if df.empty:
        st.info("Nenhum projeto cadastrado ainda. Bora começar? 🚀")
    else:
        total        = len(df_filtrado)
        em_andamento = len(df_filtrado[df_filtrado["Status"] == "Em andamento"])
        concluidos   = len(df_filtrado[df_filtrado["Status"] == "Concluído"])
        atrasados_n  = len(projetos_atrasados(df_filtrado)) if not df_filtrado.empty else 0
        media_prog   = df_filtrado["Progresso (%)"].mean() if not df_filtrado.empty else 0

        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("Total de Projetos", total)
        c2.metric("Em Andamento", em_andamento)
        c3.metric("Concluídos", concluidos)
        c4.metric("⚠ Atrasados", atrasados_n,
                  delta=f"-{atrasados_n}" if atrasados_n > 0 else None, delta_color="inverse")
        c5.metric("Progresso Médio", f"{media_prog:.0f}%")

        st.divider()

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown('<div class="evoy-section-label">Status dos Projetos</div>', unsafe_allow_html=True)
            cnt = df_filtrado["Status"].value_counts().reset_index()
            cnt.columns = ["Status","Qtd"]
            fig = px.pie(cnt, names="Status", values="Qtd",
                         color="Status", color_discrete_map=CORES_STATUS, hole=0.55)
            fig.update_traces(textfont_color="#020f07", textfont_size=11,
                              marker=dict(line=dict(color="#051a0e", width=2)))
            fig.update_layout(**PLOTLY_LAYOUT,
                              legend=dict(orientation="h", yanchor="bottom", y=-0.2,
                                          font=dict(color="#6b8f74")))
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            st.markdown('<div class="evoy-section-label">Progresso por Projeto</div>', unsafe_allow_html=True)
            if not df_filtrado.empty:
                df_p = df_filtrado[["Projeto","Progresso (%)","Status"]].sort_values("Progresso (%)")
                fig2 = go.Figure(go.Bar(
                    x=df_p["Progresso (%)"], y=df_p["Projeto"], orientation="h",
                    marker_color=df_p["Status"].map(CORES_STATUS).fillna("#3d6647").tolist(),
                    text=df_p["Progresso (%)"].astype(int).astype(str)+"%",
                    textposition="outside",
                    textfont=dict(color="#6b8f74", size=10),
                ))
                fig2.update_layout(**PLOTLY_LAYOUT,
                                   xaxis=dict(range=[0,120], showgrid=False, zeroline=False,
                                              showticklabels=False),
                                   yaxis=dict(showgrid=False, tickfont=dict(color="#b8d4bf", size=10)),
                                   showlegend=False)
                st.plotly_chart(fig2, use_container_width=True)

        col_c, col_d = st.columns(2)
        with col_c:
            st.markdown('<div class="evoy-section-label">Projetos por Responsável</div>', unsafe_allow_html=True)
            if not df_filtrado.empty:
                rc = df_filtrado["Responsável"].value_counts().reset_index()
                rc.columns = ["Responsável","Projetos"]
                fig3 = px.bar(rc, x="Responsável", y="Projetos",
                              color_discrete_sequence=["#00d23c"])
                fig3.update_layout(**PLOTLY_LAYOUT,
                                   xaxis=dict(showgrid=False, tickfont=dict(color="#b8d4bf", size=10)),
                                   yaxis=dict(showgrid=False, tickfont=dict(color="#6b8f74", size=10)))
                st.plotly_chart(fig3, use_container_width=True)

        with col_d:
            st.markdown('<div class="evoy-section-label">Linha do Tempo (Prazos)</div>', unsafe_allow_html=True)
            if not df_filtrado.empty and "Prazo" in df_filtrado.columns:
                df_g = df_filtrado.dropna(subset=["Início","Prazo"]).copy()
                if not df_g.empty:
                    fig4 = px.timeline(df_g, x_start="Início", x_end="Prazo",
                                       y="Projeto", color="Status",
                                       color_discrete_map=CORES_STATUS)
                    fig4.update_yaxes(autorange="reversed",
                                      tickfont=dict(color="#b8d4bf", size=10), showgrid=False)
                    fig4.update_xaxes(showgrid=False, tickfont=dict(color="#6b8f74", size=10))
                    fig4.update_layout(**PLOTLY_LAYOUT, showlegend=False)
                    st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — PROJETOS
# ══════════════════════════════════════════════════════════════════════════════
with tab_projetos:
    st.markdown('<div class="evoy-page-title">Todos os <span class="accent">Projetos</span></div>', unsafe_allow_html=True)

    if df_filtrado.empty:
        st.info("Nenhum projeto encontrado com os filtros aplicados.")
    else:
        PRIO_TAG = {
            "Alta":  '<span class="evoy-tag evoy-tag-alta">Alta</span>',
            "Média": '<span class="evoy-tag evoy-tag-media">Média</span>',
            "Baixa": '<span class="evoy-tag evoy-tag-baixa">Baixa</span>',
        }
        df_filtrado_reset = df_filtrado.reset_index(drop=True)
        for idx, row in df_filtrado_reset.iterrows():
            prio  = str(row.get("Prioridade","Média"))
            prog  = int(row.get("Progresso (%)",0))
            cor   = CORES_STATUS.get(str(row["Status"]), "#3d6647")
            label = f"{row['Projeto']}  ·  {row['Responsável']}  ·  {row['Status']}  ·  {prog}%"
            with st.expander(label, expanded=False):
                col_info, col_checks = st.columns([2,3])
                with col_info:
                    st.markdown(PRIO_TAG.get(prio, ""), unsafe_allow_html=True)
                    st.markdown(f"**Status:** {row['Status']}")
                    prazo_str  = pd.to_datetime(row['Prazo']).strftime('%d/%m/%Y')  if pd.notna(row.get('Prazo'))  else "—"
                    inicio_str = pd.to_datetime(row['Início']).strftime('%d/%m/%Y') if pd.notna(row.get('Início')) else "—"
                    st.markdown(f"**Início:** {inicio_str}")
                    st.markdown(f"**Prazo:** {prazo_str}")
                    st.markdown(f"**Horas:** {int(row.get('Horas Gastas',0))}h")
                    if row.get("Descrição") and str(row.get("Descrição")) != "nan":
                        st.markdown(f"**Desc.:** {row['Descrição']}")
                    st.progress(prog/100)
                    st.caption(f"{prog}% concluído")
                with col_checks:
                    st.markdown('<div class="evoy-section-label">Etapas do Projeto</div>', unsafe_allow_html=True)
                    etapas_atuais = get_etapas(row)
                    novas_etapas  = []
                    for i, etapa in enumerate(ETAPAS_PROJETO):
                        checked = st.checkbox(etapa, value=etapas_atuais[i], key=f"etapa_{idx}_{i}")
                        novas_etapas.append(checked)
                    if novas_etapas != etapas_atuais:
                        atualizar_etapas(idx, novas_etapas)
                        novo_prog = round((sum(novas_etapas)/len(ETAPAS_PROJETO))*100)
                        st.success(f"✅ Progresso atualizado: {novo_prog}%")
                        st.rerun()

        st.divider()
        df_exp = df_filtrado.copy()
        for c in ["Início","Prazo"]:
            if c in df_exp.columns:
                df_exp[c] = df_exp[c].dt.strftime("%d/%m/%Y")
        csv = df_exp.drop(columns=["Etapas"], errors="ignore").to_csv(index=False).encode("utf-8")
        st.download_button("↓  Exportar CSV", data=csv, file_name="projetos_ti.csv", mime="text/csv")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — NOVO PROJETO
# ══════════════════════════════════════════════════════════════════════════════
with tab_novo:
    st.markdown('<div class="evoy-page-title">Cadastrar <span class="accent">Novo Projeto</span></div>', unsafe_allow_html=True)
    with st.form("form_novo_projeto", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome        = st.text_input("Nome do Projeto *", placeholder="Ex: Portal do Cliente")
            responsavel = st.text_input("Responsável *", placeholder="Ex: Ana Silva")
            prioridade  = st.selectbox("Prioridade *", ["Alta","Média","Baixa"])
            status      = st.selectbox("Status *", ["Em andamento","Pausado","Concluído","Atrasado"])
        with col2:
            inicio    = st.date_input("Data de Início *", value=date.today())
            prazo     = st.date_input("Prazo *", value=date.today())
            horas     = st.number_input("Horas Gastas", min_value=0, value=0, step=1)
            descricao = st.text_area("Descrição", placeholder="Breve descrição do projeto...")

        st.markdown('<div class="evoy-section-label" style="margin-top:1rem">Etapas iniciais concluídas</div>', unsafe_allow_html=True)
        cols_etapas = st.columns(2)
        etapas_ini = []
        for i, etapa in enumerate(ETAPAS_PROJETO):
            etapas_ini.append(cols_etapas[i%2].checkbox(etapa, value=False, key=f"novo_etapa_{i}"))
        prog_ini = round((sum(etapas_ini)/len(ETAPAS_PROJETO))*100)
        st.info(f"Progresso calculado automaticamente: **{prog_ini}%**")

        enviado = st.form_submit_button("✅  Cadastrar Projeto", use_container_width=True, type="primary")
        if enviado:
            if not nome or not responsavel:
                st.error("Preencha pelo menos Nome e Responsável.")
            elif prazo < inicio:
                st.error("O Prazo não pode ser anterior ao Início.")
            else:
                salvar_projeto({
                    "Projeto": nome, "Responsável": responsavel, "Prioridade": prioridade,
                    "Status": status, "Progresso (%)": prog_ini,
                    "Etapas": ",".join(["1" if e else "0" for e in etapas_ini]),
                    "Início": pd.Timestamp(inicio), "Prazo": pd.Timestamp(prazo),
                    "Horas Gastas": horas, "Descrição": descricao,
                })
                st.success(f"✅ Projeto **{nome}** cadastrado! Progresso: {prog_ini}%")
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — CALENDÁRIO
# ══════════════════════════════════════════════════════════════════════════════
with tab_cal:
    import json as _json
    import streamlit.components.v1 as _cv1
    hoje_cal = date.today()
    reunioes = carregar_reunioes()

    sub_cal, sub_gerenciar = st.tabs(["📅  Calendário", "🗂️  Gerenciar Reuniões"])

    with sub_cal:
        with st.form("form_reuniao", clear_on_submit=True):
            st.markdown('<div class="evoy-section-label">Agendar Reunião</div>', unsafe_allow_html=True)
            c1,c2,c3,c4 = st.columns(4)
            titulo_r      = c1.text_input("Título *",        placeholder="Alinhamento X")
            responsavel_r = c2.text_input("Responsável *",   placeholder="Matheus")
            participantes = c3.text_input("Participantes *", placeholder="Rose, João")
            empresa       = c4.text_input("Empresa *",       placeholder="Acme Corp")
            c5,c6,c7,c8,c9 = st.columns([1,1,1,2,1])
            data_r  = c5.date_input("Data *", value=hoje_cal)
            hora_h  = c6.selectbox("Hora *",   list(range(0,24)), index=9,  format_func=lambda x:f"{x:02d}")
            hora_m  = c7.selectbox("Minuto *", [0,15,30,45],               format_func=lambda x:f"{x:02d}")
            local   = c8.text_input("Local / Link", placeholder="Sala 3 ou Meet")
            obs_r   = c9.text_input("Obs.", placeholder="Pauta...")
            if st.form_submit_button("📅  Salvar Reunião", use_container_width=True, type="primary"):
                if not titulo_r or not responsavel_r or not participantes or not empresa:
                    st.error("Preencha os campos obrigatórios *.")
                else:
                    salvar_reuniao({
                        "Título": titulo_r, "Responsável": responsavel_r,
                        "Participantes": participantes, "Empresa": empresa,
                        "Data": pd.Timestamp(data_r),
                        "Horário": f"{hora_h:02d}:{hora_m:02d}",
                        "Local": local, "Observações": obs_r,
                    })
                    st.rerun()

        df_cal = carregar_dados()
        CORES_CAL = ["#00d23c","#beff00","#00c8d2","#ff6400","#ff1432","#f59e0b","#78ff96","#ffd700"]
        eventos = []

        if not reunioes.empty:
            for pos, (_, r) in enumerate(reunioes.iterrows()):
                try:
                    data_str = pd.to_datetime(r["Data"]).strftime("%Y-%m-%d")
                    hora = str(r["Horário"]).strip()
                    try:
                        h,m = hora.split(":")
                        st_ = f"{data_str}T{int(h):02d}:{int(m):02d}:00"
                        en_ = f"{data_str}T{min(int(h)+1,23):02d}:{int(m):02d}:00"
                    except Exception:
                        st_ = data_str; en_ = data_str
                    cor = CORES_CAL[pos % len(CORES_CAL)]
                    eventos.append({
                        "id": f"r_{pos}", "title": f"🤝 {hora} · {r['Título']}",
                        "start": st_, "end": en_,
                        "backgroundColor": cor, "borderColor": cor,
                        "extendedProps": {"tipo":"reuniao","idx":pos,
                            "responsavel":str(r.get("Responsável","")),
                            "participantes":str(r.get("Participantes","")),
                            "empresa":str(r.get("Empresa","")),
                            "local":str(r.get("Local","")),
                            "obs":str(r.get("Observações","")),}
                    })
                except Exception:
                    pass

        if not df_cal.empty:
            for idx,row in df_cal.iterrows():
                if pd.notna(row.get("Prazo")):
                    prazo_str = pd.to_datetime(row["Prazo"]).date().strftime("%Y-%m-%d")
                    status_p  = str(row.get("Status",""))
                    cor_p     = CORES_STATUS.get(status_p,"#3d6647")
                    prog_p    = int(row.get("Progresso (%)", 0))
                    eventos.append({
                        "id": f"p_{idx}", "title": f"🏁 {row['Projeto']} · {prog_p}%",
                        "start": prazo_str, "allDay": True,
                        "backgroundColor": cor_p, "borderColor": cor_p,
                        "extendedProps": {"tipo":"prazo",
                            "projeto":str(row.get("Projeto","")),
                            "responsavel":str(row.get("Responsável","")),
                            "status":status_p,
                            "progresso":int(row.get("Progresso (%)",0)),}
                    })

        ev_json = _json.dumps(eventos, ensure_ascii=False)
        _cv1.html("""
<html><head><meta charset='utf-8'>
<link rel='preconnect' href='https://fonts.googleapis.com'>
<link href='https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap' rel='stylesheet'>
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:'Roboto',sans-serif;background:#051a0e;color:#e8f5ec;padding:10px;}
.nav{display:flex;align-items:center;gap:6px;margin-bottom:12px;}
.nav-btn{
  background:#071f10;color:#6b8f74;
  border:1px solid rgba(0,210,60,0.2);
  padding:5px 16px;cursor:pointer;font-size:11px;font-weight:700;
  letter-spacing:0.06em;text-transform:uppercase;transition:all 0.2s;
  clip-path:polygon(0 0,calc(100% - 8px) 0,100% 100%,8px 100%);
}
.nav-btn:hover{background:#00d23c;color:#051a0e;border-color:#00d23c;}
.nav-title{flex:1;text-align:center;font-size:13px;font-weight:700;color:#e8f5ec;letter-spacing:0.08em;text-transform:uppercase;}
.grid{display:grid;grid-template-columns:repeat(7,1fr);gap:3px;}
.hdr{
  background:#020f07;text-align:center;font-size:9px;font-weight:700;
  color:rgba(0,210,60,0.5);padding:7px 2px;letter-spacing:0.12em;text-transform:uppercase;
}
.cell{
  background:#071f10;min-height:88px;padding:5px;
  border:1px solid rgba(0,210,60,0.07);transition:border-color 0.2s;
  position:relative;
}
.cell:hover{border-color:rgba(0,210,60,0.25);}
.cell:hover::after{
  content:'';position:absolute;bottom:0;right:0;
  width:8px;height:8px;
  border-right:1px solid rgba(0,210,60,0.4);
  border-bottom:1px solid rgba(0,210,60,0.4);
}
.cell.other-month{opacity:.2;}
.cell.today{background:#0a2214;border-color:rgba(0,210,60,0.5)!important;}
.day-num{font-size:10px;color:#3d6647;margin-bottom:3px;font-weight:500;}
.cell.today .day-num{
  color:#051a0e;font-weight:800;background:#00d23c;
  width:18px;height:18px;display:flex;align-items:center;justify-content:center;
  clip-path:polygon(50% 0%,100% 50%,50% 100%,0% 50%);
}
.ev{
  padding:1px 5px;font-size:9px;margin-bottom:2px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
  color:#051a0e;font-weight:600;
  clip-path:polygon(0 0,calc(100% - 5px) 0,100% 100%,5px 100%);
}
.more{font-size:9px;color:#3d6647;margin-top:2px;}
</style></head><body>
<div class='nav'>
  <button class='nav-btn' onclick='prev()'>&#8249; Ant</button>
  <button class='nav-btn' onclick='goToday()'>Hoje</button>
  <span class='nav-title' id='title'></span>
  <button class='nav-btn' onclick='next()'>Próx &#8250;</button>
</div>
<div class='grid' id='grid'></div>
<script>
var EVENTS=EVENTOS_JSON;
var MESES=['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'];
var DIAS=['Dom','Seg','Ter','Qua','Qui','Sex','Sáb'];
var cur=new Date();cur.setDate(1);
var today=new Date();today.setHours(0,0,0,0);
function evDay(y,m,d){return EVENTS.filter(function(e){var raw=e.start.length===10?e.start+'T12:00:00':e.start;var s=new Date(raw);return s.getFullYear()===y&&s.getMonth()===m&&s.getDate()===d;});}
function render(){
  var y=cur.getFullYear(),m=cur.getMonth();
  document.getElementById('title').textContent=MESES[m]+' / '+y;
  var g=document.getElementById('grid');g.innerHTML='';
  DIAS.forEach(function(d){var h=document.createElement('div');h.className='hdr';h.textContent=d;g.appendChild(h);});
  var fd=new Date(y,m,1).getDay(),td=new Date(y,m+1,0).getDate(),pd=new Date(y,m,0).getDate();
  for(var i=0;i<fd;i++){var c=mk();c.classList.add('other-month');c.appendChild(mkd('day-num',pd-fd+1+i));g.appendChild(c);}
  for(var d=1;d<=td;d++){
    var dt=new Date(y,m,d);dt.setHours(0,0,0,0);
    var c=mk();if(dt.getTime()===today.getTime())c.classList.add('today');
    c.appendChild(mkd('day-num',d));
    var evs=evDay(y,m,d);
    evs.slice(0,3).forEach(function(e){
      var el=mkd('ev',e.title);
      el.style.background=e.backgroundColor||'#00d23c';
      c.appendChild(el);
    });
    if(evs.length>3)c.appendChild(mkd('more','+'+(evs.length-3)+' mais'));
    g.appendChild(c);
  }
  var rem=(fd+td)%7;if(rem>0)for(var i=0;i<7-rem;i++){var c=mk();c.classList.add('other-month');g.appendChild(c);}
}
function mk(){var c=document.createElement('div');c.className='cell';return c;}
function mkd(cls,txt){var c=document.createElement('div');c.className=cls;if(txt!=null)c.textContent=txt;return c;}
function prev(){cur.setMonth(cur.getMonth()-1);render();}
function next(){cur.setMonth(cur.getMonth()+1);render();}
function goToday(){cur=new Date();cur.setDate(1);render();}
render();
</script></body></html>""".replace("EVENTOS_JSON", ev_json), height=620, scrolling=False)

    with sub_gerenciar:
        col_reunioes, col_projetos = st.columns([3, 2])

        with col_reunioes:
            st.markdown('<div class="evoy-section-label">Reuniões Agendadas</div>', unsafe_allow_html=True)
            if reunioes.empty:
                st.info("Nenhuma reunião agendada ainda.")
            else:
                for pos, (_, row) in enumerate(reunioes.iterrows()):
                    data_fmt = pd.to_datetime(row["Data"]).strftime("%d/%m/%Y") if pd.notna(row["Data"]) else "—"
                    dia_num  = pd.to_datetime(row["Data"]).strftime("%d") if pd.notna(row["Data"]) else "—"
                    mes_abr  = pd.to_datetime(row["Data"]).strftime("%b").upper() if pd.notna(row["Data"]) else ""
                    loc = str(row.get("Local",""))
                    obs = str(row.get("Observações",""))
                    extra = []
                    if loc and loc not in ("nan",""): extra.append(f"📍 {loc}")
                    if obs and obs not in ("nan",""): extra.append(f"📝 {obs}")

                    with st.container():
                        col_d, col_info, col_btn = st.columns([1, 6, 1])
                        with col_d:
                            st.markdown(f"""
                            <div class='evoy-reunion-date'>
                                {mes_abr}<strong>{dia_num}</strong>
                                <span style='font-size:9px;color:#3d6647'>{row.get('Horário','')}</span>
                            </div>""", unsafe_allow_html=True)
                        with col_info:
                            st.markdown(f"**{row['Título']}** &nbsp;·&nbsp; 👤 {row.get('Responsável','')} &nbsp;·&nbsp; 🏢 {row.get('Empresa','')}")
                            if extra:
                                st.caption(" · ".join(extra))
                        with col_btn:
                            if st.button("🗑", key=f"del_{pos}", help="Excluir"):
                                deletar_reuniao(pos)
                                st.toast("Reunião excluída!", icon="🗑️")
                                st.rerun()
                        st.divider()

        with col_projetos:
            st.markdown('<div class="evoy-section-label">Progresso dos Projetos</div>', unsafe_allow_html=True)
            df_prog = carregar_dados()
            if df_prog.empty:
                st.info("Nenhum projeto cadastrado.")
            else:
                df_prog = df_prog.sort_values("Progresso (%)", ascending=False)
                for _, proj in df_prog.iterrows():
                    prog     = int(proj.get("Progresso (%)", 0))
                    status_p = str(proj.get("Status",""))
                    cor      = CORES_STATUS.get(status_p, "#3d6647")
                    prazo_p  = pd.to_datetime(proj["Prazo"]).strftime("%d/%m") if pd.notna(proj.get("Prazo")) else "—"
                    st.markdown(f"""
                    <div class='evoy-proj-bar-wrap'>
                      <div class='evoy-proj-bar-header'>
                        <span class='proj-name'>{proj['Projeto']}</span>
                        <span class='proj-pct' style='color:{cor}'>{prog}%</span>
                      </div>
                      <div style='font-size:10px;color:#3d6647;margin-bottom:4px'>
                        👤 {proj.get('Responsável','')} · 📅 {prazo_p} · <span style='color:{cor}'>{status_p}</span>
                      </div>
                      <div class='evoy-prog-track'>
                        <div class='evoy-prog-fill' style='width:{prog}%;background:{cor}'></div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — SPRINT
# ══════════════════════════════════════════════════════════════════════════════
with tab_sprint:
    st.markdown('<div class="evoy-page-title">Sprint <span class="accent">Semanal</span></div>', unsafe_allow_html=True)

    sprints   = carregar_sprints()
    seg_atual = segunda_da_semana()

    col_form_sp, col_hist = st.columns([2, 3], gap="large")

    with col_form_sp:
        st.markdown(f'<div class="evoy-section-label">Registrar · Semana {seg_atual.strftime("%d/%m/%Y")}</div>', unsafe_allow_html=True)
        with st.form("form_sprint", clear_on_submit=True):
            bu = st.selectbox("BU / Área *", ["Estratégia & Projetos","Governança & Sustentação"])
            responsavel_sp = st.text_input("Responsável *", placeholder="Ex: Ana Silva")
            progressos = st.text_area("📈 Progressos da semana *",
                placeholder="- Concluímos o módulo X\n- Finalizamos a migração Y", height=110)
            desafios = st.text_area("⚠ Desafios",
                placeholder="- Atraso na entrega do fornecedor Z", height=90)
            proxima = st.text_area("🔜 Próxima Sprint",
                placeholder="- Iniciar módulo W\n- Reunião com cliente", height=90)
            meta     = st.text_input("🎯 Meta da semana", placeholder="Ex: Disp. Core 98,5%")
            realizado= st.text_input("✅ Realizado vs Meta", placeholder="Ex: 98,7% ✅")
            ok_sp = st.form_submit_button("💾  Salvar Sprint", use_container_width=True, type="primary")

            if ok_sp:
                if not bu or not responsavel_sp or not progressos:
                    st.error("Preencha BU, Responsável e Progressos.")
                else:
                    ja_existe = False
                    if not sprints.empty:
                        mask = (
                            (pd.to_datetime(sprints["Semana"]).dt.date == seg_atual) &
                            (sprints["BU"] == bu) &
                            (sprints["Responsável"].str.strip().str.lower() == responsavel_sp.strip().lower())
                        )
                        ja_existe = mask.any()
                    if ja_existe:
                        st.warning(f"Sprint de **{bu}** / **{responsavel_sp}** já registrada nesta semana.")
                    else:
                        salvar_sprint({
                            "Semana": pd.Timestamp(seg_atual), "BU": bu,
                            "Responsável": responsavel_sp, "Progressos": progressos,
                            "Desafios": desafios, "Próxima Sprint": proxima,
                            "Meta": meta, "Realizado": realizado,
                        })
                        st.success(f"✅ Sprint de **{responsavel_sp}** ({bu}) salva!")
                        st.rerun()

    with col_hist:
        st.markdown('<div class="evoy-section-label">Histórico de Sprints</div>', unsafe_allow_html=True)
        if sprints.empty:
            st.info("Nenhuma sprint registrada ainda.")
        else:
            sprints_ord = sprints.sort_values("Semana", ascending=False).copy()
            sprints_ord["Semana"] = pd.to_datetime(sprints_ord["Semana"])

            fc1, fc2 = st.columns(2)
            bus_disponiveis = ["Todas"] + sorted(sprints_ord["BU"].dropna().unique().tolist())
            filtro_bu  = fc1.selectbox("BU", bus_disponiveis, key="filtro_bu_sprint")
            semanas_disponiveis = sprints_ord["Semana"].dt.strftime("%d/%m/%Y").unique().tolist()
            filtro_sem = fc2.selectbox("Semana", ["Todas"] + semanas_disponiveis, key="filtro_sem_sprint")

            df_hist = sprints_ord.copy()
            if filtro_bu != "Todas":
                df_hist = df_hist[df_hist["BU"] == filtro_bu]
            if filtro_sem != "Todas":
                df_hist = df_hist[df_hist["Semana"].dt.strftime("%d/%m/%Y") == filtro_sem]

            if df_hist.empty:
                st.warning("Nenhuma sprint encontrada com esses filtros.")
            else:
                st.caption(f"{len(df_hist)} sprint(s) encontrada(s)")
                for _, sp in df_hist.iterrows():
                    semana_str = pd.to_datetime(sp["Semana"]).strftime("%d/%m/%Y")
                    is_atual   = pd.to_datetime(sp["Semana"]).date() == seg_atual
                    label_exp  = f"{'🟢 ' if is_atual else ''}Semana {semana_str} — {sp.get('BU','')} — {sp.get('Responsável','')}"
                    with st.expander(label_exp, expanded=is_atual):
                        col_s1, col_s2 = st.columns(2)
                        with col_s1:
                            st.markdown(f"**👤 Responsável:** {sp.get('Responsável','')}")
                            st.markdown(f"**🎯 Meta:** {sp.get('Meta','—')}")
                            st.markdown(f"**✅ Realizado:** {sp.get('Realizado','—')}")
                            st.divider()
                            st.markdown('<div class="evoy-section-label">Progressos</div>', unsafe_allow_html=True)
                            for linha in str(sp.get("Progressos","")).split("\n"):
                                if linha.strip():
                                    st.markdown(f"· {linha.strip().lstrip('-').strip()}")
                        with col_s2:
                            st.markdown('<div class="evoy-section-label">Desafios</div>', unsafe_allow_html=True)
                            for linha in str(sp.get("Desafios","")).split("\n"):
                                if linha.strip():
                                    st.markdown(f"· {linha.strip().lstrip('-').strip()}")
                            st.markdown('<div class="evoy-section-label" style="margin-top:0.6rem">Próxima Sprint</div>', unsafe_allow_html=True)
                            for linha in str(sp.get("Próxima Sprint","")).split("\n"):
                                if linha.strip():
                                    st.markdown(f"· {linha.strip().lstrip('-').strip()}")