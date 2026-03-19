import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURAÇÃO DE TEMA E LAYOUT ---
st.set_page_config(page_title="Scanner Quant B3", layout="wide", initial_sidebar_state="collapsed")

# CSS para deixar o visual "Pro" (Dark Mode e Cards)
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { color: #00ffcc; font-size: 24px; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #262730; color: white; border: 1px solid #4x4x4x; }
    .stButton>button:hover { border: 1px solid #00ffcc; color: #00ffcc; }
    [data-testid="stMetric"] { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNÇÕES CORE ---
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTn6i6FnZ7awsqEZLkxsIRSFHgRonDnBrK33Jvi-gATeCnUbSgWQp3J0aMzr7VqC_b2hySzKN_LEMxS/pub?output=csv"

@st.cache_data(ttl=600)
def carregar_dados():
    try:
        df = pd.read_csv(URL_PLANILHA)
        df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Ativo', 'Gap', 'Max_A', 'Min_A']
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Fech_Apos_Abertura'] = ((df['Close'] / df['Open']) - 1) * 100
        return df.dropna(subset=['Ativo'])
    except: return pd.DataFrame()

def obter_gap_hoje(ticker):
    try:
        dados = yf.download(ticker, period="2d", progress=False)
        if len(dados) < 2: return 0.0
        dados.columns = [c[0] if isinstance(c, tuple) else c for c in dados.columns]
        return round(((float(dados['Open'].iloc[-1]) / float(dados['Close'].iloc[-2])) - 1) * 100, 2)
    except: return 0.0

def calcular_performance(df_ev):
    melhor_y, melhor_x = 0.5, 0.0
    if len(df_ev) >= 3:
        for alvo in [x * 0.1 for x in range(1, 41)]:
            taxa = (len(df_ev[df_ev['Max_A'] >= alvo]) / len(df_ev)) * 100
            if taxa >= 70: melhor_y, melhor_x = round(alvo, 2), round(taxa, 1)
        if melhor_x < 70:
            for alvo in [x * -0.1 for x in range(1, 41)]:
                taxa = (len(df_ev[df_ev['Min_A'] <= alvo]) / len(df_ev)) * 100
                if taxa >= 70: melhor_y, melhor_x = round(alvo, 2), round(taxa, 1)
    return melhor_y, melhor_x

# --- 3. INICIALIZAÇÃO E BARRA LATERAL ---
df_mestre = carregar_dados()
if not df_mestre.empty:
    lista_ativos = sorted(df_mestre['Ativo'].unique())
    
    with st.sidebar:
        st.header("⚙️ Filtros Globais")
        ativo_global = st.selectbox("Ativo Principal:", lista_ativos)
        data_ini_global = st.date_input("Início do Backtest:", datetime.now() - timedelta(days=3*365))
        min_acerto_radar = st.slider("Mínimo Acerto Radar (%)", 50, 95, 80)
        gap_atual_ref = obter_gap_hoje(ativo_global)
        st.metric(f"GAP Hoje {ativo_global}", f"{gap_atual_ref}%")

    # --- 4. NAVEGAÇÃO POR ABAS (SISTEMA PROFISSIONAL) ---
    tab1, tab2, tab3 = st.tabs(["🚀 RADAR DO DIA", "📊 BACKTEST DETALHADO", "🔍 CONFERIR DATA"])

    # --- ABA 1: RADAR DE ELITE ---
    with tab1:
        st.subheader("Melhores Oportunidades para Hoje")
        if st.button("Escanear Mercado Agora"):
            radar_data = []
            barra = st.progress(0)
            for i, tk in enumerate(lista_ativos):
                g_hoje = obter_gap_hoje(tk)
                df_h = df_mestre[(df_mestre['Ativo'] == tk) & (df_mestre['Gap'] <= g_hoje + 0.15) & (df_mestre['Gap'] >= g_hoje - 0.15)]
                if len(df_h) >= 5:
                    alvo, acerto = calcular_performance(df_h)
                    if acerto >= min_acerto_radar:
                        radar_data.append({"Ativo": tk, "GAP Hoje": f"{g_hoje}%", "Sinal": "COMPRA 🟢" if alvo > 0 else "VENDA 🔴", "Alvo": f"{alvo}%", "Acerto": f"{acerto}%"})
                barra.progress((i + 1) / len(lista_ativos))
            
            if radar_data:
                st.dataframe(pd.DataFrame(radar_data).sort_values("Acerto", ascending=False), use_container_width=True)
            else:
                st.info("Nenhuma oportunidade de alta probabilidade encontrada.")

    # --- ABA 2: BACKTEST DETALHADO ---
    with tab2:
        st.subheader(f"Estatística de GAP: {ativo_global}")
        gap_analise = st.number_input("GAP para simulação:", value=gap_atual_ref, step=0.1)
        
        df_hist = df_mestre[(df_mestre['Ativo'] == ativo_global) & (df_mestre['Date'] >= pd.to_datetime(data_ini_global))]
        ev_esp = df_hist[(df_hist['Gap'] <= gap_analise + 0.15) & (df_hist['Gap'] >= gap_analise - 0.15)]
        
        if not ev_esp.empty:
            total = len(ev_esp)
            pos = len(ev_esp[ev_esp['Max_A'] > 0])
            alvo_f, acerto_f = calcular_performance(ev_esp)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Amostra", f"{total} dias")
            c2.metric("Nível Alvo", f"{alvo_f}%")
            c3.metric("Assertividade", f"{acerto_n}%" if 'acerto_n' in locals() else f"{acerto_f}%")
            c4.metric("Freq. Positiva", f"{(pos/total)*100:.1f}%")

            st.markdown("---")
            st.write("### Mapa de GAPs do Ativo")
            ranking = []
            for val in [x * 0.5 for x in range(-10, 11)]:
                t_gap = round(val, 2)
                ev_r = df_hist[(df_hist['Gap'] <= t_gap + 0.2) & (df_hist['Gap'] >= t_gap - 0.2)]
                if len(ev_r) >= 3:
                    yr, xr = calcular_performance(ev_r)
                    ranking.append({"GAP": f"{t_gap}%", "Dias": len(ev_r), "Alvo": f"{yr}%", "Acerto": f"{xr}%"})
            st.table(pd.DataFrame(ranking).sort_values("GAP", ascending=False))

    # --- ABA 3: CONFERIR DATA ---
    with tab3:
        st.subheader("Histórico de Execução")
        col_d1, col_d2 = st.columns([2,1])
        with col_d1:
            data_sel = st.date_input("Data do Pregão:", datetime.now())
        with col_d2:
            verificar = st.button("Consultar Resultado")
        
        if verificar:
            res = df_mestre[(df_mestre['Ativo'] == ativo_global) & (df_mestre['Date'].dt.date == data_sel)]
            if not res.empty:
                # Busca alvo estatístico antes desse dia
                df_prev = df_mestre[(df_mestre['Ativo'] == ativo_global) & (df_mestre['Date'] < pd.to_datetime(data_sel))]
                alvo_p, _ = calcular_performance(df_prev)
                max_r = res['Max_A'].iloc[0]
                min_r = res['Min_A'].iloc[0]
                ganhou = (alvo_p > 0 and max_r >= alvo_p) or (alvo_p < 0 and min_r <= alvo_p)
                
                st.markdown(f"### {'✅ GAIN' if ganhou else '❌ LOSS'}")
                v1, v2, v3 = st.columns(3)
                v1.metric("GAP Abertura", f"{res['Gap'].iloc[0]}%")
                v2.metric("Objetivo na Época", f"{alvo_p}%")
                v3.metric("Máxima Real", f"{max_r}%")
            else:
                st.warning("Sem dados para esta data.")
else:
    st.error("Erro crítico ao carregar banco de dados.")
