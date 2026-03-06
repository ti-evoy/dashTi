token_valido = st.secrets.get("TOKEN_ACESSO", "")
token_url    = st.query_params.get("token", "")

if token_url != token_valido:
    st.set_page_config(page_title="Acesso Restrito", page_icon="🔒")
    st.error("🔒 Acesso não autorizado.")
    st.stop()

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

# ── Página ────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Dashboard TI", page_icon="📊", layout="wide")

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
    .prio-alta   { color: #ef4444; font-weight: 700; }
    .prio-media  { color: #f59e0b; font-weight: 700; }
    .prio-baixa  { color: #22c55e; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ── Dados globais ─────────────────────────────────────────────────────────────
df = carregar_dados()

CORES_STATUS = {
    "Em andamento": "#3b82f6",
    "Concluído":    "#22c55e",
    "Atrasado":     "#ef4444",
    "Pausado":      "#f59e0b",
}
PRIO_ORDEM = {"Alta": 0, "Média": 1, "Baixa": 2}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📊 TI Dashboard")
    st.divider()
    st.header("🔍 Filtros")
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
    st.button("🔄 Atualizar dados", use_container_width=True)

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
    "📈 Dashboard", "📋 Projetos", "➕ Novo Projeto", "📅 Calendário", "🏃 Sprint"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
with tab_dash:
    st.subheader("Visão Geral")

    if df.empty:
        st.info("Nenhum projeto cadastrado ainda.")
    else:
        total          = len(df_filtrado)
        em_andamento   = len(df_filtrado[df_filtrado["Status"] == "Em andamento"])
        concluidos     = len(df_filtrado[df_filtrado["Status"] == "Concluído"])
        atrasados_n    = len(projetos_atrasados(df_filtrado)) if not df_filtrado.empty else 0
        media_prog     = df_filtrado["Progresso (%)"].mean() if not df_filtrado.empty else 0

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("📁 Total", total)
        c2.metric("🔄 Em Andamento", em_andamento)
        c3.metric("✅ Concluídos", concluidos)
        c4.metric("⚠️ Atrasados", atrasados_n,
                  delta=f"-{atrasados_n}" if atrasados_n > 0 else None, delta_color="inverse")
        c5.metric("📊 Progresso Médio", f"{media_prog:.0f}%")

        st.divider()

        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("#### Status dos Projetos")
            cnt = df_filtrado["Status"].value_counts().reset_index()
            cnt.columns = ["Status", "Qtd"]
            fig = px.pie(cnt, names="Status", values="Qtd",
                         color="Status", color_discrete_map=CORES_STATUS, hole=0.45)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              legend=dict(orientation="h", yanchor="bottom", y=-0.2),
                              margin=dict(t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            st.markdown("#### Progresso (%) por Projeto")
            if not df_filtrado.empty:
                df_p = df_filtrado[["Projeto", "Progresso (%)", "Status"]].sort_values("Progresso (%)")
                # Cores por status
                cor_map = df_p["Status"].map(CORES_STATUS).fillna("#64748b")
                fig2 = go.Figure(go.Bar(
                    x=df_p["Progresso (%)"],
                    y=df_p["Projeto"],
                    orientation="h",
                    marker_color=cor_map.tolist(),
                    text=df_p["Progresso (%)"].astype(int).astype(str) + "%",
                    textposition="outside",
                ))
                fig2.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(range=[0, 115], showgrid=False),
                    yaxis=dict(tickfont=dict(size=11)),
                    margin=dict(t=10, b=10, r=40),
                    showlegend=False,
                )
                st.plotly_chart(fig2, use_container_width=True)

        col_c, col_d = st.columns(2)

        with col_c:
            st.markdown("#### Projetos por Responsável")
            if not df_filtrado.empty:
                rc = df_filtrado["Responsável"].value_counts().reset_index()
                rc.columns = ["Responsável", "Projetos"]
                fig3 = px.bar(rc, x="Responsável", y="Projetos",
                              color="Projetos", color_continuous_scale="Blues")
                fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                   coloraxis_showscale=False, margin=dict(t=10, b=10))
                st.plotly_chart(fig3, use_container_width=True)

        with col_d:
            st.markdown("#### Linha do Tempo (Prazos)")
            if not df_filtrado.empty and "Prazo" in df_filtrado.columns:
                df_g = df_filtrado.dropna(subset=["Início", "Prazo"]).copy()
                if not df_g.empty:
                    fig4 = px.timeline(df_g, x_start="Início", x_end="Prazo",
                                       y="Projeto", color="Status",
                                       color_discrete_map=CORES_STATUS)
                    fig4.update_yaxes(autorange="reversed")
                    fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                       showlegend=False, margin=dict(t=10, b=10))
                    st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — LISTA DE PROJETOS (com checkboxes de etapas)
# ══════════════════════════════════════════════════════════════════════════════
with tab_projetos:
    st.subheader("📋 Projetos")

    if df_filtrado.empty:
        st.info("Nenhum projeto encontrado.")
    else:
        PRIO_ICON = {"Alta": "🔴", "Média": "🟡", "Baixa": "🟢"}

        for idx, row in df_filtrado.iterrows():
            prio_icon = PRIO_ICON.get(str(row.get("Prioridade", "Média")), "🟡")
            prog = int(row.get("Progresso (%)", 0))

            with st.expander(
                f"{prio_icon} **{row['Projeto']}** — {row['Responsável']} | "
                f"{row['Status']} | {prog}%",
                expanded=False
            ):
                col_info, col_checks = st.columns([2, 3])

                with col_info:
                    st.markdown(f"**Prioridade:** {row.get('Prioridade','Média')}")
                    st.markdown(f"**Status:** {row['Status']}")
                    prazo_str = pd.to_datetime(row['Prazo']).strftime('%d/%m/%Y') if pd.notna(row.get('Prazo')) else "—"
                    inicio_str = pd.to_datetime(row['Início']).strftime('%d/%m/%Y') if pd.notna(row.get('Início')) else "—"
                    st.markdown(f"**Início:** {inicio_str}")
                    st.markdown(f"**Prazo:** {prazo_str}")
                    st.markdown(f"**Horas:** {int(row.get('Horas Gastas', 0))}h")
                    if row.get("Descrição") and str(row.get("Descrição")) != "nan":
                        st.markdown(f"**Descrição:** {row['Descrição']}")
                    st.progress(prog / 100)
                    st.caption(f"Progresso: {prog}%")

                with col_checks:
                    st.markdown("**✅ Etapas do Projeto**")
                    etapas_atuais = get_etapas(row)
                    novas_etapas  = []
                    for i, etapa in enumerate(ETAPAS_PROJETO):
                        checked = st.checkbox(
                            etapa,
                            value=etapas_atuais[i],
                            key=f"etapa_{idx}_{i}"
                        )
                        novas_etapas.append(checked)

                    if novas_etapas != etapas_atuais:
                        atualizar_etapas(idx, novas_etapas)
                        novo_prog = round((sum(novas_etapas) / len(ETAPAS_PROJETO)) * 100)
                        st.success(f"Progresso atualizado: {novo_prog}%")
                        st.rerun()

        st.divider()
        df_exp = df_filtrado.copy()
        for c in ["Início", "Prazo"]:
            if c in df_exp.columns:
                df_exp[c] = df_exp[c].dt.strftime("%d/%m/%Y")
        csv = df_exp.drop(columns=["Etapas"], errors="ignore").to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Exportar CSV", data=csv, file_name="projetos_ti.csv", mime="text/csv")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — NOVO PROJETO
# ══════════════════════════════════════════════════════════════════════════════
with tab_novo:
    st.subheader("➕ Cadastrar Novo Projeto")

    with st.form("form_novo_projeto", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome        = st.text_input("Nome do Projeto *", placeholder="Ex: Portal do Cliente")
            responsavel = st.text_input("Responsável *", placeholder="Ex: Ana Silva")
            prioridade  = st.selectbox("Prioridade *", ["Alta", "Média", "Baixa"])
            status      = st.selectbox("Status *", ["Em andamento", "Pausado", "Concluído", "Atrasado"])
        with col2:
            inicio  = st.date_input("Data de Início *", value=date.today())
            prazo   = st.date_input("Prazo *", value=date.today())
            horas   = st.number_input("Horas Gastas", min_value=0, value=0, step=1)
            descricao = st.text_area("Descrição", placeholder="Breve descrição...")

        st.markdown("**✅ Etapas iniciais concluídas** *(opcional — você pode marcar depois na aba Projetos)*")
        cols_etapas = st.columns(2)
        etapas_ini = []
        for i, etapa in enumerate(ETAPAS_PROJETO):
            col_e = cols_etapas[i % 2]
            etapas_ini.append(col_e.checkbox(etapa, value=False, key=f"novo_etapa_{i}"))

        prog_ini = round((sum(etapas_ini) / len(ETAPAS_PROJETO)) * 100)
        st.info(f"Progresso calculado automaticamente: **{prog_ini}%**")

        enviado = st.form_submit_button("✅ Cadastrar Projeto", use_container_width=True, type="primary")
        if enviado:
            if not nome or not responsavel:
                st.error("Preencha pelo menos Nome e Responsável.")
            elif prazo < inicio:
                st.error("O Prazo não pode ser anterior ao Início.")
            else:
                etapas_str = ",".join(["1" if e else "0" for e in etapas_ini])
                salvar_projeto({
                    "Projeto": nome, "Responsável": responsavel,
                    "Prioridade": prioridade, "Status": status,
                    "Progresso (%)": prog_ini, "Etapas": etapas_str,
                    "Início": pd.Timestamp(inicio), "Prazo": pd.Timestamp(prazo),
                    "Horas Gastas": horas, "Descrição": descricao,
                })
                st.success(f"✅ Projeto **{nome}** cadastrado! Progresso inicial: {prog_ini}%")
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — CALENDÁRIO (reuniões + prazos de projetos)
# ══════════════════════════════════════════════════════════════════════════════
with tab_cal:
    try:
        from streamlit_calendar import calendar as st_calendar
        CALENDAR_OK = True
    except ImportError:
        CALENDAR_OK = False
        st.error("⚠️ Instale: `pip install streamlit-calendar` e reinicie.")

    if CALENDAR_OK:
        hoje_cal = date.today()

        with st.expander("➕ Agendar Nova Reunião", expanded=False):
            with st.form("form_reuniao", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                titulo_r      = c1.text_input("Título *", placeholder="Alinhamento Projeto X")
                responsavel_r = c2.text_input("Responsável *", placeholder="Matheus")
                participantes = c3.text_input("Participantes *", placeholder="Rose, João")
                c4, c5, c6, c7 = st.columns(4)
                empresa = c4.text_input("Empresa *", placeholder="Acme Corp")
                data_r  = c5.date_input("Data *", value=hoje_cal)
                horario = c6.text_input("Horário *", placeholder="14:00")
                local   = c7.text_input("Local / Link", placeholder="Sala 3")
                obs     = st.text_area("Observações", height=60)
                if st.form_submit_button("📅 Salvar", use_container_width=True, type="primary"):
                    if not titulo_r or not responsavel_r or not participantes or not empresa or not horario:
                        st.error("Preencha os campos obrigatórios *.")
                    else:
                        salvar_reuniao({
                            "Título": titulo_r, "Responsável": responsavel_r,
                            "Participantes": participantes, "Empresa": empresa,
                            "Data": pd.Timestamp(data_r), "Horário": horario,
                            "Local": local, "Observações": obs,
                        })
                        st.success(f"✅ Reunião **{titulo_r}** salva! Feche o painel para ver no calendário.")

        reunioes = carregar_reunioes()
        df_cal   = carregar_dados()  # fresh

        CORES_CAL = ["#3b82f6","#8b5cf6","#ec4899","#f59e0b","#10b981","#ef4444","#06b6d4","#f97316"]
        eventos = []

        # Reuniões
        if not reunioes.empty:
            for idx, r in reunioes.iterrows():
                try:
                    data_str = pd.to_datetime(r["Data"]).strftime("%Y-%m-%d")
                    hora = str(r["Horário"]).strip()
                    try:
                        h, m = hora.split(":")
                        start = f"{data_str}T{int(h):02d}:{int(m):02d}:00"
                        end   = f"{data_str}T{min(int(h)+1,23):02d}:{int(m):02d}:00"
                    except Exception:
                        start = data_str
                        end   = data_str
                    cor = CORES_CAL[idx % len(CORES_CAL)]
                    eventos.append({
                        "id": f"r_{idx}",
                        "title": f"🤝 {hora} · {r['Título']}",
                        "start": start, "end": end,
                        "backgroundColor": cor, "borderColor": cor,
                        "extendedProps": {
                            "tipo": "reuniao",
                            "responsavel": str(r.get("Responsável","")),
                            "participantes": str(r.get("Participantes","")),
                            "empresa": str(r.get("Empresa","")),
                            "local": str(r.get("Local","")),
                            "obs": str(r.get("Observações","")),
                            "idx": int(idx),
                        }
                    })
                except Exception:
                    pass

        # Prazos dos projetos (dia final de entrega)
        if not df_cal.empty:
            for idx, row in df_cal.iterrows():
                if pd.notna(row.get("Prazo")):
                    prazo_str = pd.to_datetime(row["Prazo"]).strftime("%Y-%m-%d")
                    status_p  = str(row.get("Status",""))
                    cor_p     = CORES_STATUS.get(status_p, "#64748b")
                    eventos.append({
                        "id": f"p_{idx}",
                        "title": f"🏁 Entrega: {row['Projeto']}",
                        "start": prazo_str,
                        "allDay": True,
                        "backgroundColor": cor_p,
                        "borderColor": cor_p,
                        "extendedProps": {
                            "tipo": "prazo",
                            "responsavel": str(row.get("Responsável","")),
                            "status": status_p,
                            "progresso": int(row.get("Progresso (%)", 0)),
                        }
                    })

        opcoes_cal = {
            "initialView": "dayGridMonth",
            "locale": "pt-br",
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "dayGridMonth,timeGridWeek,timeGridDay,listWeek"
            },
            "buttonText": {"today":"Hoje","month":"Mês","week":"Semana","day":"Dia","list":"Lista"},
            "height": 660,
            "selectable": True,
            "editable": False,
            "nowIndicator": True,
            "dayMaxEvents": 4,
            "eventTimeFormat": {"hour":"2-digit","minute":"2-digit","hour12":False},
        }

        custom_css = """
        .fc { font-family: 'Inter','Segoe UI',sans-serif; }
        .fc-toolbar-title { font-size:1.1rem!important; font-weight:700; }
        .fc-button-primary { background:#3b82f6!important; border-color:#2563eb!important; border-radius:6px!important; font-size:0.78rem!important; }
        .fc-button-primary:not(.fc-button-active):hover { background:#2563eb!important; }
        .fc-button-active { background:#1d4ed8!important; }
        .fc-event { border-radius:4px; font-size:0.76rem; padding:1px 4px; cursor:pointer; }
        .fc-day-today { background:rgba(59,130,246,0.07)!important; }
        .fc-daygrid-day-number { font-size:0.8rem; padding:4px 6px; }
        """

        import hashlib, json as _json
        _ev_hash = hashlib.md5(_json.dumps(eventos, default=str).encode()).hexdigest()[:8]
        if "cal_eventos_hash" not in st.session_state or st.session_state["cal_eventos_hash"] != _ev_hash:
            st.session_state["cal_eventos_hash"] = _ev_hash
            st.session_state["cal_key"] = _ev_hash
        if "cal_key" not in st.session_state:
            st.session_state["cal_key"] = "init"

        col_cal_v, col_detail = st.columns([4, 1])
        with col_cal_v:
            resultado = st_calendar(
                events=eventos,
                options=opcoes_cal,
                custom_css=custom_css,
                key="fullcalendar_" + st.session_state["cal_key"]
            )

        with col_detail:
            st.markdown("#### 🗓️ Detalhe")
            if resultado and resultado.get("eventClick"):
                ev    = resultado["eventClick"]["event"]
                props = ev.get("extendedProps", {})
                tipo  = props.get("tipo", "")

                if tipo == "reuniao":
                    titulo_ev = ev.get("title","").split("·",1)
                    st.markdown(f"**🤝 {titulo_ev[-1].strip() if len(titulo_ev)>1 else titulo_ev[0]}**")
                    st.markdown(f"👤 **{props.get('responsavel','')}**")
                    st.markdown(f"🤝 {props.get('participantes','')}")
                    st.markdown(f"🏢 {props.get('empresa','')}")
                    if props.get("local") and props.get("local") != "nan":
                        st.markdown(f"📍 {props['local']}")
                    if props.get("obs") and props.get("obs") != "nan":
                        st.markdown(f"📝 {props['obs']}")
                    st.divider()
                    if st.button("🗑️ Excluir reunião", type="secondary", use_container_width=True):
                        deletar_reuniao(int(props.get("idx", 0)))
                        st.rerun()

                elif tipo == "prazo":
                    titulo_ev = ev.get("title","").replace("🏁 Entrega: ","")
                    st.markdown(f"**🏁 {titulo_ev}**")
                    st.markdown(f"👤 {props.get('responsavel','')}")
                    st.markdown(f"📌 Status: {props.get('status','')}")
                    st.markdown(f"📊 Progresso: {props.get('progresso',0)}%")
                    st.progress(int(props.get('progresso', 0)) / 100)
            else:
                st.caption("Clique em um evento para ver os detalhes.")
                futuras = (
                    reunioes[pd.to_datetime(reunioes["Data"]).dt.date >= hoje_cal].sort_values("Data")
                    if not reunioes.empty else pd.DataFrame()
                )
                if not futuras.empty:
                    st.markdown(f"**🔔 Próximas reuniões ({len(futuras)})**")
                    for _, r in futuras.head(5).iterrows():
                        dt = pd.to_datetime(r["Data"])
                        badge = "🟡" if dt.date() == hoje_cal else "🔵"
                        st.markdown(
                            f"{badge} **{r['Título']}**  \n"
                            f"<small>{dt.strftime('%d/%m')} {r['Horário']} · {r['Responsável']}</small>",
                            unsafe_allow_html=True
                        )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — SPRINT SEMANAL
# ══════════════════════════════════════════════════════════════════════════════
with tab_sprint:
    st.subheader("🏃 Sprint Semanal")

    sprints = carregar_sprints()
    seg_atual = segunda_da_semana()
    seg_prox  = proxima_segunda()

    # Sprint da semana atual já existe?
    sprint_existe = False
    if not sprints.empty:
        sprint_existe = any(
            pd.to_datetime(sprints["Semana"]).dt.date == seg_atual
        )

    col_form_sp, col_hist = st.columns([2, 3], gap="large")

    with col_form_sp:
        label_semana = f"Semana {seg_atual.strftime('%d/%m/%Y')}"
        st.markdown(f"#### ✍️ Registrar Sprint — {label_semana}")

        if sprint_existe:
            st.info(f"✅ Sprint da semana **{label_semana}** já registrada!")
            if st.button("Registrar sprint adicional desta semana"):
                sprint_existe = False  # libera o form

        if not sprint_existe:
            with st.form("form_sprint", clear_on_submit=True):
                bu = st.selectbox("BU / Área *", [
                    "Estratégia & Projetos",
                    "Governança & Sustentação",
                ])
                responsavel_sp = st.text_input("Responsável *", placeholder="Ex: Ana Silva")
                progressos = st.text_area(
                    "📈 Progressos da semana *",
                    placeholder="- Concluímos o módulo X\n- Finalizamos a migração Y",
                    height=110
                )
                desafios = st.text_area(
                    "⚠️ Desafios",
                    placeholder="- Atraso na entrega do fornecedor Z",
                    height=90
                )
                proxima = st.text_area(
                    "🔜 Próxima Sprint",
                    placeholder="- Iniciar módulo W\n- Reunião com cliente",
                    height=90
                )
                meta = st.text_input(
                    "🎯 Meta da semana",
                    placeholder="Ex: Disp. Core 98,5% | QA Projetos"
                )
                realizado = st.text_input(
                    "✅ Realizado vs Meta",
                    placeholder="Ex: 98,7% ✅"
                )
                ok_sp = st.form_submit_button("💾 Salvar Sprint", use_container_width=True, type="primary")

                if ok_sp:
                    if not bu or not responsavel_sp or not progressos:
                        st.error("Preencha BU, Responsável e Progressos.")
                    else:
                        salvar_sprint({
                            "Semana": pd.Timestamp(seg_atual),
                            "BU": bu,
                            "Responsável": responsavel_sp,
                            "Progressos": progressos,
                            "Desafios": desafios,
                            "Próxima Sprint": proxima,
                            "Meta": meta,
                            "Realizado": realizado,
                        })
                        st.success(f"✅ Sprint da semana **{label_semana}** salva!")
                        st.rerun()

    with col_hist:
        st.markdown("#### 📚 Histórico de Sprints")

        if sprints.empty:
            st.info("Nenhuma sprint registrada ainda.")
        else:
            sprints_ord = sprints.sort_values("Semana", ascending=False)

            for _, sp in sprints_ord.iterrows():
                semana_str = pd.to_datetime(sp["Semana"]).strftime("%d/%m/%Y")
                is_atual   = pd.to_datetime(sp["Semana"]).date() == seg_atual

                with st.expander(
                    f"{'🟢 ' if is_atual else ''}Semana {semana_str} — {sp.get('BU','')}"
                    f"{' ← ATUAL' if is_atual else ''}",
                    expanded=is_atual
                ):
                    col_s1, col_s2 = st.columns(2)
                    with col_s1:
                        st.markdown(f"**👤 Responsável:** {sp.get('Responsável','')}")
                        st.markdown(f"**🎯 Meta:** {sp.get('Meta','—')}")
                        st.markdown(f"**✅ Realizado:** {sp.get('Realizado','—')}")
                        st.divider()
                        st.markdown("**📈 Progressos:**")
                        for linha in str(sp.get("Progressos","")).split("\n"):
                            if linha.strip():
                                st.markdown(f"- {linha.strip().lstrip('-').strip()}")
                    with col_s2:
                        st.markdown("**⚠️ Desafios:**")
                        for linha in str(sp.get("Desafios","")).split("\n"):
                            if linha.strip():
                                st.markdown(f"- {linha.strip().lstrip('-').strip()}")
                        st.markdown("**🔜 Próxima Sprint:**")
                        for linha in str(sp.get("Próxima Sprint","")).split("\n"):
                            if linha.strip():
                                st.markdown(f"- {linha.strip().lstrip('-').strip()}")