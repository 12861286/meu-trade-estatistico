import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuração visual (SEU PADRÃO ORIGINAL)
st.set_page_config(page_title="Scanner Quant B3", layout="wide")
st.title("🔍 Scanner de Estatística de Abertura")

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSg04Li1XStwno4T5cQxMuUwDS35uzY2eRoLPi8zUIpxadZpBPTGMbd_IyftA-rbjpuc6_5TQfi0hXv/pub?output=csv"

@st.cache_data(ttl=3600)
def carregar_dados():
    try:
        # Lê a planilha tratando o ponto como separador de milhar para limpar a bagunça
        df = pd.read_csv(URL_PLANILHA, thousands='.')
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        # Garante que as colunas sejam números reais
        colunas = ['Open', 'High', 'Low', 'Close', 'Gap', 'Max_A', 'Min_A']
        for col in colunas:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df.dropna(subset=['Ativo', 'Open'])
    except Exception as e:
        st.error(f"Erro ao ler planilha: {e}")
        return pd.DataFrame()

def obter_gap_hoje(ticker):
    try:
        d = yf.download(ticker, period="2d", progress=False, timeout=10)
        if d.empty: return 0.0
        d.columns = [c[0] if isinstance(c, tuple) else c for c in d.columns]
        return round(((d['Open'].iloc[-1] / d['Close'].iloc[-2]) - 1) * 100, 2)
    except: return 0.0

# --- INTERFACE ---
df_mestre = carregar_dados()

if not df_mestre.empty:
    lista_ativos = sorted(df_mestre['Ativo'].unique())
    st.subheader("Configurações do Backtest")
    ativo = st.selectbox("Selecione a ação:", lista_ativos)
    
    gap_hoje = obter_gap_hoje(ativo)
    cor = "#d4edda" if gap_hoje >= 0 else "#f8d7da"
    st.markdown(f'<div style="background-color:{cor}; padding:15px; border-radius:10px; text-align:center; color: black; border: 1px solid #ccc;"><b>GAP HOJE EM {ativo}: {gap_hoje}%</b></div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1: data_ini = st.date_input("Início:", datetime(2020, 1, 1))
    with c2: gap_alvo = st.number_input("GAP desejado (%):", value=gap_hoje, step=0.1)
    with c3: min_acc = st.number_input("Mínimo de Acerto Radar (%):", value=80)

    if st.button('🚀 Rodar Estatística e Radar', use_container_width=True):
        # Estatística detalhada
        df_a = df_mestre[(df_mestre['Ativo'] == ativo) & (df_mestre['Date'] >= pd.to_datetime(data_ini))]
        ev = df_a[(df_a['Gap'] <= gap_alvo + 0.15) & (df_a['Gap'] >= gap_alvo - 0.15)]
        
        if not ev.empty:
            st.success(f"### Resultados Históricos para {ativo}")
            res1, res2, res3 = st.columns(3)
            res1.metric("Ocorrências", len(ev))
            res2.metric("Acerto Compra (+0.5%)", f"{round((len(ev[ev['Max_A'] >= 0.5])/len(ev))*100, 1)}%")
            res3.metric("Acerto Venda (-0.5%)", f"{round((len(ev[ev['Min_A'] <= -0.5])/len(ev))*100, 1)}%")

        # Radar com abas originais
        st.markdown("---")
        st.subheader("🚀 Radar de Elite")
        abas = st.tabs(["65%", "85%", "100%"])
        
        radar_lista = []
        for t in lista_ativos[:30]:
            g = obter_gap_hoje(t)
            sim = df_mestre[(df_mestre['Ativo'] == t) & (df_mestre['Gap'] <= g + 0.15) & (df_mestre['Gap'] >= g - 0.15)]
            if len(sim) >= 5:
                ac_c = (len(sim[sim['Max_A'] >= 0.5]) / len(sim)) * 100
                ac_v = (len(sim[sim['Min_A'] <= -0.5]) / len(sim)) * 100
                if ac_c >= 65 or ac_v >= 65:
                    radar_lista.append({"Ativo": t, "GAP": f"{g}%", "Lado": "🟢 COMPRA" if ac_c >= ac_v else "🔴 VENDA", "Acerto": max(ac_c, ac_v)})
        
        df_radar = pd.DataFrame(radar_lista)
        if not df_radar.empty:
            for i, n in enumerate([65, 85, 100]):
                with abas[i]:
                    st.table(df_radar[df_radar['Acerto'] >= n].sort_values('Acerto', ascending=False))

        # Gráfico original
        fig = px.bar(df_a.tail(50), x='Date', y=['Max_A', 'Min_A'], barmode='group')
        st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Planilha vazia ou com erro. Limpe as colunas B até I no Google Sheets e cole os novos dados.")
