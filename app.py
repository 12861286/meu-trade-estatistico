import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# --- 1. CONFIGURAÇÃO MOBILE-FIRST E VISUAL ---
st.set_page_config(page_title="Quant B3 Mobile", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #fafafa; font-family: 'Inter', sans-serif; }
    .app-header { text-align: center; padding: 0.5rem 0; border-bottom: 1px solid #30363d; margin-bottom: 1rem; }
    .app-title { font-size: 1.2rem; margin: 0; color: #fafafa; }
    [data-testid="stMetric"] { background-color: #0e1117; padding: 0.5rem; text-align: center; border: none; }
    div[data-testid="stMetricValue"] { color: #00ffcc; font-size: 1.5rem; }
    .stButton>button { width: 100% !important; height: 3rem; background-color: #1f6feb; color: white; font-weight: 600; border: none; border-radius: 4px; }
    div.stSuccess, div.stWarning, div.stInfo { background-color: #161b22 !important; color: #fafafa !important; border: 1px solid #30363d !important; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="app-header"><h1 class="app-title">🔍 Quant B3 Mobile</h1></div>', unsafe_allow_html=True)

# --- 2. FUNÇÕES CORE CORRIGIDAS ---
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
    melhor_y, melhor_x = 0.5, 0.0 # CORRIGIDO: Removido o 'mejor_x' que causava erro
    if len(df_ev) >= 3:
        for alvo in [x * 0.1 for x in range(1, 41)]:
            taxa = (len(df_ev[df_ev['Max_A'] >= alvo]) / len(df_ev)) * 100
            if taxa >= 70: melhor_y, melhor_x = round(alvo, 2), round(taxa, 1)
        if melhor_x < 70:
            for alvo in [x * -0.1 for x in range(1, 41)]:
                taxa = (len(df_ev[df_ev['Min_A'] <= alvo]) / len(df_ev)) * 100
                if taxa >= 70: melhor_y, melhor_x = round(alvo, 2), round(taxa, 1)
    return melhor_y, melhor_x

# --- 3. INTERFACE ---
df_mestre = carregar_dados()
if not df_mestre.empty:
    lista_ativos = sorted(df_mestre['Ativo'].unique())
    ativo_principal = st.selectbox("Selecione o ativo:", lista_ativos)
    
    gap_atual_ativo = obter_gap_hoje(ativo_principal)
    st.markdown(f'<div class="stInfo"><b>GAP hoje: {gap_atual_ativo}%</b></div>', unsafe_allow_html=True)

    with st.expander("⚙️ Configurações"):
        data_ini = st.date_input("Início Backtest:", datetime.now() - timedelta(days=3*365))
        min_acerto_r = st.number_input("Mínimo Acerto Radar (%)", 50, 95, 80)

    # --- SEÇÃO: CONFERIR DATA (FORA DO BOTÃO RODAR) ---
    st.markdown("---")
    st.subheader("📅 Conferir Data")
    with st.form("form_data"):
        c1, c2 = st.columns([1.5, 1])
        with c1:
            data_sel = st.date_input("Dia do Pregão:", datetime.now())
        with c2:
            st.write("") # Espaçador
            st.write("") 
            verificar_data = st.form_submit_button("Consultar")
        
        if verificar_data:
            res = df_mestre[(df_mestre['Ativo'] == ativo_principal) & (df_mestre['Date'].dt.date == data_sel)]
            if not res.empty:
                df_prev = df_mestre[(df_mestre['Ativo'] == ativo_principal) & (df_mestre['Date'] < pd.to_datetime(data_sel))]
                alvo_p, acerto_p = calcular_performance(df_prev)
                max_r, min_r = res['Max_A'].iloc[0], res['Min_A'].iloc[0]
                ganhou = (alvo_p > 0 and max_r >= alvo_p) or (alvo_p < 0 and min_r <= alvo_p)
                
                if ganhou: st.success(f"✅ OBJETIVO ATINGIDO ({alvo_p}%)")
                else: st.warning(f"❌ NÃO ATINGIU ({alvo_p}%)")
                
                m1, m2 = st.columns(2)
                m1.metric("Máxima", f"{max_r}%")
                m2.metric("Mínima", f"{min_r}%")
            else:
                st.error("Dados não encontrados.")

    # --- SEÇÃO: RODAR TUDO ---
    st.markdown("---")
    if st.button("🚀 Rodar Radar e Estatística"):
        # Radar
        st.subheader("🚀 Radar do Dia")
        radar_list = []
        barra = st.progress(0)
        for i, tk in enumerate(lista_ativos):
            g = obter_gap_hoje(tk)
            df_h = df_mestre[(df_mestre['Ativo'] == tk) & (df_mestre['Date'] >= pd.to_datetime(data_ini)) & (df_mestre['Gap'] <= g + 0.15) & (df_mestre['Gap'] >= g - 0.15)]
            if len(df_h) >= 5:
                alvo, acerto = calcular_performance(df_h)
                if acerto >= min_acerto_r:
                    radar_list.append({"Ativo": tk, "Sinal": "🟢 COMPRA" if alvo > 0 else "🔴 VENDA", "Alvo": f"{alvo}%", "Acerto": f"{acerto}%"})
            barra.progress((i + 1) / len(lista_ativos))
        
        if radar_list:
            st.dataframe(pd.DataFrame(radar_list).sort_values("Acerto", ascending=False), use_container_width=True, hide_index=True)
        
        # Backtest
        st.subheader(f"📊 Backtest: {ativo_principal}")
        df_at = df_mestre[(df_mestre['Ativo'] == ativo_principal) & (df_mestre['Date'] >= pd.to_datetime(data_ini))]
        ev = df_at[(df_at['Gap'] <= gap_atual_ativo + 0.15) & (df_at['Gap'] >= gap_atual_ativo - 0.15)]
        
        if not ev.empty:
            alvo_f, acerto_f = calcular_performance(ev)
            b1, b2 = st.columns(2)
            b1.metric("Alvo", f"{alvo_f}%")
            b2.metric("Acerto", f"{acerto_f}%")
            
            st.write("**📋 Mapa de GAPs Histórico**")
            mapa = []
            for v in [x * 0.5 for x in range(-6, 7)]:
                df_r = df_at[(df_at['Gap'] <= v + 0.2) & (df_at['Gap'] >= v - 0.2)]
                if len(df_r) >= 3:
                    yr, xr = calcular_performance(df_r)
                    mapa.append({"GAP": f"{v}%", "Dias": len(df_r), "Alvo": f"{yr}%", "Acerto": f"{xr}%"})
            st.dataframe(pd.DataFrame(mapa), use_container_width=True, hide_index=True)
