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
    atualizar_projeto, deletar_projeto, atualizar_sprint,
    carregar_chamados, salvar_chamado, atualizar_chamado, deletar_chamado,
    SITUACOES_CHAMADO,
)

# ── Página ────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Dashboard TI", page_icon="", layout="wide")

# ── Proteção por token na URL ─────────────────────────────────────────────────
_token_valido = git rm --cached .streamlit/secrets.tomlst.secrets.get("TOKEN_ACESSO", "")
_token_url    = st.query_params.get("token", "")
if _token_valido and _token_url != _token_valido:
    st.error("🔒 Acesso não autorizado. Verifique o link com sua equipe.")
    st.stop()

st.markdown("""
<style>
    .block-container { padding-top: 3.5rem !important; padding-bottom: 2rem; }
    header[data-testid="stHeader"] { background: rgba(15,23,42,0.95); backdrop-filter: blur(8px); }
    .stMetric label { font-size: 0.85rem; color: #94a3b8; }
    div[data-testid="stSidebar"] { background-color: #0f172a; }
    .sprint-card {
        background: #1e293b; border-radius: 10px; padding: 1rem 1.2rem;
        margin-bottom: 0.8rem; border-left: 4px solid #3b82f6;
    }
    .sprint-card h4 { margin: 0 0 0.4rem 0; color: #e2e8f0; font-size: 0.95rem; }
    .sprint-card p  { margin: 0.15rem 0; color: #94a3b8; font-size: 0.82rem; }
    .prio-alta   { color: #00d339; font-weight: 700; }
    .prio-media  { color: #f59e0b; font-weight: 700; }
    .prio-baixa  { color: #22c55e; font-weight: 700; }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #00d339 !important;
    }
    [data-baseweb="tab-highlight"] {
        background-color: #00d339 !important;
    }
    [data-testid="stTabs"] button[aria-selected="true"] {
        color: #00d339 !important;
        border-bottom-color: #00d339 !important;
    }
    button[data-baseweb="tab"]:hover { color: #00d339 !important; }
    [data-testid="stTabs"] button:hover {
        color: #00d339 !important;
        border-bottom-color: #00d339 !important;
    }

    button[data-testid="baseButton-primary"],
    button[kind="primary"],
    .stButton > button[kind="primary"],
    [data-testid="stBaseButton-primaryFormSubmit"],
    [data-testid="stBaseButton-primary"] {
        background-color: #00d339 !important;
        border-color: #00d339 !important;
        color: #060e08 !important;
    }
    button[data-testid="baseButton-primary"]:hover,
    .stButton > button[kind="primary"]:hover,
    [data-testid="stBaseButton-primaryFormSubmit"]:hover,
    [data-testid="stBaseButton-primary"]:hover {
        background-color: #00b82f !important;
        border-color: #00b82f !important;
        color: #060e08 !important;
    }

    [data-testid="stSlider"] [role="slider"] { background-color: #00d339 !important; }
    [data-testid="stSlider"] > div > div > div > div { background-color: #00d339 !important; }
    [data-testid="stSlider"] .st-emotion-cache-1j0e0b7 { color: #00d339 !important; }

    input[type="checkbox"]:checked + div,
    [data-testid="stCheckbox"] svg { color: #00d339 !important; fill: #00d339 !important; }
    [data-baseweb="checkbox"] [data-checked="true"] { background-color: #00d339 !important; border-color: #00d339 !important; }

    .ia-chat-user {
        background: #1e293b; border-radius: 10px; padding: 0.7rem 1rem;
        margin-bottom: 0.5rem; border-left: 3px solid #3b82f6;
    }
    .ia-chat-bot {
        background: #0d2212; border-radius: 10px; padding: 0.7rem 1rem;
        margin-bottom: 0.5rem; border-left: 3px solid #00d339;
    }
    .ia-chat-label { font-size: 0.8rem; color: #94a3b8; margin-bottom: 3px; }
    .ia-chat-label-bot { font-size: 0.8rem; color: #5a7d60; margin-bottom: 3px; }

    /* Chamados badge */
    .badge-atendido  { background:#166534; color:#bbf7d0; padding:2px 10px; border-radius:99px; font-size:11px; font-weight:700; }
    .badge-aberto    { background:#1e3a5f; color:#93c5fd; padding:2px 10px; border-radius:99px; font-size:11px; font-weight:700; }
    .badge-andamento { background:#713f12; color:#fde68a; padding:2px 10px; border-radius:99px; font-size:11px; font-weight:700; }
    .badge-cancelado { background:#3f1515; color:#fca5a5; padding:2px 10px; border-radius:99px; font-size:11px; font-weight:700; }
    .badge-aguardando{ background:#312e81; color:#c7d2fe; padding:2px 10px; border-radius:99px; font-size:11px; font-weight:700; }
</style>
""", unsafe_allow_html=True)

# ── Dados globais ─────────────────────────────────────────────────────────────
df = carregar_dados()

CORES_STATUS = {
    "Em andamento": "#7fa17b",
    "Concluído":    "#22c55e",
    "Atrasado":     "#00d339",
    "Pausado":      "#f59e0b",
}
PRIO_ORDEM = {"Alta": 0, "Média": 1, "Baixa": 2}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("evoy.png", width=180)
    st.image("dashti.png", width=80)
    st.divider()
    st.header("Filtros")
    busca = st.text_input("Pesquisar projeto...", placeholder="Ex: Sistema de RH")
    responsaveis = st.multiselect(
        "Responsável",
        options=sorted(df["Responsável"].dropna().unique()) if not df.empty else [],
    )
    status_filtro = st.multiselect(
        "Status", options=["Em andamento", "Concluído", "Atrasado", "Pausado"],
    )
    prio_filtro = st.multiselect(
        "Prioridade", options=["Alta", "Média", "Baixa"],
    )
    progresso_range = st.slider("Progresso (%)", 0, 100, (0, 100))
    st.divider()
    st.button("Atualizar dados", use_container_width=True)

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
tab_dash, tab_projetos, tab_novo, tab_cal, tab_sprint, tab_chamados, tab_ia = st.tabs([
    "Dashboard", "Projetos", "Novo Projeto", "Calendário", "Sprint", "Chamados", "IA do TI"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
with tab_dash:
    st.subheader("Visão Geral")
    if df.empty:
        st.info("Nenhum projeto cadastrado ainda.")
    else:
        total        = len(df_filtrado)
        em_andamento = len(df_filtrado[df_filtrado["Status"] == "Em andamento"])
        concluidos   = len(df_filtrado[df_filtrado["Status"] == "Concluído"])
        atrasados_n  = len(projetos_atrasados(df_filtrado)) if not df_filtrado.empty else 0
        media_prog   = df_filtrado["Progresso (%)"].mean() if not df_filtrado.empty else 0
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("Total", total)
        c2.metric("Em Andamento", em_andamento)
        c3.metric("Concluídos", concluidos)
        c4.metric("Atrasados", atrasados_n,
                  delta=f"-{atrasados_n}" if atrasados_n > 0 else None, delta_color="inverse")
        c5.metric("Progresso Médio", f"{media_prog:.0f}%")
        st.divider()
        col_a,col_b = st.columns(2)
        with col_a:
            st.markdown("#### Status dos Projetos")
            cnt = df_filtrado["Status"].value_counts().reset_index()
            cnt.columns = ["Status","Qtd"]
            fig = px.pie(cnt, names="Status", values="Qtd",
                         color="Status", color_discrete_map=CORES_STATUS, hole=0.45)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              legend=dict(orientation="h",yanchor="bottom",y=-0.2),
                              margin=dict(t=10,b=10))
            st.plotly_chart(fig, use_container_width=True)
        with col_b:
            st.markdown("#### Progresso (%) por Projeto")
            if not df_filtrado.empty:
                df_p = df_filtrado[["Projeto","Progresso (%)","Status"]].sort_values("Progresso (%)")
                fig2 = go.Figure(go.Bar(
                    x=df_p["Progresso (%)"], y=df_p["Projeto"], orientation="h",
                    marker_color=df_p["Status"].map(CORES_STATUS).fillna("#64748b").tolist(),
                    text=df_p["Progresso (%)"].astype(int).astype(str)+"%", textposition="outside"))
                fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                                   xaxis=dict(range=[0,115],showgrid=False),
                                   margin=dict(t=10,b=10,r=40),showlegend=False)
                st.plotly_chart(fig2, use_container_width=True)
        col_c,col_d = st.columns(2)
        with col_c:
            st.markdown("#### Projetos por Responsável")
            if not df_filtrado.empty:
                rc = df_filtrado["Responsável"].value_counts().reset_index()
                rc.columns = ["Responsável","Projetos"]
                # Escala de verde em vez de azul
                fig3 = px.bar(rc, x="Responsável", y="Projetos", color="Projetos",
                              color_continuous_scale=[[0,"#064e1a"],[0.5,"#00d339"],[1,"#bbf7d0"]])
                fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                                   coloraxis_showscale=False,margin=dict(t=10,b=10))
                st.plotly_chart(fig3, use_container_width=True)
        with col_d:
            st.markdown("#### Linha do Tempo (Prazos)")
            if not df_filtrado.empty and "Prazo" in df_filtrado.columns:
                df_g = df_filtrado.dropna(subset=["Início","Prazo"]).copy()
                if not df_g.empty:
                    fig4 = px.timeline(df_g,x_start="Início",x_end="Prazo",
                                       y="Projeto",color="Status",color_discrete_map=CORES_STATUS)
                    fig4.update_yaxes(autorange="reversed")
                    fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                                       showlegend=False,margin=dict(t=10,b=10))
                    st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — PROJETOS
# ══════════════════════════════════════════════════════════════════════════════
with tab_projetos:
    st.subheader("Projetos")

    # Session state para controle de edição/exclusão
    if "proj_edit_idx" not in st.session_state:
        st.session_state["proj_edit_idx"] = None
    if "proj_del_idx" not in st.session_state:
        st.session_state["proj_del_idx"] = None

    if df_filtrado.empty:
        st.info("Nenhum projeto encontrado.")
    else:
        PRIO_ICON = {"Alta":"🔴","Média":"🟡","Baixa":"🟢"}
        df_filtrado_reset = df_filtrado.reset_index(drop=True)

        for idx, row in df_filtrado_reset.iterrows():
            prio_icon = PRIO_ICON.get(str(row.get("Prioridade","Média")),"🟡")
            prog = int(row.get("Progresso (%)",0))

            with st.expander(f"{prio_icon} **{row['Projeto']}** — {row['Responsável']} | {row['Status']} | {prog}%", expanded=False):

                # ── Modal de confirmação de exclusão ──────────────────────
                if st.session_state["proj_del_idx"] == idx:
                    st.warning(f"⚠️ Tem certeza que deseja excluir o projeto **{row['Projeto']}**? Esta ação não pode ser desfeita.")
                    ca, cb, cc = st.columns([2,1,1])
                    if cb.button("✅ Confirmar exclusão", key=f"conf_del_{idx}", type="primary"):
                        deletar_projeto(idx)
                        st.session_state["proj_del_idx"] = None
                        st.toast("Projeto excluído!", icon="🗑️")
                        st.rerun()
                    if cc.button("❌ Cancelar", key=f"canc_del_{idx}"):
                        st.session_state["proj_del_idx"] = None
                        st.rerun()

                # ── Modal de edição ───────────────────────────────────────
                elif st.session_state["proj_edit_idx"] == idx:
                    st.markdown("#### ✏️ Editando projeto")
                    with st.form(f"form_edit_proj_{idx}"):
                        ec1, ec2 = st.columns(2)
                        nome_e      = ec1.text_input("Nome do Projeto *", value=str(row.get("Projeto","")))
                        resp_e      = ec1.text_input("Responsável *",     value=str(row.get("Responsável","")))
                        prio_e      = ec1.selectbox("Prioridade", ["Alta","Média","Baixa"],
                                        index=["Alta","Média","Baixa"].index(str(row.get("Prioridade","Média"))) if str(row.get("Prioridade","Média")) in ["Alta","Média","Baixa"] else 1)
                        status_e    = ec2.selectbox("Status", ["Em andamento","Pausado","Concluído","Atrasado"],
                                        index=["Em andamento","Pausado","Concluído","Atrasado"].index(str(row.get("Status","Em andamento"))) if str(row.get("Status","")) in ["Em andamento","Pausado","Concluído","Atrasado"] else 0)
                        inicio_e    = ec2.date_input("Início", value=pd.to_datetime(row.get("Início")).date() if pd.notna(row.get("Início")) else date.today())
                        prazo_e     = ec2.date_input("Prazo",  value=pd.to_datetime(row.get("Prazo")).date()  if pd.notna(row.get("Prazo"))  else date.today())
                        horas_e     = ec2.number_input("Horas Gastas", min_value=0, value=int(row.get("Horas Gastas",0)), step=1)
                        desc_e      = st.text_area("Descrição", value=str(row.get("Descrição","")) if str(row.get("Descrição","")) != "nan" else "")
                        col_sv, col_cc = st.columns(2)
                        salvar_e    = col_sv.form_submit_button("💾 Salvar alterações", type="primary", use_container_width=True)
                        cancelar_e  = col_cc.form_submit_button("❌ Cancelar", use_container_width=True)

                        if salvar_e:
                            atualizar_projeto(idx, {
                                "Projeto": nome_e, "Responsável": resp_e,
                                "Prioridade": prio_e, "Status": status_e,
                                "Início": pd.Timestamp(inicio_e).strftime("%Y-%m-%d"),
                                "Prazo":  pd.Timestamp(prazo_e).strftime("%Y-%m-%d"),
                                "Horas Gastas": horas_e, "Descrição": desc_e,
                            })
                            st.session_state["proj_edit_idx"] = None
                            st.toast("Projeto atualizado!", icon="✅")
                            st.rerun()
                        if cancelar_e:
                            st.session_state["proj_edit_idx"] = None
                            st.rerun()

                # ── Visualização normal ───────────────────────────────────
                else:
                    col_info, col_checks = st.columns([2,3])
                    with col_info:
                        st.markdown(f"**Prioridade:** {row.get('Prioridade','Média')}")
                        st.markdown(f"**Status:** {row['Status']}")
                        prazo_str  = pd.to_datetime(row['Prazo']).strftime('%d/%m/%Y')  if pd.notna(row.get('Prazo'))  else "—"
                        inicio_str = pd.to_datetime(row['Início']).strftime('%d/%m/%Y') if pd.notna(row.get('Início')) else "—"
                        st.markdown(f"**Início:** {inicio_str}")
                        st.markdown(f"**Prazo:** {prazo_str}")
                        st.markdown(f"**Horas:** {int(row.get('Horas Gastas',0))}h")
                        if row.get("Descrição") and str(row.get("Descrição")) != "nan":
                            st.markdown(f"**Descrição:** {row['Descrição']}")
                        st.progress(prog/100)
                        st.caption(f"Progresso: {prog}%")

                        # Botões editar / excluir
                        btn_col1, btn_col2 = st.columns(2)
                        if btn_col1.button("✏️ Editar", key=f"edit_proj_{idx}", use_container_width=True):
                            st.session_state["proj_edit_idx"] = idx
                            st.session_state["proj_del_idx"]  = None
                            st.rerun()
                        if btn_col2.button("🗑️ Excluir", key=f"del_proj_{idx}", use_container_width=True):
                            st.session_state["proj_del_idx"]  = idx
                            st.session_state["proj_edit_idx"] = None
                            st.rerun()

                    with col_checks:
                        st.markdown("**⚙️ Etapas do Projeto**")
                        etapas_atuais = get_etapas(row)
                        novas_etapas  = []
                        for i,etapa in enumerate(ETAPAS_PROJETO):
                            checked = st.checkbox(etapa, value=etapas_atuais[i], key=f"etapa_{idx}_{i}")
                            novas_etapas.append(checked)
                        if novas_etapas != etapas_atuais:
                            atualizar_etapas(idx, novas_etapas)
                            novo_prog = round((sum(novas_etapas)/len(ETAPAS_PROJETO))*100)
                            st.success(f"Progresso atualizado: {novo_prog}%")
                            st.rerun()

        st.divider()
        df_exp = df_filtrado.copy()
        for c in ["Início","Prazo"]:
            if c in df_exp.columns:
                df_exp[c] = df_exp[c].dt.strftime("%d/%m/%Y")
        csv = df_exp.drop(columns=["Etapas"],errors="ignore").to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Exportar CSV", data=csv, file_name="projetos_ti.csv", mime="text/csv")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — NOVO PROJETO
# ══════════════════════════════════════════════════════════════════════════════
with tab_novo:
    st.subheader("Cadastrar Novo Projeto")
    with st.form("form_novo_projeto", clear_on_submit=True):
        col1,col2 = st.columns(2)
        with col1:
            nome        = st.text_input("Nome do Projeto *", placeholder="Ex: Portal do Cliente")
            responsavel = st.text_input("Responsável *",     placeholder="Ex: Ana Silva")
            prioridade  = st.selectbox("Prioridade *",  ["Alta","Média","Baixa"])
            status      = st.selectbox("Status *", ["Em andamento","Pausado","Concluído","Atrasado"])
        with col2:
            inicio    = st.date_input("Data de Início *", value=date.today())
            prazo     = st.date_input("Prazo *",          value=date.today())
            horas     = st.number_input("Horas Gastas", min_value=0, value=0, step=1)
            descricao = st.text_area("Descrição", placeholder="Breve descrição...")
        st.markdown("**⚙️ Etapas iniciais concluídas** *(opcional — você pode marcar depois na aba Projetos)*")
        cols_etapas = st.columns(2)
        etapas_ini = []
        for i,etapa in enumerate(ETAPAS_PROJETO):
            etapas_ini.append(cols_etapas[i%2].checkbox(etapa, value=False, key=f"novo_etapa_{i}"))
        prog_ini = round((sum(etapas_ini)/len(ETAPAS_PROJETO))*100)
        st.info(f"Progresso calculado automaticamente: **{prog_ini}%**")
        enviado = st.form_submit_button("✅ Cadastrar Projeto", use_container_width=True, type="primary")
        if enviado:
            if not nome or not responsavel:
                st.error("Preencha pelo menos Nome e Responsável.")
            elif prazo < inicio:
                st.error("O Prazo não pode ser anterior ao Início.")
            else:
                salvar_projeto({
                    "Projeto":nome, "Responsável":responsavel, "Prioridade":prioridade,
                    "Status":status, "Progresso (%)":prog_ini,
                    "Etapas":",".join(["1" if e else "0" for e in etapas_ini]),
                    "Início":pd.Timestamp(inicio), "Prazo":pd.Timestamp(prazo),
                    "Horas Gastas":horas, "Descrição":descricao,
                })
                st.success(f"✅ Projeto **{nome}** cadastrado! Progresso inicial: {prog_ini}%")
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — CALENDÁRIO
# ══════════════════════════════════════════════════════════════════════════════
with tab_cal:
    import json as _json
    import streamlit.components.v1 as _cv1
    hoje_cal = date.today()

    reunioes = carregar_reunioes()

    sub_cal, sub_gerenciar = st.tabs(["Calendário", "⚙️ Gerenciar Reuniões"])

    with sub_cal:
        with st.form("form_reuniao", clear_on_submit=True):
            st.markdown("##### Agendar Reunião")
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
            if st.form_submit_button("✅ Salvar Reunião", use_container_width=True, type="primary"):
                if not titulo_r or not responsavel_r or not participantes or not empresa:
                    st.error("Preencha os campos obrigatórios *.")
                else:
                    salvar_reuniao({
                        "Título":titulo_r, "Responsável":responsavel_r,
                        "Participantes":participantes, "Empresa":empresa,
                        "Data":pd.Timestamp(data_r),
                        "Horário":f"{hora_h:02d}:{hora_m:02d}",
                        "Local":local, "Observações":obs_r,
                    })
                    st.rerun()

        df_cal   = carregar_dados()
        CORES_CAL = ["#00245f","#8b5cf6","#ec4899","#f59e0b","#10b981","#00d339","#06b6d4","#f97316"]
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
                        "id": f"r_{pos}", "title": f"{hora} · {r['Título']}",
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
                    cor_p     = CORES_STATUS.get(status_p,"#64748b")
                    prog_p = int(row.get("Progresso (%)", 0))
                    eventos.append({
                        "id": f"p_{idx}", "title": f"📌 {row['Projeto']} · {prog_p}%",
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
<html><head><meta charset='utf-8'><style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&display=swap');
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:'DM Sans',sans-serif;background:#0f1729;color:#eef5ef;padding:10px;}
.nav{display:flex;align-items:center;gap:6px;margin-bottom:12px;}
.nav-btn{background:#0e1117;color:#5a7d60;border:1px solid rgba(0,210,60,0.16);border-radius:7px;padding:5px 14px;cursor:pointer;font-size:12px;font-weight:600;transition:all 0.2s;}
.nav-btn:hover{background:rgb(0,210,60);color:#060e08;border-color:rgb(0,210,60);}
.nav-title{flex:1;text-align:center;font-size:15px;font-weight:700;color:#eef5ef;}
.grid{display:grid;grid-template-columns:repeat(7,1fr);gap:3px;}
.hdr{background:#0e1117;text-align:center;font-size:10px;font-weight:700;color:rgba(0,210,60,0.5);padding:7px 2px;border-radius:6px;letter-spacing:1px;text-transform:uppercase;}
.cell{background:#262730;border-radius:8px;min-height:90px;padding:6px 5px;border:1px solid rgba(0,210,60,0.08);transition:border-color 0.2s;}
.cell:hover{border-color:rgba(0,210,60,0.3);}
.cell.other-month{opacity:.25;}
.cell.today{background:#0d2212;border-color:rgb(0,210,60)!important;box-shadow:0 0 12px rgba(0,210,60,0.15);}
.day-num{font-size:11px;color:#5a7d60;margin-bottom:3px;font-weight:500;}
.cell.today .day-num{color:#060e08;font-weight:800;background:rgb(0,210,60);border-radius:50%;width:20px;height:20px;display:flex;align-items:center;justify-content:center;}
.ev{border-radius:4px;padding:2px 5px;font-size:10px;margin-bottom:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#fff;font-weight:600;}
.more{font-size:10px;color:#5a7d60;margin-top:1px;}
</style></head><body>
<div class='nav'>
  <button class='nav-btn' onclick='prev()'>&#8249; Anterior</button>
  <button class='nav-btn' onclick='goToday()'>Hoje</button>
  <span class='nav-title' id='title'></span>
  <button class='nav-btn' onclick='next()'>Próximo &#8250;</button>
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
  document.getElementById('title').textContent=MESES[m]+' '+y;
  var g=document.getElementById('grid');g.innerHTML='';
  DIAS.forEach(function(d){var h=document.createElement('div');h.className='hdr';h.textContent=d;g.appendChild(h);});
  var fd=new Date(y,m,1).getDay(),td=new Date(y,m+1,0).getDate(),pd=new Date(y,m,0).getDate();
  for(var i=0;i<fd;i++){var c=mk();c.classList.add('other-month');var dn=mkd('day-num',pd-fd+1+i);c.appendChild(dn);g.appendChild(c);}
  for(var d=1;d<=td;d++){
    var dt=new Date(y,m,d);dt.setHours(0,0,0,0);
    var c=mk();if(dt.getTime()===today.getTime())c.classList.add('today');
    c.appendChild(mkd('day-num',d));
    var evs=evDay(y,m,d);
    evs.slice(0,3).forEach(function(e){
      var el=mkd('ev',e.title);
      el.style.background=e.backgroundColor||'#3b82f6';
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
            st.markdown("#### Reuniões Agendadas")
            if reunioes.empty:
                st.info("Nenhuma reunião agendada ainda.")
            else:
                for pos, (_, row) in enumerate(reunioes.iterrows()):
                    data_fmt = pd.to_datetime(row["Data"]).strftime("%d/%m/%Y") if pd.notna(row["Data"]) else "—"
                    with st.container():
                        col_info, col_btn = st.columns([5,1])
                        with col_info:
                            st.markdown(
                                f"**{row['Título']}** &nbsp;|&nbsp; "
                                f"{data_fmt} {row.get('Horário','')} &nbsp;|&nbsp; "
                                f"{row.get('Responsável','')} &nbsp;|&nbsp; "
                                f"🏢 {row.get('Empresa','')}"
                            )
                            loc = str(row.get("Local",""))
                            obs = str(row.get("Observações",""))
                            extra = []
                            if loc and loc not in ("nan",""): extra.append(f"📍 {loc}")
                            if obs and obs not in ("nan",""): extra.append(f"📝 {obs}")
                            if extra:
                                st.caption(" · ".join(extra))
                        with col_btn:
                            if st.button("🗑️", key=f"del_{pos}", help="Excluir reunião"):
                                deletar_reuniao(pos)
                                st.toast("Reunião excluída!", icon="🗑️")
                                st.rerun()
                        st.divider()

        with col_projetos:
            st.markdown("#### Progresso dos Projetos")
            df_prog = carregar_dados()
            if df_prog.empty:
                st.info("Nenhum projeto cadastrado.")
            else:
                df_prog = df_prog.sort_values("Progresso (%)", ascending=False)
                for _, proj in df_prog.iterrows():
                    prog = int(proj.get("Progresso (%)", 0))
                    status_p = str(proj.get("Status",""))
                    cor = CORES_STATUS.get(status_p, "#64748b")
                    prazo_p = pd.to_datetime(proj["Prazo"]).strftime("%d/%m") if pd.notna(proj.get("Prazo")) else "—"
                    st.markdown(
                        f"<div style='margin-bottom:2px;font-size:13px;font-weight:600;color:#e2e8f0'>"
                        f"{proj['Projeto']}"
                        f"<span style='float:right;font-size:12px;color:{cor};font-weight:700'>{prog}%</span>"
                        f"</div>"
                        f"<div style='font-size:11px;color:#64748b;margin-bottom:5px'>"
                        f"{proj.get('Responsável','')} &nbsp;·&nbsp; até {prazo_p} &nbsp;·&nbsp; "
                        f"<span style='color:{cor}'>{status_p}</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                    st.progress(prog / 100)
                    st.markdown("<div style='margin-bottom:10px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — SPRINT SEMANAL
# ══════════════════════════════════════════════════════════════════════════════
with tab_sprint:
    st.subheader("Sprint Semanal")

    sprints   = carregar_sprints()
    seg_atual = segunda_da_semana()

    if "sprint_edit_idx" not in st.session_state:
        st.session_state["sprint_edit_idx"] = None

    col_form_sp, col_hist = st.columns([2, 3], gap="large")

    with col_form_sp:
        label_semana = f"Semana {seg_atual.strftime('%d/%m/%Y')}"
        st.markdown(f"#### Registrar Sprint — {label_semana}")

        with st.form("form_sprint", clear_on_submit=True):
            bu = st.selectbox("BU / Área *", [
                "Estratégia & Projetos",
                "Governança & Sustentação",
            ])
            responsavel_sp = st.text_input("Responsável *", placeholder="Ex: Ana Silva")
            progressos = st.text_area(
                "Progressos da semana *",
                placeholder="- Concluímos o módulo X\n- Finalizamos a migração Y",
                height=110
            )
            desafios = st.text_area(
                "Desafios",
                placeholder="- Atraso na entrega do fornecedor Z",
                height=90
            )
            proxima = st.text_area(
                "Próxima Sprint",
                placeholder="- Iniciar módulo W\n- Reunião com cliente",
                height=90
            )
            meta = st.text_input(
                "Meta da semana",
                placeholder="Ex: Disp. Core 98,5% | QA Projetos"
            )
            realizado = st.text_input(
                "Realizado vs Meta",
                placeholder="Ex: 98,7% ✅"
            )
            ok_sp = st.form_submit_button("Salvar Sprint", use_container_width=True, type="primary")

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
                            "Semana":       pd.Timestamp(seg_atual),
                            "BU":           bu,
                            "Responsável":  responsavel_sp,
                            "Progressos":   progressos,
                            "Desafios":     desafios,
                            "Próxima Sprint": proxima,
                            "Meta":         meta,
                            "Realizado":    realizado,
                        })
                        st.success(f"✅ Sprint de **{responsavel_sp}** ({bu}) salva!")
                        st.rerun()

    with col_hist:
        st.markdown("#### Histórico de Sprints")

        if sprints.empty:
            st.info("Nenhuma sprint registrada ainda.")
        else:
            sprints_ord = sprints.sort_values("Semana", ascending=False).copy()
            sprints_ord["Semana"] = pd.to_datetime(sprints_ord["Semana"])

            fc1, fc2 = st.columns(2)
            bus_disponiveis = ["Todas"] + sorted(sprints_ord["BU"].dropna().unique().tolist())
            filtro_bu  = fc1.selectbox("Filtrar por BU", bus_disponiveis, key="filtro_bu_sprint")
            semanas_disponiveis = sprints_ord["Semana"].dt.strftime("%d/%m/%Y").unique().tolist()
            filtro_sem = fc2.selectbox("Filtrar por Semana", ["Todas"] + semanas_disponiveis, key="filtro_sem_sprint")

            df_hist = sprints_ord.copy()
            if filtro_bu != "Todas":
                df_hist = df_hist[df_hist["BU"] == filtro_bu]
            if filtro_sem != "Todas":
                df_hist = df_hist[df_hist["Semana"].dt.strftime("%d/%m/%Y") == filtro_sem]

            if df_hist.empty:
                st.warning("Nenhuma sprint encontrada com os filtros selecionados.")
            else:
                st.caption(f"{len(df_hist)} sprint(s) encontrada(s)")

                for sp_idx, (raw_idx, sp) in enumerate(df_hist.iterrows()):
                    semana_ts  = pd.to_datetime(sp["Semana"])
                    semana_str = semana_ts.strftime("%d/%m/%Y") if not pd.isnull(semana_ts) else "—"
                    is_atual   = (not pd.isnull(semana_ts)) and semana_ts.date() == seg_atual

                    with st.expander(
                        f"{'🟢 ' if is_atual else ''}Semana {semana_str} — {sp.get('BU','')} — {sp.get('Responsável','')}",
                        expanded=is_atual
                    ):
                        # ── Botão Editar Sprint ──────────────────────────
                        edit_key = f"sprint_edit_{raw_idx}"
                        if st.session_state["sprint_edit_idx"] == raw_idx:
                            st.markdown("#### ✏️ Editando Sprint")
                            with st.form(f"form_edit_sprint_{raw_idx}"):
                                ep1, ep2 = st.columns(2)
                                meta_e     = ep1.text_input("Meta",      value=str(sp.get("Meta","")) if str(sp.get("Meta","")) != "nan" else "")
                                realiz_e   = ep2.text_input("Realizado", value=str(sp.get("Realizado","")) if str(sp.get("Realizado","")) != "nan" else "")
                                prog_e     = st.text_area("Progressos",    value=str(sp.get("Progressos",""))    if str(sp.get("Progressos","")) != "nan" else "",    height=90)
                                desaf_e    = st.text_area("Desafios",      value=str(sp.get("Desafios",""))      if str(sp.get("Desafios","")) != "nan" else "",      height=80)
                                proxima_e  = st.text_area("Próxima Sprint",value=str(sp.get("Próxima Sprint","")) if str(sp.get("Próxima Sprint","")) != "nan" else "",height=80)
                                es1, es2   = st.columns(2)
                                salvar_sp  = es1.form_submit_button("💾 Salvar", type="primary", use_container_width=True)
                                cancelar_sp= es2.form_submit_button("❌ Cancelar", use_container_width=True)
                                if salvar_sp:
                                    atualizar_sprint(raw_idx, {
                                        "Meta": meta_e, "Realizado": realiz_e,
                                        "Progressos": prog_e, "Desafios": desaf_e,
                                        "Próxima Sprint": proxima_e,
                                    })
                                    st.session_state["sprint_edit_idx"] = None
                                    st.toast("Sprint atualizada!", icon="✅")
                                    st.rerun()
                                if cancelar_sp:
                                    st.session_state["sprint_edit_idx"] = None
                                    st.rerun()
                        else:
                            if st.button("✏️ Editar esta Sprint", key=edit_key):
                                st.session_state["sprint_edit_idx"] = raw_idx
                                st.rerun()

                            col_s1, col_s2 = st.columns(2)
                            with col_s1:
                                st.markdown(f"**Responsável:** {sp.get('Responsável','')}")
                                st.markdown(f"**Meta:** {sp.get('Meta','—')}")
                                st.markdown(f"**Realizado:** {sp.get('Realizado','—')}")
                                st.divider()
                                st.markdown("**Progressos:**")
                                for linha in str(sp.get("Progressos","")).split("\n"):
                                    if linha.strip():
                                        st.markdown(f"- {linha.strip().lstrip('-').strip()}")
                            with col_s2:
                                st.markdown("**Desafios:**")
                                for linha in str(sp.get("Desafios","")).split("\n"):
                                    if linha.strip():
                                        st.markdown(f"- {linha.strip().lstrip('-').strip()}")
                                st.markdown("**Próxima Sprint:**")
                                for linha in str(sp.get("Próxima Sprint","")).split("\n"):
                                    if linha.strip():
                                        st.markdown(f"- {linha.strip().lstrip('-').strip()}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — CHAMADOS
# ══════════════════════════════════════════════════════════════════════════════
with tab_chamados:
    st.subheader("Chamados")

    if "cham_edit_idx"  not in st.session_state: st.session_state["cham_edit_idx"]  = None
    if "cham_del_idx"   not in st.session_state: st.session_state["cham_del_idx"]   = None
    if "cham_obs_idx"   not in st.session_state: st.session_state["cham_obs_idx"]   = None

    df_cham = carregar_chamados()

    sub_lista, sub_novo_cham = st.tabs(["📋 Lista de Chamados", "➕ Novo Chamado"])

    # ══ SUB-TAB: LISTA ════════════════════════════════════════════════════════
    with sub_lista:
        # Filtros rápidos
        fc1, fc2, fc3, fc4 = st.columns(4)
        f_sit  = fc1.multiselect("Situação", SITUACOES_CHAMADO, key="f_sit_cham")
        f_tipo = fc2.multiselect("Tipo", sorted(df_cham["Tipo"].dropna().unique().tolist()) if not df_cham.empty else [], key="f_tipo_cham")
        _fornecedores_disponiveis = sorted([x for x in df_cham.get("Fornecedor", pd.Series()).dropna().unique().tolist() if x and str(x) != "nan"]) if not df_cham.empty else []
        f_forn = fc3.multiselect("Fornecedor", _fornecedores_disponiveis, key="f_forn_cham")
        f_text = fc4.text_input("Buscar (Chave / Resumo / Solicitante)", key="f_text_cham")

        df_vis = df_cham.copy()
        if f_sit:   df_vis = df_vis[df_vis["Situação"].isin(f_sit)]
        if f_tipo:  df_vis = df_vis[df_vis["Tipo"].isin(f_tipo)]
        if f_forn and "Fornecedor" in df_vis.columns:
            df_vis = df_vis[df_vis["Fornecedor"].isin(f_forn)]
        if f_text:  df_vis = df_vis[
            df_vis["Chave"].str.contains(f_text, case=False, na=False) |
            df_vis["Resumo"].str.contains(f_text, case=False, na=False) |
            df_vis["Solicitante"].str.contains(f_text, case=False, na=False)
        ]

        if df_vis.empty:
            st.info("Nenhum chamado encontrado.")
        else:
            st.caption(f"{len(df_vis)} chamado(s) encontrado(s)")
            st.divider()

            for i, (raw_idx, row) in enumerate(df_vis.iterrows()):
                sit = str(row.get("Situação",""))
                badge_map = {
                    "Atendido":    "badge-atendido",
                    "Aberto":      "badge-aberto",
                    "Em Andamento":"badge-andamento",
                    "Cancelado":   "badge-cancelado",
                    "Aguardando":  "badge-aguardando",
                }
                badge_cls = badge_map.get(sit, "badge-aberto")

                with st.expander(
                    f"**{row.get('Chave','—')}** · {row.get('Resumo','')[:80]}  |  {sit}",
                    expanded=False
                ):
                    # ── Confirmação exclusão ─────────────────────────────
                    if st.session_state["cham_del_idx"] == raw_idx:
                        st.warning(f"⚠️ Excluir chamado **{row.get('Chave','—')}**? Ação irreversível.")
                        cd1, cd2 = st.columns(2)
                        if cd1.button("✅ Confirmar", key=f"conf_del_cham_{raw_idx}", type="primary"):
                            deletar_chamado(raw_idx)
                            st.session_state["cham_del_idx"] = None
                            st.toast("Chamado excluído!", icon="🗑️")
                            st.rerun()
                        if cd2.button("❌ Cancelar", key=f"canc_del_cham_{raw_idx}"):
                            st.session_state["cham_del_idx"] = None
                            st.rerun()

                    # ── Formulário de edição ──────────────────────────────
                    elif st.session_state["cham_edit_idx"] == raw_idx:
                        st.markdown("#### ✏️ Editando Chamado")
                        with st.form(f"form_edit_cham_{raw_idx}"):
                            ce1, ce2 = st.columns(2)
                            tipo_e   = ce1.text_input("Tipo",        value=str(row.get("Tipo","")))
                            chave_e  = ce1.text_input("Chave",       value=str(row.get("Chave","")))
                            resumo_e = ce1.text_input("Resumo",      value=str(row.get("Resumo","")))
                            forn_e   = ce1.text_input("Fornecedor",  value=str(row.get("Fornecedor","")) if str(row.get("Fornecedor","")) != "nan" else "")
                            solic_e  = ce2.text_input("Solicitante", value=str(row.get("Solicitante","")))
                            criado_e = ce2.text_input("Criado",      value=str(row.get("Criado","")))
                            fechado_e= ce2.text_input("Fechado",     value=str(row.get("Fechado","")))
                            sit_opts = SITUACOES_CHAMADO
                            sit_idx  = sit_opts.index(sit) if sit in sit_opts else 0
                            sit_e    = ce1.selectbox("Situação", sit_opts, index=sit_idx)
                            impacta_e= st.text_input("Onde Impacta", value=str(row.get("Onde Impacta","")) if str(row.get("Onde Impacta","")) != "nan" else "")
                            obs_e    = st.text_area("Obs", value=str(row.get("Obs","")) if str(row.get("Obs","")) != "nan" else "", height=100)
                            sv1, sv2 = st.columns(2)
                            salvar_ce   = sv1.form_submit_button("💾 Salvar", type="primary", use_container_width=True)
                            cancelar_ce = sv2.form_submit_button("❌ Cancelar", use_container_width=True)
                            if salvar_ce:
                                atualizar_chamado(raw_idx, {
                                    "Tipo": tipo_e, "Chave": chave_e, "Resumo": resumo_e,
                                    "Fornecedor": forn_e,
                                    "Solicitante": solic_e, "Criado": criado_e, "Fechado": fechado_e,
                                    "Situação": sit_e, "Onde Impacta": impacta_e, "Obs": obs_e,
                                })
                                st.session_state["cham_edit_idx"] = None
                                st.toast("Chamado atualizado!", icon="✅")
                                st.rerun()
                            if cancelar_ce:
                                st.session_state["cham_edit_idx"] = None
                                st.rerun()

                    # ── Visualização normal + modal de observação ─────────
                    else:
                        # Dados principais (sem ID)
                        r1, r2, r3 = st.columns([2,2,2])
                        r1.markdown(f"**Tipo:** {row.get('Tipo','—')}")
                        r1.markdown(f"**Chave:** {row.get('Chave','—')}")
                        r1.markdown(f"**Fornecedor:** {row.get('Fornecedor','—')}")
                        r2.markdown(f"**Solicitante:** {row.get('Solicitante','—')}")
                        r2.markdown(f"**Criado:** {row.get('Criado','—')}")
                        r2.markdown(f"**Fechado:** {row.get('Fechado','—')}")
                        r3.markdown(f"**Situação:** {sit}")
                        r3.markdown(f"**Onde Impacta:** {row.get('Onde Impacta','—')}")

                        resumo_full = str(row.get("Resumo",""))
                        if resumo_full and resumo_full != "nan":
                            st.markdown(f"**Resumo:** {resumo_full}")

                        obs_atual = str(row.get("Obs",""))
                        if obs_atual and obs_atual not in ("nan",""):
                            st.markdown("**Observações:**")
                            st.info(obs_atual)

                        # Botões de ação (sem excluir)
                        ba1, ba2 = st.columns(2)

                        if ba1.button("📝 Obs / Atualizar", key=f"obs_btn_{raw_idx}", use_container_width=True):
                            st.session_state["cham_obs_idx"]  = raw_idx
                            st.session_state["cham_edit_idx"] = None
                            st.session_state["cham_del_idx"]  = None
                            st.rerun()

                        if ba2.button("✏️ Editar", key=f"edit_cham_{raw_idx}", use_container_width=True):
                            st.session_state["cham_edit_idx"] = raw_idx
                            st.session_state["cham_obs_idx"]  = None
                            st.session_state["cham_del_idx"]  = None
                            st.rerun()

                    # ── Painel de nova observação (fora do else para aparecer junto) ──
                    if st.session_state["cham_obs_idx"] == raw_idx and st.session_state["cham_edit_idx"] != raw_idx:
                        st.divider()
                        st.markdown("##### 📝 Adicionar Observação")
                        obs_atual_txt = str(row.get("Obs","")) if str(row.get("Obs","")) not in ("nan","") else ""
                        with st.form(f"form_obs_{raw_idx}"):
                            data_obs  = st.text_input("Data (ex: 24/03/2026)", value=date.today().strftime("%d/%m/%Y"))
                            nova_obs  = st.text_area("Observação *", height=90, placeholder="Descreva a atualização...")
                            op1, op2  = st.columns(2)
                            salvar_o  = op1.form_submit_button("💾 Salvar Obs", type="primary", use_container_width=True)
                            cancelar_o= op2.form_submit_button("❌ Cancelar", use_container_width=True)
                            if salvar_o and nova_obs.strip():
                                separador = "\n\n---\n" if obs_atual_txt else ""
                                obs_nova_completa = f"{obs_atual_txt}{separador}[{data_obs}] {nova_obs.strip()}"
                                atualizar_chamado(raw_idx, {"Obs": obs_nova_completa})
                                st.session_state["cham_obs_idx"] = None
                                st.toast("Observação adicionada!", icon="📝")
                                st.rerun()
                            if cancelar_o:
                                st.session_state["cham_obs_idx"] = None
                                st.rerun()

    # ══ SUB-TAB: NOVO CHAMADO ══════════════════════════════════════════════════
    with sub_novo_cham:
        st.markdown("#### Registrar Novo Chamado")
        with st.form("form_novo_chamado", clear_on_submit=True):
            nc1, nc2 = st.columns(2)
            tipo_n      = nc1.text_input("Tipo *",        placeholder="Ex: Reportar Incidente")
            chave_n     = nc1.text_input("Chave *",       placeholder="Ex: NCS-84376")
            resumo_n    = nc1.text_input("Resumo *",      placeholder="Breve descrição do chamado")
            forn_n      = nc1.text_input("Fornecedor",    placeholder="Ex: Sinqia, Nexios, NCS...")
            solic_n     = nc2.text_input("Solicitante *", placeholder="Nome do solicitante")
            criado_n    = nc2.text_input("Criado",        placeholder="dd/mm/aaaa", value=date.today().strftime("%d/%m/%Y"))
            fechado_n   = nc2.text_input("Fechado",       placeholder="dd/mm/aaaa ou deixe em branco")
            sit_n       = nc1.selectbox("Situação *", SITUACOES_CHAMADO)
            impacta_n   = st.text_input("Onde Impacta", placeholder="Ex: Central de Cobrança, Sistema X, NCS...")
            obs_n       = st.text_area("Observações", placeholder="Detalhes, histórico, ações tomadas...", height=100)

            st.form_submit_button_label = "✅ Cadastrar Chamado"
            enviado_cham = st.form_submit_button("✅ Cadastrar Chamado", use_container_width=True, type="primary")

            if enviado_cham:
                if not tipo_n or not chave_n or not resumo_n or not solic_n:
                    st.error("Preencha: Tipo, Chave, Resumo e Solicitante.")
                else:
                    salvar_chamado({
                        "Tipo": tipo_n, "Chave": chave_n, "Resumo": resumo_n,
                        "Fornecedor": forn_n,
                        "Solicitante": solic_n, "Criado": criado_n, "Fechado": fechado_n,
                        "Situação": sit_n, "Onde Impacta": impacta_n, "Obs": obs_n,
                    })
                    st.success(f"✅ Chamado **{chave_n}** cadastrado!")
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 — IA DO TI (mantida sem alterações)
# ══════════════════════════════════════════════════════════════════════════════
with tab_ia:
    st.info("IA do TI — em breve.")