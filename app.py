import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime
import time

# 1. Configuração de layout (Seu visual original)
st.set_page_config(page_title="Scanner Quant B3", layout="wide")
st.title("🔍 Scanner de Estatística: Compra e Venda")

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSg04Li1XStwno4T5cQxMuUwDS35uzY2eRoLPi8zUIpxadZpBPTGMbd_IyftA-rbjpuc6_5TQfi0hXv/pub?output=csv"

@st.cache_data(ttl=3600)
def carregar_dados():
    try:
        df = pd.read_csv(URL_PLANILHA)
        df['Date'] = pd.to_datetime(df['Date'])
        
        # LIMPEZA CRÍTICA: Remove pontos de milhar e garante números
        colunas_num = ['Open', 'High', 'Low', 'Close', 'Gap', 'Max_A', 'Min_A']
        for col in colunas_num:
            if col in df.columns:
                # Transforma em texto, remove pontos e vira número
                df[col] = df[col].astype(str).str.replace('.', '', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df.dropna(subset=['Open', 'Close'])
    except Exception as e:
        st.error(f"Erro ao processar dados: {e}")
        return pd.DataFrame()

def obter_gap_hoje(ticker):
    try:
        d = yf.download(ticker, period="2d", progress=False, timeout=10)
        if len(d) < 2: return 0.0
        d.columns = [c[0] if isinstance(c, tuple) else c for c in d.columns]
        fechamento_ontem = float(d['Close'].iloc[-2])
        abertura_hoje = float(d['Open'].iloc[-1])
        return round(((abertura_hoje / fechamento_ontem) - 1) * 100, 2)
    except:
        return 0.0

df_mestre = carregar_dados()

if not df_mestre.empty:
    lista_ativos = sorted(df_mestre['Ativo'].unique())
    
    # --- SEU VISUAL ORIGINAL DE CONFIGURAÇÃO ---
    st.subheader("Configurações do Backtest")
    ativo = st.selectbox("Selecione a ação:", lista_ativos)
    
    gap_atual = obter_gap_hoje(ativo)
    cor_caixa = "#d4edda" if gap_atual >= 0 else "#f8d7da"
    st.markdown(f'<div style="background-color:{cor_caixa}; padding:15px; border-radius:10px; text-align:center; color: black; margin-bottom: 20px; border: 1px solid #ccc;">'
                f'<b>GAP HOJE EM {ativo}: {gap_atual}%</b></div>', unsafe_allow_html=True)

    col_cfg1, col_cfg2, col_cfg3 = st.columns([1, 1, 1])
    with col_cfg1:
        data_inicio = st.date_input("Data de Início:", datetime(2020, 1, 1))
    with col_cfg2:
        gap_digitado = st.number_input("GAP desejado (%):", value=gap_atual, step=0.1)
    with col_cfg3:
        filtro_radar = st.number_input("Mínimo de Acerto Radar (%):", value=80, step=5)

    rodar = st.button('🚀 Rodar Estatística e Radar', use_container_width=True)

    if rodar:
        # 1. RESULTADOS (USANDO MÉTRICAS COMO NO SEU VISUAL ANTIGO)
        df_ativo = df_mestre[(df_mestre['Ativo'] == ativo) & (df_mestre['Date'] >= pd.to_datetime(data_inicio))].copy()
        eventos = df_ativo[(df_ativo['Gap'] <= gap_digitado + 0.15) & (df_ativo['Gap'] >= gap_digitado - 0.15)]
        
        st.success(f"### 🎯 Resultados para GAP de {gap_digitado}%")
        if not eventos.empty:
            acc_buy = (len(eventos[eventos['Max_A'] >= 0.5]) / len(eventos)) * 100
            acc_sell = (len(eventos[eventos['Min_A'] <= -0.5]) / len(eventos)) * 100
            
            # Mostra em colunas bonitas como você gosta
            c1, c2, c3 = st.columns(3)
            c1.metric("Ocorrências", len(eventos))
            c2.metric("Chance COMPRA (+0.5%)", f"{round(acc_buy, 1)}%")
            c3.metric("Chance VENDA (-0.5%)", f"{round(acc_sell, 1)}%")
        else:
            st.warning("Sem dados históricos para este GAP.")

        # 2. RADAR DE ELITE (COM AS TABS QUE VOCÊ PEDIU)
        st.markdown("---")
        st.subheader(f"🚀 Radar de Elite (Acerto > {filtro_radar}%)")
        
        abas = st.tabs(["65%", "75%", "85%", "95%", "100%"])
        radar_lista = []
        
        with st.spinner("Analisando mercado..."):
            for t in lista_ativos[:40]:
                g_hoje = obter_gap_hoje(t)
                hist_t = df_mestre[df_mestre['Ativo'] == t]
                similares = hist_t[(hist_t['Gap'] <= g_hoje + 0.15) & (hist_t['Gap'] >= g_hoje - 0.15)]
                
                if len(similares) >= 5:
                    buy_t = (len(similares[similares['Max_A'] >= 0.5]) / len(similares)) * 100
                    sell_t = (len(similares[similares['Min_A'] <= -0.5]) / len(similares)) * 100
                    
                    if buy_t >= sell_t and buy_t >= 65:
                        radar_lista.append({"Ativo": t, "GAP": f"{g_hoje}%", "Lado": "🟢 COMPRA", "Acerto": buy_t})
                    elif sell_t > buy_t and sell_t >= 65:
                        radar_lista.append({"Ativo": t, "GAP": f"{g_hoje}%", "Lado": "🔴 VENDA", "Acerto": sell_t})

        df_radar = pd.DataFrame(radar_lista)
        if not df_radar.empty:
            for i, corte in enumerate([65, 75, 85, 95, 100]):
                with abas[i]:
                    final = df_radar[df_radar['Acerto'] >= corte].sort_values('Acerto', ascending=False)
                    if not final.empty:
                        st.table(final)
                    else:
                        st.write("Nada neste nível hoje.")

        # 3. GRÁFICO (O SEU ORIGINAL)
        st.markdown("---")
        st.subheader("📊 Histórico de Variações")
        fig = px.bar(df_ativo.tail(50), x='Date', y=['Max_A', 'Min_A'], barmode='group')
        st.plotly_chart(fig, use_container_width=True)
else:
    st.error("Erro ao carregar a planilha. Verifique os dados.")
