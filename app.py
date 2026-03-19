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


LOGO_B64 = "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"

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="qb3-header">
    <div class="qb3-logo-wrap">
        <img src="data:image/jpeg;base64,{LOGO_B64}"
             style="width:42px;height:42px;border-radius:10px;object-fit:cover;
                    border:1px solid #1c6b3a44;flex-shrink:0;">
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
