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

# ── Página ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="Dashboard TI", page_icon="📊", layout="wide")

# ── Carregar CSS externo ───────────────────────────────────────────────
def carregar_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

carregar_css("style.css")

# ── Proteção por token na URL ──────────────────────────────────────────
_token_valido = st.secrets.get("TOKEN_ACESSO", "")
_token_url = st.query_params.get("token", "")

if _token_valido and _token_url != _token_valido:
    st.error("🔒 Acesso não autorizado. Verifique o link com sua equipe.")
    st.stop()

# ── Dados globais ──────────────────────────────────────────────────────
df = carregar_dados()

CORES_STATUS = {
    "Em andamento": "#3b82f6",
    "Concluído": "#22c55e",
    "Atrasado": "#ef4444",
    "Pausado": "#f59e0b",
}

PRIO_ORDEM = {"Alta": 0, "Média": 1, "Baixa": 2}

# ── Sidebar ────────────────────────────────────────────────────────────
with st.sidebar:

    st.title("📊 TI Dashboard")

    st.divider()

    st.header("🔍 Filtros")

    busca = st.text_input(
        "Pesquisar projeto...",
        placeholder="Ex: Sistema de RH"
    )

    responsaveis = st.multiselect(
        "Responsável",
        options=sorted(df["Responsável"].dropna().unique()) if not df.empty else [],
    )

    status_filtro = st.multiselect(
        "Status",
        options=["Em andamento", "Concluído", "Atrasado", "Pausado"],
    )

    prio_filtro = st.multiselect(
        "Prioridade",
        options=["Alta", "Média", "Baixa"],
    )

    progresso_range = st.slider(
        "Progresso (%)",
        0,
        100,
        (0, 100)
    )

    st.divider()

    st.button(
        "🔄 Atualizar dados",
        use_container_width=True
    )

# ── Aplicar filtros ────────────────────────────────────────────────────
df_filtrado = df.copy()

if busca:
    df_filtrado = df_filtrado[
        df_filtrado["Projeto"].str.contains(busca, case=False, na=False)
    ]

if responsaveis:
    df_filtrado = df_filtrado[
        df_filtrado["Responsável"].isin(responsaveis)
    ]

if status_filtro:
    df_filtrado = df_filtrado[
        df_filtrado["Status"].isin(status_filtro)
    ]

if prio_filtro:
    df_filtrado = df_filtrado[
        df_filtrado["Prioridade"].isin(prio_filtro)
    ]

if "Progresso (%)" in df_filtrado.columns:
    df_filtrado = df_filtrado[
        df_filtrado["Progresso (%)"].between(
            progresso_range[0],
            progresso_range[1]
        )
    ]

# ── Tabs ───────────────────────────────────────────────────────────────
tab_dash, tab_projetos, tab_novo, tab_cal, tab_sprint = st.tabs([
    "📈 Dashboard",
    "📋 Projetos",
    "➕ Novo Projeto",
    "📅 Calendário",
    "🏃 Sprint"
])

# ═══════════════════════════════════════════════════════════════════════
# TAB 1 — DASHBOARD
# ═══════════════════════════════════════════════════════════════════════
with tab_dash:

    st.subheader("Visão Geral")

    if df.empty:

        st.info("Nenhum projeto cadastrado ainda.")

    else:

        total = len(df_filtrado)

        em_andamento = len(
            df_filtrado[df_filtrado["Status"] == "Em andamento"]
        )

        concluidos = len(
            df_filtrado[df_filtrado["Status"] == "Concluído"]
        )

        atrasados_n = len(
            projetos_atrasados(df_filtrado)
        ) if not df_filtrado.empty else 0

        media_prog = df_filtrado["Progresso (%)"].mean()

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric("📁 Total", total)
        c2.metric("🔄 Em Andamento", em_andamento)
        c3.metric("✅ Concluídos", concluidos)
        c4.metric("⚠️ Atrasados", atrasados_n)
        c5.metric("📊 Progresso Médio", f"{media_prog:.0f}%")

        st.divider()

        col_a, col_b = st.columns(2)

        with col_a:

            st.markdown("#### Status dos Projetos")

            cnt = df_filtrado["Status"].value_counts().reset_index()
            cnt.columns = ["Status", "Qtd"]

            fig = px.pie(
                cnt,
                names="Status",
                values="Qtd",
                color="Status",
                color_discrete_map=CORES_STATUS,
                hole=0.45
            )

            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )

            st.plotly_chart(fig, use_container_width=True)

        with col_b:

            st.markdown("#### Progresso (%) por Projeto")

            df_p = df_filtrado[
                ["Projeto", "Progresso (%)", "Status"]
            ].sort_values("Progresso (%)")

            fig2 = go.Figure(go.Bar(
                x=df_p["Progresso (%)"],
                y=df_p["Projeto"],
                orientation="h",
                marker_color=df_p["Status"].map(CORES_STATUS),
                text=df_p["Progresso (%)"].astype(str) + "%"
            ))

            st.plotly_chart(fig2, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════
# TAB 2 — PROJETOS
# ═══════════════════════════════════════════════════════════════════════
with tab_projetos:

    st.subheader("📋 Projetos")

    if df_filtrado.empty:

        st.info("Nenhum projeto encontrado.")

    else:

        PRIO_ICON = {
            "Alta": "🔴",
            "Média": "🟡",
            "Baixa": "🟢"
        }

        df_filtrado_reset = df_filtrado.reset_index(drop=True)

        for idx, row in df_filtrado_reset.iterrows():

            prio_icon = PRIO_ICON.get(
                str(row.get("Prioridade", "Média")),
                "🟡"
            )

            prog = int(row.get("Progresso (%)", 0))

            with st.expander(
                f"{prio_icon} **{row['Projeto']}** — "
                f"{row['Responsável']} | "
                f"{row['Status']} | {prog}%"
            ):

                col_info, col_checks = st.columns([2, 3])

                with col_info:

                    st.markdown(
                        f"**Prioridade:** {row.get('Prioridade','Média')}"
                    )

                    st.markdown(
                        f"**Status:** {row['Status']}"
                    )

                    st.progress(prog / 100)

                with col_checks:

                    st.markdown("**✅ Etapas do Projeto**")

                    etapas_atuais = get_etapas(row)

                    novas_etapas = []

                    for i, etapa in enumerate(ETAPAS_PROJETO):

                        checked = st.checkbox(
                            etapa,
                            value=etapas_atuais[i],
                            key=f"etapa_{idx}_{i}"
                        )

                        novas_etapas.append(checked)

                    if novas_etapas != etapas_atuais:

                        atualizar_etapas(idx, novas_etapas)

                        st.rerun()

# ═══════════════════════════════════════════════════════════════════════
# TAB 3 — NOVO PROJETO
# ═══════════════════════════════════════════════════════════════════════
with tab_novo:

    st.subheader("➕ Cadastrar Novo Projeto")

    with st.form("form_novo_projeto"):

        nome = st.text_input("Nome do Projeto")

        responsavel = st.text_input("Responsável")

        prioridade = st.selectbox(
            "Prioridade",
            ["Alta", "Média", "Baixa"]
        )

        enviado = st.form_submit_button("Cadastrar")

        if enviado:

            salvar_projeto({
                "Projeto": nome,
                "Responsável": responsavel,
                "Prioridade": prioridade
            })

            st.success("Projeto cadastrado!")

# ═══════════════════════════════════════════════════════════════════════
# TAB 4 — CALENDÁRIO
# ═══════════════════════════════════════════════════════════════════════
with tab_cal:

    st.subheader("📅 Calendário")

    reunioes = carregar_reunioes()

    if reunioes.empty:

        st.info("Nenhuma reunião cadastrada.")

    else:

        st.dataframe(reunioes)

# ═══════════════════════════════════════════════════════════════════════
# TAB 5 — SPRINT
# ═══════════════════════════════════════════════════════════════════════
with tab_sprint:

    st.subheader("🏃 Sprint Semanal")

    sprints = carregar_sprints()

    if sprints.empty:

        st.info("Nenhuma sprint registrada.")

    else:

        st.dataframe(sprints)