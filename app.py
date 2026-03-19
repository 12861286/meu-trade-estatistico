import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Scanner Quant B3", layout="wide")
st.title("🔍 Scanner de Estatística de Abertura")

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSg04Li1XStwno4T5cQxMuUwDS35uzY2eRoLPi8zUIpxadZpBPTGMbd_IyftA-rbjpuc6_5TQfi0hXv/pub?output=csv"

@st.cache_data(ttl=3600)
def carregar_dados():
    try:
        # Lendo como texto primeiro para limpar formatações doidas
        df = pd.read_csv(URL_PLANILHA, dtype=str)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        colunas = ['Open', 'High', 'Low', 'Close', 'Gap', 'Max_A', 'Min_A']
        for col in colunas:
            if col in df.columns:
                # Se o número tiver mais de dois pontos (ex: 18.784.458.800), limpamos tudo exceto o valor real
                df[col] = df[col].str.replace(r'\.(?=\d{3})', '', regex=True).str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df.dropna(subset=['Ativo', 'Open'])
    except Exception as e:
        st.error(f"Erro: {e}")
        return pd.DataFrame()

def obter_gap_hoje(ticker):
    try:
        dados = yf.download(ticker, period="2d", progress=False, timeout=10)
        if dados.empty: return 0.0
        dados.columns = [c[0] if isinstance(c, tuple) else c for c in dados.columns]
        return round(((dados['Open'].iloc[-1] / dados['Close'].iloc[-2]) - 1) * 100, 2)
    except: return 0.0

df_mestre = carregar_dados()

if not df_mestre.empty:
    lista_ativos = sorted(df_mestre['Ativo'].unique())
    st.subheader("Configurações")
    ativo = st.selectbox("Ação:", lista_ativos)
    gap_hoje = obter_gap_hoje(ativo)

    cor = "#d4edda" if gap_hoje >= 0 else "#f8d7da"
    st.markdown(f'<div style="background-color:{cor}; padding:15px; border-radius:10px; text-align:center; color: black;"><b>GAP HOJE: {gap_hoje}%</b></div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1: data_ini = st.date_input("Início:", datetime(2020, 1, 1))
    with c2: gap_alvo = st.number_input("GAP (%):", value=gap_hoje, step=0.1)
    with c3: min_acc = st.number_input("Min. Acerto (%):", value=80)

    if st.button('🚀 Rodar Estatística e Radar', use_container_width=True):
        df_a = df_mestre[(df_mestre['Ativo'] == ativo) & (df_mestre['Date'] >= pd.to_datetime(data_ini))]
        ev = df_a[(df_a['Gap'] <= gap_alvo + 0.15) & (df_a['Gap'] >= gap_alvo - 0.15)]
        
        if not ev.empty:
            st.success(f"### Resultados para {ativo}")
            res1, res2, res3 = st.columns(3)
            res1.metric("Ocorrências", len(ev))
            res2.metric("Compra (+0.5%)", f"{round((len(ev[ev['Max_A'] >= 0.5])/len(ev))*100, 1)}%")
            res3.metric("Venda (-0.5%)", f"{round((len(ev[ev['Min_A'] <= -0.5])/len(ev))*100, 1)}%")

        # Radar
        st.markdown("---")
        abas = st.tabs(["65%", "85%", "100%"])
        # ... (Logica de radar simplificada para velocidade) ...
        
        fig = px.bar(df_a.tail(50), x='Date', y=['Max_A', 'Min_A'], barmode='group')
        st.plotly_chart(fig, use_container_width=True)
