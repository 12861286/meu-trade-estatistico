import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime
import time

# Configuração Original
st.set_page_config(page_title="Scanner Quant B3", layout="wide")
st.title("🔍 Scanner de Estatística: Compra e Venda")

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSg04Li1XStwno4T5cQxMuUwDS35uzY2eRoLPi8zUIpxadZpBPTGMbd_IyftA-rbjpuc6_5TQfi0hXv/pub?output=csv"

@st.cache_data(ttl=3600)
def carregar_dados():
    df = pd.read_csv(URL_PLANILHA)
    df['Date'] = pd.to_datetime(df['Date'])
    for col in ['Open', 'High', 'Low', 'Close', 'Gap', 'Max_A', 'Min_A']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df.dropna()

def obter_gap_hoje(ticker):
    try:
        d = yf.download(ticker, period="2d", progress=False)
        d.columns = [c[0] if isinstance(c, tuple) else c for c in d.columns]
        return round(((d['Open'].iloc[-1] / d['Close'].iloc[-2]) - 1) * 100, 2)
    except: return 0.0

df_mestre = carregar_dados()

if not df_mestre.empty:
    lista_ativos = sorted(df_mestre['Ativo'].unique())
    
    # --- INTERFACE ORIGINAL ---
    st.subheader("Configurações do Backtest")
    ativo = st.selectbox("Selecione a ação:", lista_ativos)
    
    gap_atual = obter_gap_hoje(ativo)
    cor = "#d4edda" if gap_atual >= 0 else "#f8d7da"
    st.markdown(f'<div style="background-color:{cor}; padding:10px; border-radius:10px; text-align:center; color: black; margin-bottom: 20px;"><b>GAP HOJE: {gap_atual}%</b></div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1: data_ini = st.date_input("Início:", datetime(2020, 1, 1))
    with c2: gap_desejado = st.number_input("GAP alvo (%):", value=gap_atual, step=0.1)
    with c3: filtro_min = st.number_input("Min. Acerto Radar (%):", value=80)

    if st.button('🚀 Rodar Estatística e Radar Completo', use_container_width=True):
        # 1. Estatística do Ativo
        df_a = df_mestre[(df_mestre['Ativo'] == ativo) & (df_mestre['Date'] >= pd.to_datetime(data_ini))]
        ev = df_a[(df_a['Gap'] <= gap_desejado + 0.15) & (df_a['Gap'] >= gap_desejado - 0.15)]
        
        if not ev.empty:
            st.success(f"### Histórico de {ativo} para GAP {gap_desejado}%")
            # Cálculo de Compra e Venda
            buy_acc = (len(ev[ev['Max_A'] >= 0.5]) / len(ev)) * 100
            sell_acc = (len(ev[ev['Min_A'] <= -0.5]) / len(ev)) * 100
            
            res1, res2 = st.columns(2)
            res1.metric("Chance de SUBIR (+0.5%)", f"{round(buy_acc,1)}%")
            res2.metric("Chance de CAIR (-0.5%)", f"{round(sell_acc,1)}%")

        # 2. RADAR POR ABAS (O QUE VOCÊ PEDIU)
        st.markdown("---")
        st.subheader("🚀 Radar Quantitativo (Compra e Venda)")
        
        # Aqui criamos as abas de porcentagem
        abas = st.tabs(["65%", "75%", "85%", "95%", "100%"])
        
        radar_data = []
        with st.spinner("Analisando ativos..."):
            for t in lista_ativos[:30]: # Limite para não travar
                g = obter_gap_hoje(t)
                hist = df_mestre[df_mestre['Ativo'] == t]
                sim = hist[(hist['Gap'] <= g + 0.15) & (hist['Gap'] >= g - 0.15)]
                
                if len(sim) >= 5:
                    acc_buy = (len(sim[sim['Max_A'] >= 0.5]) / len(sim)) * 100
                    acc_sell = (len(sim[sim['Min_A'] <= -0.5]) / len(sim)) * 100
                    
                    # Decide qual lado é mais forte
                    if acc_buy >= acc_sell:
                        radar_data.append({"Ativo": t, "GAP": g, "Lado": "🟢 COMPRA", "Acerto": acc_buy})
                    else:
                        radar_data.append({"Ativo": t, "GAP": g, "Lado": "🔴 VENDA", "Acerto": acc_sell})

        df_radar = pd.DataFrame(radar_data)
        for i, nivel in enumerate([65, 75, 85, 95, 100]):
            with abas[i]:
                filtrado = df_radar[df_radar['Acerto'] >= nivel]
                if not filtrado.empty:
                    st.table(filtrado.sort_values('Acerto', ascending=False))
                else:
                    st.write("Nenhuma oportunidade neste nível.")
