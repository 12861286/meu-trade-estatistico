import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# --- 1. CONFIGURAÇÃO E VISUAL ---
st.set_page_config(
    page_title="Quant B3",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    /* ── RESET & BASE ─────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Syne:wght@400;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Syne', sans-serif !important;
    }
    .main .block-container {
        background-color: #07111c;
        padding: 0.75rem 0.85rem 3rem !important;
        max-width: 480px !important;
        margin: 0 auto;
    }

    /* ── HEADER ───────────────────────────────────────── */
    .qb3-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.5rem 0 1rem;
        border-bottom: 1px solid #1a2e40;
        margin-bottom: 1.1rem;
    }
    .qb3-logo-wrap {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    /* Bull icon SVG inline */
    .qb3-icon {
        width: 38px;
        height: 38px;
        border-radius: 10px;
        background: linear-gradient(135deg, #0d3d2a 0%, #0a2540 100%);
        border: 1px solid #1c6b3a44;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.35rem;
        line-height: 1;
    }
    .qb3-title-block {}
    .qb3-logo {
        font-family: 'Syne', sans-serif;
        font-size: 1.15rem;
        font-weight: 800;
        color: #e8f4e8;
        letter-spacing: -0.3px;
        line-height: 1.1;
    }
    .qb3-logo span { color: #c8a93a; }
    .qb3-sub {
        font-size: 0.58rem;
        color: #3a7a50;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 700;
        margin-top: 1px;
    }
    .qb3-badge {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.6rem;
        background: linear-gradient(135deg, #0d3d2a, #0a2540);
        color: #4ecb7a;
        border: 1px solid #2a6b3a55;
        padding: 4px 10px;
        border-radius: 20px;
        letter-spacing: 1px;
        text-transform: uppercase;
        display: flex;
        align-items: center;
        gap: 5px;
    }
    .qb3-badge::before {
        content: '';
        width: 6px; height: 6px;
        border-radius: 50%;
        background: #4ecb7a;
        box-shadow: 0 0 6px #4ecb7a;
        animation: pulse 1.6s infinite;
    }

    /* ── SELECTBOX ────────────────────────────────────── */
    .stSelectbox label {
        font-size: 0.7rem !important;
        color: #3a7a50 !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 700;
    }
    .stSelectbox > div > div {
        background: #0b1f14 !important;
        border: 1px solid #1c4a2a !important;
        border-radius: 10px !important;
        color: #e8f4e8 !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
    }

    /* ── GAP CARD ─────────────────────────────────────── */
    .gap-card {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: linear-gradient(135deg, #0b1f14 0%, #0a1a2e 100%);
        border: 1px solid #1c4a2a;
        border-radius: 12px;
        padding: 0.85rem 1rem;
        margin: 0.6rem 0 1.1rem;
    }
    .gap-label {
        font-size: 0.65rem;
        color: #3a7a50;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 700;
        margin-bottom: 2px;
    }
    .gap-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.6rem;
        font-weight: 700;
        line-height: 1;
    }
    .gap-pos  { color: #4ecb7a; }
    .gap-neg  { color: #ff4d6d; }
    .gap-zero { color: #3a7a50; }
    .gap-dot {
        width: 10px; height: 10px;
        border-radius: 50%;
        margin-left: 8px;
        animation: pulse 1.6s infinite;
    }
    .gap-dot-pos { background: #4ecb7a; box-shadow: 0 0 8px #4ecb7a88; }
    .gap-dot-neg { background: #ff4d6d; box-shadow: 0 0 8px #ff4d6d88; }
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(0.8); }
    }

    /* ── SECTION TITLE ────────────────────────────────── */
    .sec-title {
        font-size: 0.65rem;
        color: #3a7a50;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 700;
        margin: 1.2rem 0 0.55rem;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .sec-title::after {
        content: '';
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, #1c4a2a, transparent);
    }

    /* ── METRIC CARDS ─────────────────────────────────── */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #0b1f14 0%, #0a1a2e 100%) !important;
        border: 1px solid #1c4a2a !important;
        border-radius: 12px !important;
        padding: 0.75rem 0.85rem !important;
        transition: border-color 0.2s;
    }
    [data-testid="stMetric"]:hover { border-color: #c8a93a55 !important; }
    [data-testid="stMetricLabel"] > div {
        font-size: 0.62rem !important;
        color: #3a7a50 !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 700 !important;
    }
    [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 1.45rem !important;
        font-weight: 700 !important;
        color: #c8a93a !important;
    }

    /* ── WARNING / INFO ───────────────────────────────── */
    [data-testid="stAlert"] {
        background: #0b1f14 !important;
        border-radius: 10px !important;
        border-left: 3px solid #1c6b3a !important;
        font-size: 0.85rem !important;
        padding: 0.6rem 0.85rem !important;
        color: #a0c8a8 !important;
    }

    /* ── EXPANDER ─────────────────────────────────────── */
    [data-testid="stExpander"] {
        background: #0b1f14 !important;
        border: 1px solid #1c4a2a !important;
        border-radius: 10px !important;
        overflow: hidden;
    }
    [data-testid="stExpander"] summary {
        font-size: 0.8rem !important;
        color: #5a9a6a !important;
        padding: 0.6rem 0.85rem !important;
    }

    /* ── DATAFRAME ────────────────────────────────────── */
    [data-testid="stDataFrame"] {
        border-radius: 10px !important;
        overflow: hidden;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.75rem !important;
    }

    /* ── BUTTONS ──────────────────────────────────────── */
    .stButton > button {
        width: 100% !important;
        height: 2.8rem !important;
        background: linear-gradient(135deg, #1c6b3a 0%, #0e4a2a 100%) !important;
        color: #e8f4e8 !important;
        font-family: 'Syne', sans-serif !important;
        font-size: 0.82rem !important;
        font-weight: 700 !important;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        border: 1px solid #2a8a4a44 !important;
        border-radius: 10px !important;
        transition: all 0.15s !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #c8a93a 0%, #a08020 100%) !important;
        color: #0b1f14 !important;
        border-color: transparent !important;
    }

    /* ── DATE INPUT ───────────────────────────────────── */
    [data-testid="stDateInput"] label {
        font-size: 0.7rem !important;
        color: #3a7a50 !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }
    [data-testid="stDateInput"] input {
        background: #0b1f14 !important;
        border: 1px solid #1c4a2a !important;
        border-radius: 10px !important;
        color: #e8f4e8 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.9rem !important;
    }

    /* ── DIVIDER ──────────────────────────────────────── */
    hr { border-color: #1c4a2a !important; margin: 1.2rem 0 !important; }

    /* ── BOTTOM SAFE AREA ─────────────────────────────── */
    .bottom-space { height: 2rem; }

    /* ── HIDE STREAMLIT CHROME ────────────────────────── */
    #MainMenu, footer, header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)


# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="qb3-header">
    <div class="qb3-logo-wrap">
        <div class="qb3-icon">🐂</div>
        <div class="qb3-title-block">
            <div class="qb3-logo">Quant<span>B3</span></div>
            <div class="qb3-sub">Scanner · B3</div>
        </div>
    </div>
    <div class="qb3-badge">Live</div>
</div>
""", unsafe_allow_html=True)


# --- 2. FUNÇÕES CORE ---
URL_PLANILHA = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vTn6i6FnZ7awsqEZLkxsIRSFHgRonDnBrK33Jvi-gATeCnUbSgWQp3J0aMzr7VqC_b2hySzKN_LEMxS"
    "/pub?output=csv"
)

@st.cache_data(ttl=600)
def carregar_dados():
    try:
        df = pd.read_csv(URL_PLANILHA)
        df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Ativo', 'Gap', 'Max_A', 'Min_A']
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df.dropna(subset=['Ativo'])
    except:
        return pd.DataFrame()


def obter_gap_hoje(ticker):
    try:
        dados = yf.download(ticker, period="2d", progress=False)
        if len(dados) < 2:
            return 0.0
        dados.columns = [c[0] if isinstance(c, tuple) else c for c in dados.columns]
        return round(((float(dados['Open'].iloc[-1]) / float(dados['Close'].iloc[-2])) - 1) * 100, 2)
    except:
        return 0.0


def calcular_performance(df_ev):
    melhor_y, melhor_x = 0.5, 0.0
    if len(df_ev) >= 3:
        for alvo in [x * 0.1 for x in range(1, 41)]:
            taxa = (len(df_ev[df_ev['Max_A'] >= alvo]) / len(df_ev)) * 100
            if taxa >= 70:
                melhor_y, melhor_x = round(alvo, 2), round(taxa, 1)
        if melhor_x < 70:
            for alvo in [x * -0.1 for x in range(1, 41)]:
                taxa = (len(df_ev[df_ev['Min_A'] <= alvo]) / len(df_ev)) * 100
                if taxa >= 70:
                    melhor_y, melhor_x = round(alvo, 2), round(taxa, 1)
    return melhor_y, melhor_x


# --- 3. INTERFACE PRINCIPAL ---
df_mestre = carregar_dados()

if df_mestre.empty:
    st.error("⚠️ Falha ao carregar dados. Verifique a planilha.")
    st.stop()

lista_ativos = sorted(df_mestre['Ativo'].unique())

# ── 3.1 SELEÇÃO DE ATIVO ───────────────────────────────────────────────────────
st.markdown('<div class="sec-title">Ativo</div>', unsafe_allow_html=True)
ativo_sel = st.selectbox("", lista_ativos, label_visibility="collapsed")

# ── GAP DO DIA ────────────────────────────────────────────────────────────────
g_hoje = obter_gap_hoje(ativo_sel)
gap_class = "gap-pos" if g_hoje > 0 else ("gap-neg" if g_hoje < 0 else "gap-zero")
dot_class  = "gap-dot-pos" if g_hoje >= 0 else "gap-dot-neg"
gap_sign   = "+" if g_hoje > 0 else ""

st.markdown(f"""
<div class="gap-card">
    <div>
        <div class="gap-label">GAP de Hoje</div>
        <div class="gap-value {gap_class}">{gap_sign}{g_hoje}%</div>
    </div>
    <div style="display:flex;align-items:center;">
        <div style="text-align:right;margin-right:8px;">
            <div class="gap-label">Ativo</div>
            <div style="font-weight:700;color:#e8f4ff;font-size:1rem;">{ativo_sel.replace('.SA','')}</div>
        </div>
        <div class="gap-dot {dot_class}"></div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── 3.2 ESTATÍSTICAS ───────────────────────────────────────────────────────────
st.markdown('<div class="sec-title">Estatísticas — 3 anos</div>', unsafe_allow_html=True)

data_ini = datetime.now() - timedelta(days=3 * 365)
df_at = df_mestre[
    (df_mestre['Ativo'] == ativo_sel) &
    (df_mestre['Date'] >= pd.to_datetime(data_ini))
]
ev = df_at[
    (df_at['Gap'] <= g_hoje + 0.15) &
    (df_at['Gap'] >= g_hoje - 0.15)
]

if not ev.empty:
    alvo_f, acerto_f = calcular_performance(ev)
    c1, c2, c3 = st.columns(3)
    c1.metric("Alvo", f"{alvo_f}%")
    c2.metric("Acerto", f"{acerto_f}%")
    c3.metric("Amostras", len(ev))

    with st.expander("📊 Mapa completo de GAPs"):
        mapa = []
        for v in [x * 0.5 for x in range(-6, 7)]:
            df_r = df_at[
                (df_at['Gap'] <= v + 0.2) &
                (df_at['Gap'] >= v - 0.2)
            ]
            if len(df_r) >= 3:
                yr, xr = calcular_performance(df_r)
                mapa.append({
                    "GAP": f"{v:+.1f}%",
                    "N": len(df_r),
                    "Alvo": f"{yr}%",
                    "Acerto": f"{xr}%"
                })
        if mapa:
            st.dataframe(
                pd.DataFrame(mapa),
                use_container_width=True,
                hide_index=True
            )
else:
    st.warning("Sem histórico suficiente para este GAP.")

# ── 3.3 CONFERIR DATA ──────────────────────────────────────────────────────────
st.markdown('<div class="sec-title">Conferir Data</div>', unsafe_allow_html=True)

with st.form("form_data"):
    data_sel = st.date_input("Selecione o dia:", datetime.now())
    btn_data = st.form_submit_button("Consultar Data")

    if btn_data:
        res = df_mestre[
            (df_mestre['Ativo'] == ativo_sel) &
            (df_mestre['Date'].dt.date == data_sel)
        ]
        if not res.empty:
            df_prev = df_mestre[
                (df_mestre['Ativo'] == ativo_sel) &
                (df_mestre['Date'] < pd.to_datetime(data_sel))
            ]
            alvo_p, _ = calcular_performance(df_prev)
            max_r  = res['Max_A'].iloc[0]
            min_r  = res['Min_A'].iloc[0]
            ganhou = (alvo_p > 0 and max_r >= alvo_p) or (alvo_p < 0 and min_r <= alvo_p)

            cor     = "#00d4aa" if ganhou else "#ff4d6d"
            emoji   = "✅" if ganhou else "❌"
            label   = "GAIN" if ganhou else "LOSS"
            gap_dia = res['Gap'].iloc[0]

            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#0b1f14,#0a1a2e);border:1px solid {cor}44;border-left:3px solid {cor};
                        border-radius:10px;padding:0.75rem 1rem;margin-top:0.5rem;">
                <div style="font-size:0.65rem;color:#3a7a50;text-transform:uppercase;
                            letter-spacing:1.5px;font-weight:700;margin-bottom:6px;">Resultado</div>
                <div style="font-size:1.3rem;font-weight:800;color:{cor};">{emoji} {label}</div>
                <div style="margin-top:6px;display:flex;gap:1rem;font-size:0.78rem;color:#5a9a6a;">
                    <span>GAP <b style="color:#e8f4e8;">{gap_dia:+.2f}%</b></span>
                    <span>Alvo <b style="color:#c8a93a;">{alvo_p}%</b></span>
                    <span>Max <b style="color:#e8f4e8;">{max_r:.2f}%</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Data não encontrada na base.")

# ── 3.4 RADAR ─────────────────────────────────────────────────────────────────
st.markdown('<div class="sec-title">Radar de Mercado</div>', unsafe_allow_html=True)

if st.button("🚀  Escanear Todo o Mercado"):
    radar_list = []
    prog = st.progress(0, text="Escaneando ativos…")
    status = st.empty()

    for i, tk in enumerate(lista_ativos):
        status.caption(f"Analisando {tk.replace('.SA','')}…")
        gt = obter_gap_hoje(tk)
        df_h = df_mestre[
            (df_mestre['Ativo'] == tk) &
            (df_mestre['Gap'] <= gt + 0.15) &
            (df_mestre['Gap'] >= gt - 0.15)
        ]
        if len(df_h) >= 5:
            alvo, acerto = calcular_performance(df_h)
            if acerto >= 80:
                radar_list.append({
                    "Ativo": tk.replace('.SA', ''),
                    "Dir":   "🟢 LONG" if alvo > 0 else "🔴 SHORT",
                    "Alvo":  f"{alvo:+.1f}%",
                    "Acerto": f"{acerto:.0f}%",
                    "GAP":   f"{gt:+.2f}%",
                })
        prog.progress((i + 1) / len(lista_ativos))

    status.empty()
    prog.empty()

    if radar_list:
        df_radar = (
            pd.DataFrame(radar_list)
            .sort_values("Acerto", ascending=False)
            .reset_index(drop=True)
        )
        st.dataframe(df_radar, use_container_width=True, hide_index=True)
        st.caption(f"✅ {len(radar_list)} ativo(s) com acerto ≥ 80%")
    else:
        st.info("Nenhum ativo com acerto ≥ 80% no momento.")

st.markdown('<div class="bottom-space"></div>', unsafe_allow_html=True)
