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

# ── Proteção por token na URL ─────────────────────────────────────────────────
_token_valido = st.secrets.get("TOKEN_ACESSO", "")
_token_url    = st.query_params.get("token", "")
if _token_valido and _token_url != _token_valido:
    st.error("🔒 Acesso não autorizado. Verifique o link com sua equipe.")
    st.stop()

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

    :root {
        --g:      rgb(0,210,60);
        --g-dim:  rgba(0,210,60,0.12);
        --g-glow: rgba(0,210,60,0.30);
        --bg:     #080f0a;
        --card:   #0d1810;
        --card2:  #101f13;
        --border: rgba(0,210,60,0.16);
        --txt:    #eef5ef;
        --muted:  #5a7d60;
    }

    html, body, [data-testid="stAppViewContainer"] {
        background-color: var(--bg) !important;
        font-family: 'DM Sans', sans-serif !important;
        color: var(--txt) !important;
    }
    .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; max-width:1400px !important; }

    /* Header */
    header[data-testid="stHeader"] {
        background: rgba(8,15,10,0.97) !important;
        backdrop-filter: blur(12px) !important;
        border-bottom: 1px solid var(--border) !important;
    }

    /* Sidebar */
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg,#060e08 0%,#0a1a0c 100%) !important;
        border-right: 1px solid var(--border) !important;
    }
    div[data-testid="stSidebar"] label, div[data-testid="stSidebar"] p { color: var(--muted) !important; font-size:0.82rem !important; }

    /* Tabs */
    button[data-baseweb="tab"] { font-family:'DM Sans',sans-serif !important; font-weight:600 !important; font-size:0.85rem !important; color:var(--muted) !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color:var(--g) !important; }
    div[data-baseweb="tab-highlight"] { background:var(--g) !important; height:2px !important; }
    div[data-baseweb="tab-border"] { background:var(--border) !important; }

    /* Métricas */
    div[data-testid="metric-container"] {
        background: var(--card) !important; border:1px solid var(--border) !important;
        border-radius:12px !important; padding:1rem 1.2rem !important;
        position:relative !important; overflow:hidden !important;
    }
    div[data-testid="metric-container"]::before {
        content:''; position:absolute; top:0; left:0; right:0; height:2px; background:var(--g);
    }
    div[data-testid="metric-container"] label { font-size:0.75rem !important; color:var(--muted) !important; text-transform:uppercase !important; letter-spacing:1px !important; font-weight:600 !important; }
    div[data-testid="metric-container"] [data-testid="stMetricValue"] { color:var(--txt) !important; font-size:1.9rem !important; font-weight:700 !important; font-family:'DM Mono',monospace !important; }

    /* Botões primários */
    button[kind="primary"], button[data-testid="baseButton-primary"] {
        background: var(--g) !important; color:#060e08 !important; font-weight:700 !important;
        border:none !important; border-radius:8px !important;
        box-shadow: 0 0 18px var(--g-glow) !important; transition:all 0.2s !important;
    }
    button[kind="primary"]:hover { background:#00f040 !important; transform:translateY(-1px) !important; box-shadow:0 0 28px var(--g-glow) !important; }

    /* Botões secundários */
    button[kind="secondary"], button[data-testid="baseButton-secondary"] {
        background:transparent !important; color:var(--g) !important;
        border:1px solid var(--border) !important; border-radius:8px !important; transition:all 0.2s !important;
    }
    button[kind="secondary"]:hover { border-color:var(--g) !important; background:var(--g-dim) !important; }

    /* Inputs */
    div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input, textarea {
        background:var(--card2) !important; border:1px solid var(--border) !important;
        border-radius:8px !important; color:var(--txt) !important; font-family:'DM Sans',sans-serif !important;
    }
    div[data-testid="stTextInput"] input:focus, textarea:focus {
        border-color:var(--g) !important; box-shadow:0 0 0 2px var(--g-dim) !important;
    }
    div[data-baseweb="select"] > div {
        background:var(--card2) !important; border:1px solid var(--border) !important;
        border-radius:8px !important; color:var(--txt) !important;
    }

    /* Expanders */
    details[data-testid="stExpander"] {
        background:var(--card) !important; border:1px solid var(--border) !important;
        border-radius:12px !important; overflow:hidden !important; transition:border-color 0.2s !important;
    }
    details[data-testid="stExpander"]:hover { border-color:rgba(0,210,60,0.4) !important; }
    details[data-testid="stExpander"] summary { font-weight:600 !important; color:var(--txt) !important; padding:0.8rem 1rem !important; }
    details[data-testid="stExpander"] summary:hover { color:var(--g) !important; }

    /* Progress bar */
    div[data-testid="stProgress"] > div > div { background:var(--g) !important; box-shadow:0 0 8px var(--g-glow) !important; border-radius:4px !important; }
    div[data-testid="stProgress"] > div { background:var(--card2) !important; border-radius:4px !important; }

    /* Slider */
    div[data-testid="stSlider"] [role="slider"] { background:var(--g) !important; box-shadow:0 0 10px var(--g-glow) !important; }

    /* Divider */
    hr { border-color:var(--border) !important; margin:0.8rem 0 !important; }

    /* Headings */
    h1,h2,h3,h4 { font-family:'DM Sans',sans-serif !important; color:var(--txt) !important; font-weight:700 !important; letter-spacing:-0.3px !important; }

    /* Sprint card */
    .sprint-card { background:var(--card); border-radius:12px; padding:1rem 1.2rem; margin-bottom:0.8rem; border-left:3px solid var(--g); box-shadow:0 0 20px rgba(0,210,60,0.04); }
    .sprint-card h4 { margin:0 0 0.4rem 0; color:var(--txt); font-size:0.95rem; }
    .sprint-card p  { margin:0.15rem 0; color:var(--muted); font-size:0.82rem; }

    /* Prioridades */
    .prio-alta  { color:#ff4d4d; font-weight:700; }
    .prio-media { color:#f59e0b; font-weight:700; }
    .prio-baixa { color:var(--g); font-weight:700; }

    /* Scrollbar */
    ::-webkit-scrollbar { width:5px; height:5px; }
    ::-webkit-scrollbar-track { background:var(--bg); }
    ::-webkit-scrollbar-thumb { background:rgba(0,210,60,0.25); border-radius:3px; }
    ::-webkit-scrollbar-thumb:hover { background:var(--g); }
</style>
""", unsafe_allow_html=True)

# ── Dados globais ─────────────────────────────────────────────────────────────
df = carregar_dados()

CORES_STATUS = {
    "Em andamento": "#3b82f6",
    "Concluído":    "rgb(0,210,60)",
    "Atrasado":     "#ef4444",
    "Pausado":      "#f59e0b",
}
PRIO_ORDEM = {"Alta": 0, "Média": 1, "Baixa": 2}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style="padding:0.5rem 0 1.2rem 0;">
            <img src="app/static/evoy.png"
                 onerror="this.outerHTML='<div style=\\'font-family:DM Sans,sans-serif;font-size:1.5rem;font-weight:800;color:rgb(0,210,60);letter-spacing:-1px;\\'>evoy</div>'"
                 style="height:34px;margin-bottom:5px;display:block;" />
            <div style="font-size:10px;color:rgba(0,210,60,0.45);letter-spacing:2.5px;text-transform:uppercase;font-weight:600;">
                TI Dashboard
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.divider()
    st.markdown("<div style='font-size:11px;color:rgba(0,210,60,0.6);letter-spacing:1.5px;text-transform:uppercase;font-weight:600;margin-bottom:8px'>🔍 Filtros</div>", unsafe_allow_html=True)
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
        total        = len(df_filtrado)
        em_andamento = len(df_filtrado[df_filtrado["Status"] == "Em andamento"])
        concluidos   = len(df_filtrado[df_filtrado["Status"] == "Concluído"])
        atrasados_n  = len(projetos_atrasados(df_filtrado)) if not df_filtrado.empty else 0
        media_prog   = df_filtrado["Progresso (%)"].mean() if not df_filtrado.empty else 0
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("📁 Total", total)
        c2.metric("🔄 Em Andamento", em_andamento)
        c3.metric("✅ Concluídos", concluidos)
        c4.metric("⚠️ Atrasados", atrasados_n,
                  delta=f"-{atrasados_n}" if atrasados_n > 0 else None, delta_color="inverse")
        c5.metric("📊 Progresso Médio", f"{media_prog:.0f}%")
        st.divider()

        _layout = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       font=dict(family="DM Sans", color="#eef5ef"), margin=dict(t=10,b=10))

        col_a,col_b = st.columns(2)
        with col_a:
            st.markdown("#### Status dos Projetos")
            cnt = df_filtrado["Status"].value_counts().reset_index()
            cnt.columns = ["Status","Qtd"]
            fig = px.pie(cnt, names="Status", values="Qtd",
                         color="Status", color_discrete_map=CORES_STATUS, hole=0.45)
            fig.update_layout(**_layout, legend=dict(orientation="h",yanchor="bottom",y=-0.2))
            st.plotly_chart(fig, use_container_width=True)
        with col_b:
            st.markdown("#### Progresso (%) por Projeto")
            if not df_filtrado.empty:
                df_p = df_filtrado[["Projeto","Progresso (%)","Status"]].sort_values("Progresso (%)")
                fig2 = go.Figure(go.Bar(
                    x=df_p["Progresso (%)"], y=df_p["Projeto"], orientation="h",
                    marker_color=df_p["Status"].map(CORES_STATUS).fillna("#64748b").tolist(),
                    text=df_p["Progresso (%)"].astype(int).astype(str)+"%", textposition="outside"))
                fig2.update_layout(**_layout, xaxis=dict(range=[0,115],showgrid=False), showlegend=False, margin=dict(t=10,b=10,r=40))
                st.plotly_chart(fig2, use_container_width=True)
        col_c,col_d = st.columns(2)
        with col_c:
            st.markdown("#### Projetos por Responsável")
            if not df_filtrado.empty:
                rc = df_filtrado["Responsável"].value_counts().reset_index()
                rc.columns = ["Responsável","Projetos"]
                fig3 = px.bar(rc,x="Responsável",y="Projetos",color="Projetos",
                              color_continuous_scale=["#0d3318","rgb(0,210,60)"])
                fig3.update_layout(**_layout, coloraxis_showscale=False)
                st.plotly_chart(fig3, use_container_width=True)
        with col_d:
            st.markdown("#### Linha do Tempo (Prazos)")
            if not df_filtrado.empty and "Prazo" in df_filtrado.columns:
                df_g = df_filtrado.dropna(subset=["Início","Prazo"]).copy()
                if not df_g.empty:
                    fig4 = px.timeline(df_g,x_start="Início",x_end="Prazo",
                                       y="Projeto",color="Status",color_discrete_map=CORES_STATUS)
                    fig4.update_yaxes(autorange="reversed")
                    fig4.update_layout(**_layout, showlegend=False)
                    st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — PROJETOS
# ══════════════════════════════════════════════════════════════════════════════
with tab_projetos:
    st.subheader("📋 Projetos")
    if df_filtrado.empty:
        st.info("Nenhum projeto encontrado.")
    else:
        PRIO_ICON = {"Alta":"🔴","Média":"🟡","Baixa":"🟢"}
        for idx,row in df_filtrado.iterrows():
            prio_icon = PRIO_ICON.get(str(row.get("Prioridade","Média")),"🟡")
            prog = int(row.get("Progresso (%)",0))
            with st.expander(f"{prio_icon} **{row['Projeto']}** — {row['Responsável']} | {row['Status']} | {prog}%",expanded=False):
                col_info,col_checks = st.columns([2,3])
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
                with col_checks:
                    st.markdown("**✅ Etapas do Projeto**")
                    etapas_atuais = get_etapas(row)
                    novas_etapas  = []
                    for i,etapa in enumerate(ETAPAS_PROJETO):
                        checked = st.checkbox(etapa,value=etapas_atuais[i],key=f"etapa_{idx}_{i}")
                        novas_etapas.append(checked)
                    if novas_etapas != etapas_atuais:
                        atualizar_etapas(idx,novas_etapas)
                        novo_prog = round((sum(novas_etapas)/len(ETAPAS_PROJETO))*100)
                        st.success(f"Progresso atualizado: {novo_prog}%")
                        st.rerun()
        st.divider()
        df_exp = df_filtrado.copy()
        for c in ["Início","Prazo"]:
            if c in df_exp.columns:
                df_exp[c] = df_exp[c].dt.strftime("%d/%m/%Y")
        csv = df_exp.drop(columns=["Etapas"],errors="ignore").to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Exportar CSV",data=csv,file_name="projetos_ti.csv",mime="text/csv")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — NOVO PROJETO
# ══════════════════════════════════════════════════════════════════════════════
with tab_novo:
    st.subheader("➕ Cadastrar Novo Projeto")
    with st.form("form_novo_projeto",clear_on_submit=True):
        col1,col2 = st.columns(2)
        with col1:
            nome       = st.text_input("Nome do Projeto *",placeholder="Ex: Portal do Cliente")
            responsavel= st.text_input("Responsável *",placeholder="Ex: Ana Silva")
            prioridade = st.selectbox("Prioridade *",["Alta","Média","Baixa"])
            status     = st.selectbox("Status *",["Em andamento","Pausado","Concluído","Atrasado"])
        with col2:
            inicio    = st.date_input("Data de Início *",value=date.today())
            prazo     = st.date_input("Prazo *",value=date.today())
            horas     = st.number_input("Horas Gastas",min_value=0,value=0,step=1)
            descricao = st.text_area("Descrição",placeholder="Breve descrição...")
        st.markdown("**✅ Etapas iniciais concluídas** *(opcional — você pode marcar depois na aba Projetos)*")
        cols_etapas = st.columns(2)
        etapas_ini = []
        for i,etapa in enumerate(ETAPAS_PROJETO):
            etapas_ini.append(cols_etapas[i%2].checkbox(etapa,value=False,key=f"novo_etapa_{i}"))
        prog_ini = round((sum(etapas_ini)/len(ETAPAS_PROJETO))*100)
        st.info(f"Progresso calculado automaticamente: **{prog_ini}%**")
        enviado = st.form_submit_button("✅ Cadastrar Projeto",use_container_width=True,type="primary")
        if enviado:
            if not nome or not responsavel:
                st.error("Preencha pelo menos Nome e Responsável.")
            elif prazo < inicio:
                st.error("O Prazo não pode ser anterior ao Início.")
            else:
                salvar_projeto({
                    "Projeto":nome,"Responsável":responsavel,"Prioridade":prioridade,
                    "Status":status,"Progresso (%)":prog_ini,
                    "Etapas":",".join(["1" if e else "0" for e in etapas_ini]),
                    "Início":pd.Timestamp(inicio),"Prazo":pd.Timestamp(prazo),
                    "Horas Gastas":horas,"Descrição":descricao,
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
    sub_cal, sub_gerenciar = st.tabs(["📅 Calendário", "🗂️ Gerenciar Reuniões"])

    with sub_cal:
        with st.form("form_reuniao", clear_on_submit=True):
            st.markdown("##### ➕ Agendar Reunião")
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
            if st.form_submit_button("📅 Salvar Reunião", use_container_width=True, type="primary"):
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
        CORES_CAL = ["#00d23c","#8b5cf6","#ec4899","#f59e0b","#06b6d4","#ef4444","#3b82f6","#f97316"]
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
                    cor_p     = CORES_STATUS.get(status_p,"#64748b")
                    prog_p    = int(row.get("Progresso (%)", 0))
                    eventos.append({
                        "id": f"p_{idx}", "title": f"🏁 {row['Projeto']} · {prog_p}%",
                        "start": prazo_str, "allDay": True,
                        "backgroundColor": cor_p, "borderColor": cor_p,
                        "extendedProps": {"tipo":"prazo",
                            "projeto":str(row.get("Projeto","")),
                            "responsavel":str(row.get("Responsável","")),
                            "status":status_p,
                            "progresso":prog_p,}
                    })

        ev_json = _json.dumps(eventos, ensure_ascii=False)
        _cv1.html("""
<html><head><meta charset='utf-8'><style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&display=swap');
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:'DM Sans',sans-serif;background:#080f0a;color:#eef5ef;padding:10px;}
.nav{display:flex;align-items:center;gap:6px;margin-bottom:12px;}
.nav-btn{background:#0d1810;color:#5a7d60;border:1px solid rgba(0,210,60,0.16);border-radius:7px;padding:5px 14px;cursor:pointer;font-size:12px;font-weight:600;font-family:'DM Sans',sans-serif;transition:all 0.2s;}
.nav-btn:hover{background:rgb(0,210,60);color:#060e08;border-color:rgb(0,210,60);}
.nav-title{flex:1;text-align:center;font-size:15px;font-weight:700;color:#eef5ef;letter-spacing:-0.3px;}
.grid{display:grid;grid-template-columns:repeat(7,1fr);gap:3px;}
.hdr{background:#0d1810;text-align:center;font-size:10px;font-weight:700;color:rgba(0,210,60,0.5);padding:7px 2px;border-radius:6px;letter-spacing:1px;text-transform:uppercase;}
.cell{background:#0a150c;border-radius:8px;min-height:90px;padding:6px 5px;border:1px solid rgba(0,210,60,0.08);transition:border-color 0.2s;}
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
      el.style.background=e.backgroundColor||'rgb(0,210,60)';
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
            st.markdown("#### 🗂️ Reuniões Agendadas")
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
                                f"📅 {data_fmt} {row.get('Horário','')} &nbsp;|&nbsp; "
                                f"👤 {row.get('Responsável','')} &nbsp;|&nbsp; "
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
                                st.toast("✅ Reunião excluída!", icon="🗑️")
                                st.rerun()
                        st.divider()

        with col_projetos:
            st.markdown("#### 📊 Progresso dos Projetos")
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
                        f"<div style='margin-bottom:2px;font-size:13px;font-weight:600;color:#eef5ef'>"
                        f"{proj['Projeto']}"
                        f"<span style='float:right;font-size:12px;color:{cor};font-weight:700'>{prog}%</span>"
                        f"</div>"
                        f"<div style='font-size:11px;color:#5a7d60;margin-bottom:5px'>"
                        f"👤 {proj.get('Responsável','')} &nbsp;·&nbsp; 📅 até {prazo_p} &nbsp;·&nbsp; "
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
    st.subheader("🏃 Sprint Semanal")

    sprints   = carregar_sprints()
    seg_atual = segunda_da_semana()

    col_form_sp, col_hist = st.columns([2, 3], gap="large")

    with col_form_sp:
        label_semana = f"Semana {seg_atual.strftime('%d/%m/%Y')}"
        st.markdown(f"#### ✍️ Registrar Sprint — {label_semana}")

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
                    ja_existe = False
                    if not sprints.empty:
                        mask = (
                            (pd.to_datetime(sprints["Semana"]).dt.date == seg_atual) &
                            (sprints["BU"] == bu) &
                            (sprints["Responsável"].str.strip().str.lower() == responsavel_sp.strip().lower())
                        )
                        ja_existe = mask.any()

                    if ja_existe:
                        st.warning(f"⚠️ Sprint de **{bu}** / **{responsavel_sp}** já registrada nesta semana.")
                    else:
                        salvar_sprint({
                            "Semana":         pd.Timestamp(seg_atual),
                            "BU":             bu,
                            "Responsável":    responsavel_sp,
                            "Progressos":     progressos,
                            "Desafios":       desafios,
                            "Próxima Sprint": proxima,
                            "Meta":           meta,
                            "Realizado":      realizado,
                        })
                        st.success(f"✅ Sprint de **{responsavel_sp}** ({bu}) salva!")
                        st.rerun()

    with col_hist:
        st.markdown("#### 📚 Histórico de Sprints")

        if sprints.empty:
            st.info("Nenhuma sprint registrada ainda.")
        else:
            sprints_ord = sprints.sort_values("Semana", ascending=False).copy()
            sprints_ord["Semana"] = pd.to_datetime(sprints_ord["Semana"])

            fc1, fc2 = st.columns(2)
            bus_disponiveis = ["Todas"] + sorted(sprints_ord["BU"].dropna().unique().tolist())
            filtro_bu  = fc1.selectbox("🏢 Filtrar por BU", bus_disponiveis, key="filtro_bu_sprint")
            semanas_disponiveis = sprints_ord["Semana"].dt.strftime("%d/%m/%Y").unique().tolist()
            filtro_sem = fc2.selectbox("📅 Filtrar por Semana", ["Todas"] + semanas_disponiveis, key="filtro_sem_sprint")

            df_hist = sprints_ord.copy()
            if filtro_bu != "Todas":
                df_hist = df_hist[df_hist["BU"] == filtro_bu]
            if filtro_sem != "Todas":
                df_hist = df_hist[df_hist["Semana"].dt.strftime("%d/%m/%Y") == filtro_sem]

            if df_hist.empty:
                st.warning("Nenhuma sprint encontrada com os filtros selecionados.")
            else:
                st.caption(f"{len(df_hist)} sprint(s) encontrada(s)")
                for _, sp in df_hist.iterrows():
                    semana_str = pd.to_datetime(sp["Semana"]).strftime("%d/%m/%Y")
                    is_atual   = pd.to_datetime(sp["Semana"]).date() == seg_atual
                    with st.expander(
                        f"{'🟢 ' if is_atual else ''}Semana {semana_str} — {sp.get('BU','')} — {sp.get('Responsável','')}",
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