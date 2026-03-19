import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. Configuração de layout original
st.set_page_config(page_title="Scanner Quant B3", layout="wide")
st.title("🔍 Scanner de Estatística: Compra e Venda")

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSg04Li1XStwno4T5cQxMuUwDS35uzY2eRoLPi8zUIpxadZpBPTGMbd_IyftA-rbjpuc6_5TQfi0hXv/pub?output=csv"

@st.cache_data(ttl=600) # Cache mais curto para destravar
def carregar_dados():
    try:
        # Lendo a planilha forçando as colunas como texto para limpar antes de converter
        df = pd.read_csv(URL_PLANILHA, dtype=str)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        colunas_num = ['Open', 'High', 'Low', 'Close', 'Gap', 'Max_A', 'Min_A']
        for col in colunas_num:
            if col in df.columns:
                # Limpeza ultra-rápida: remove pontos e converte
                df[col] = df[col].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df.dropna(subset=['Ativo', 'Open'])
    except Exception as e:
        st.error(f"Erro ao carregar: {e}")
        return pd.DataFrame()

def obter_gap_hoje(ticker):
    try:
        d = yf.download(ticker, period="2d", progress=False, timeout=10)
        if d.empty: return 0.0
        d.columns = [c[0] if isinstance(c, tuple) else c for c in d.columns]
        return round(((d['Open'].iloc[-1] / d['Close'].iloc[-2]) - 1) * 100, 2)
    except: return 0.0

# Execução
df_mestre = carregar_dados()

if not df_mestre.empty:
    lista_ativos = sorted(df_mestre['Ativo'].unique())
    
    st.subheader("Configurações do Backtest")
    ativo = st.selectbox("Selecione a ação:", lista_ativos)
    
    gap_atual = obter_gap_hoje(ativo)
    cor = "#d4edda" if gap_atual >= 0 else "#f8d7da"
    st.markdown(f'<div style="background-color:{cor}; padding:15px; border-radius:10px; text-align:center; color: black;"><b>GAP HOJE EM {ativo}: {gap_atual}%</b></div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1: data_ini = st.date_input("Início:", datetime(2020, 1, 1))
    with col2: gap_alvo = st.number_input("GAP alvo (%):", value=gap_atual, step=0.1)
    with col3: min_acc = st.number_input("Mín. Acerto (%):", value=80)

    if st.button('🚀 Rodar Estatística e Radar', use_container_width=True):
        # Estatística do Ativo Selecionado
        df_a = df_mestre[(df_mestre['Ativo'] == ativo) & (df_mestre['Date'] >= pd.to_datetime(data_ini))]
        ev = df_a[(df_a['Gap'] <= gap_alvo + 0.15) & (df_a['Gap'] >= gap_alvo - 0.15)]
        
        if not ev.empty:
            st.success(f"### Resultados para {ativo}")
            c1, c2, c3 = st.columns(3)
            c1.metric("Ocorrências", len(ev))
            c2.metric("Compra (+0.5%)", f"{round((len(ev[ev['Max_A'] >= 0.5])/len(ev))*100, 1)}%")
            c3.metric("Venda (-0.5%)", f"{round((len(ev[ev['Min_A'] <= -0.5])/len(ev))*100, 1)}%")

        # Radar Simples e Rápido
        st.markdown("---")
        st.subheader("🚀 Radar de Elite")
        abas = st.tabs(["65%", "85%", "100%"])
        
        radar_lista = []
        # Analisa apenas os top 20 para destravar o site agora
        for t in lista_ativos[:20]:
            g = obter_gap_hoje(t)
            sim = df_mestre[(df_mestre['Ativo'] == t) & (df_mestre['Gap'] <= g + 0.15) & (df_mestre['Gap'] >= g - 0.15)]
            if len(sim) >= 5:
                acc_c = (len(sim[sim['Max_A'] >= 0.5]) / len(sim)) * 100
                acc_v = (len(sim[sim['Min_A'] <= -0.5]) / len(sim)) * 100
                if acc_c >= 65 or acc_v >= 65:
                    lado = "🟢 COMPRA" if acc_c >= acc_v else "🔴 VENDA"
                    perc = max(acc_c, acc_v)
                    radar_lista.append({"Ativo": t, "GAP": f"{g}%", "Lado": lado, "Acerto": perc})
        
        df_radar = pd.DataFrame(radar_lista)
        if not df_radar.empty:
            for i, n in enumerate([65, 85, 100]):
                with abas[i]:
                    st.table(df_radar[df_radar['Acerto'] >= n])

        fig = px.bar(df_a.tail(50), x='Date', y=['Max_A', 'Min_A'], barmode='group')
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Aguardando carregamento da planilha... Se demorar, verifique se a planilha Google está 'Publicada na Web' como CSV.")
