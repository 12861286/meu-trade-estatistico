import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. Configuração de layout (SEU VISUAL ORIGINAL)
st.set_page_config(page_title="Scanner Quant B3", layout="wide")
st.title("🔍 Scanner de Estatística: Compra e Venda")

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSg04Li1XStwno4T5cQxMuUwDS35uzY2eRoLPi8zUIpxadZpBPTGMbd_IyftA-rbjpuc6_5TQfi0hXv/pub?output=csv"

@st.cache_data(ttl=600)
def carregar_dados():
    try:
        # Lê a planilha
        df = pd.read_csv(URL_PLANILHA)
        
        # TRATAMENTO DE ERRO: Se os dados vierem grudados por vírgula em uma coluna só
        if len(df.columns) == 1:
            col_name = df.columns[0]
            df = df[col_name].str.split(',', expand=True)
            # Define os nomes das colunas manualmente para não ter erro
            df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Ativo', 'Gap', 'Max_A', 'Min_A']

        # Converte a data
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        # Converte números (limpando pontos de milhar se existirem)
        cols_num = ['Open', 'High', 'Low', 'Close', 'Gap', 'Max_A', 'Min_A']
        for col in cols_num:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df.dropna(subset=['Ativo', 'Open'])
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

def obter_gap_hoje(ticker):
    try:
        d = yf.download(ticker, period="2d", progress=False, timeout=10)
        if d.empty: return 0.0
        d.columns = [c[0] if isinstance(c, tuple) else c for c in d.columns]
        fechamento_ontem = float(d['Close'].iloc[-2])
        abertura_hoje = float(d['Open'].iloc[-1])
        return round(((abertura_hoje / fechamento_ontem) - 1) * 100, 2)
    except:
        return 0.0

# --- LÓGICA DO APP ---
df_mestre = carregar_dados()

if not df_mestre.empty:
    lista_ativos = sorted(df_mestre['Ativo'].unique())
    
    st.subheader("Configurações do Backtest")
    ativo = st.selectbox("Selecione a ação:", lista_ativos)
    
    gap_hoje = obter_gap_hoje(ativo)
    cor = "#d4edda" if gap_hoje >= 0 else "#f8d7da"
    st.markdown(f'<div style="background-color:{cor}; padding:15px; border-radius:10px; text-align:center; color: black; border: 1px solid #ccc;"><b>GAP HOJE EM {ativo}: {gap_hoje}%</b></div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1: data_ini = st.date_input("Início do Histórico:", datetime(2020, 1, 1))
    with c2: gap_alvo = st.number_input("GAP para analisar (%):", value=gap_hoje, step=0.1)
    with c3: min_acc = st.number_input("Min. Acerto Radar (%):", value=80)

    if st.button('🚀 Rodar Estatística e Radar', use_container_width=True):
        # Filtro de histórico
        df_a = df_mestre[(df_mestre['Ativo'] == ativo) & (df_mestre['Date'] >= pd.to_datetime(data_ini))]
        ev = df_a[(df_a['Gap'] <= gap_alvo + 0.15) & (df_a['Gap'] >= gap_alvo - 0.15)]
        
        if not ev.empty:
            st.success(f"### Estatística de GAP para {ativo}")
            res1, res2, res3 = st.columns(3)
            res1.metric("Ocorrências", len(ev))
            res2.metric("Acerto Compra (+0.5%)", f"{round((len(ev[ev['Max_A'] >= 0.5])/len(ev))*100, 1)}%")
            res3.metric("Acerto Venda (-0.5%)", f"{round((len(ev[ev['Min_A'] <= -0.5])/len(ev))*100, 1)}%")
        else:
            st.warning("Poucas ocorrências para este GAP.")

        # Radar
        st.markdown("---")
        st.subheader("🚀 Radar de Elite (Oportunidades de Agora)")
        abas = st.tabs(["65%", "75%", "85%", "95%", "100%"])
        
        radar_lista = []
        with st.spinner("Analisando Radar..."):
            for t in lista_ativos[:40]: # Analisa os 40 primeiros para ser rápido
                g = obter_gap_hoje(t)
                hist_t = df_mestre[df_mestre['Ativo'] == t]
                sim = hist_t[(hist_t['Gap'] <= g + 0.15) & (hist_t['Gap'] >= g - 0.15)]
                if len(sim) >= 5:
                    p_c = (len(sim[sim['Max_A'] >= 0.5]) / len(sim)) * 100
                    p_v = (len(sim[sim['Min_A'] <= -0.5]) / len(sim)) * 100
                    if p_c >= 65 or p_v >= 65:
                        radar_lista.append({"Ativo": t, "GAP": g, "Lado": "🟢 COMPRA" if p_c >= p_v else "🔴 VENDA", "Acerto": max(p_c, p_v)})
        
        df_radar = pd.DataFrame(radar_lista)
        if not df_radar.empty:
            niveis = [65, 75, 85, 95, 100]
            for i, n in enumerate(niveis):
                with abas[i]:
                    st.table(df_radar[df_radar['Acerto'] >= n].sort_values('Acerto', ascending=False))

        # Gráfico
        st.markdown("---")
        fig = px.bar(df_a.tail(50), x='Date', y=['Max_A', 'Min_A'], barmode='group', title=f"Histórico de {ativo}")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.error("Erro na Planilha: Os dados estão colados incorretamente. Tente usar 'Dados > Dividir texto em colunas' no Google Sheets.")
