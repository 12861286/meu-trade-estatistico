import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. Configuração de layout
st.set_page_config(page_title="Scanner Quant B3 - Radar", layout="wide")

st.title("🔍 Scanner de Estatística e Radar de Oportunidades")

# --- LISTA DE ATIVOS ---
@st.cache_data
def carregar_lista_ativos():
    # Lista otimizada com os mais líquidos
    return ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "BBAS3.SA", "ABEV3.SA", "MGLU3.SA", "PRIO3.SA", "WEGE3.SA", "RENT3.SA", "GGBR4.SA", "CSNA3.SA", "ELET3.SA", "B3SA3.SA"]

# --- FUNÇÃO PARA CALCULAR PERFORMANCE ---
def calcular_melhor_performance(df_eventos):
    melhor_y, melhor_x = 0, 0
    if len(df_eventos) >= 3:
        for alvo_t in [x * 0.1 for x in range(1, 31)]:
            taxa = (len(df_eventos[df_eventos['Max_Apos_Abertura'] >= alvo_t]) / len(df_eventos)) * 100
            if taxa >= 75: 
                melhor_y, melhor_x = round(alvo_t, 2), round(taxa, 1)
    return melhor_y, melhor_x

# --- BARRA LATERAL ---
st.sidebar.header("Configurações do Backtest")
lista_ativos = carregar_lista_ativos()
ativo_selecionado = st.sidebar.selectbox("Selecione o Ativo para Análise Detalhada:", lista_ativos)
data_inicio = st.sidebar.date_input("Data de Início da Pesquisa:", datetime(2020, 1, 1))
gap_digitado = st.sidebar.number_input("Porcentagem do GAP desejada:", value=-1.0, step=0.1)

rodar = st.sidebar.button('🚀 Rodar Análise e Radar')

# --- PROCESSAMENTO ---
if rodar:
    with st.spinner('Escaneando mercado e histórico...'):
        # --- PARTE 1: RADAR DE OPORTUNIDADES DO DIA (NOVO) ---
        st.subheader("📡 Radar de Oportunidades (GAPs de Hoje com +80% de Acerto)")
        oportunidades = []
        
        for ticker in lista_ativos:
            dados_radar = yf.download(ticker, period="max", progress=False)
            if len(dados_radar) > 100:
                dados_radar.columns = [c[0] if isinstance(c, tuple) else c for c in dados_radar.columns]
                # Cálculo do GAP de hoje
                fech_ontem = dados_radar['Close'].iloc[-2]
                aber_hoje = dados_radar['Open'].iloc[-1]
                gap_hoje = round(((aber_hoje / fech_ontem) - 1) * 100, 2)
                
                # Histórico
                df_hist = dados_radar.copy()
                df_hist['Gap'] = ((df_hist['Open'] / df_hist['Close'].shift(1)) - 1) * 100
                df_hist['Max_Apos_Abertura'] = ((df_hist['High'] / df_hist['Open']) - 1) * 100
                df_hist['Queda_Apos_Abertura'] = ((df_hist['Low'] / df_hist['Open']) - 1) * 100
                
                # Procura dias parecidos com hoje
                ev_hoje = df_hist[(df_hist['Gap'] <= gap_hoje + 0.15) & (df_hist['Gap'] >= gap_hoje - 0.15)]
                
                if len(ev_hoje) >= 5:
                    y, x = calcular_melhor_performance(ev_hoje)
                    if x >= 80: # FILTRO DE ELITE
                        oportunidades.append({
                            "Ativo": ticker,
                            "GAP Hoje": f"{gap_hoje}%",
                            "Probabilidade": f"{x}%",
                            "Alvo Sugerido": f"{y}%",
                            "Stop Técnico": f"{round(ev_hoje['Queda_Apos_Abertura'].mean(), 2)}%"
                        })
        
        if oportunidades:
            st.table(pd.DataFrame(oportunidades))
            st.info("💡 Os ativos acima abriram hoje em um cenário que historicamente paga muito bem.")
        else:
            st.write("Nenhum ativo da lista atingiu 80% de acerto com o GAP de hoje.")

        # --- PARTE 2: ANÁLISE DETALHADA (O QUE JÁ ESTAVA PRONTO) ---
        st.markdown("---")
        df = yf.download(ativo_selecionado, start=data_inicio, progress=False)
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        
        df['Gap'] = ((df['Open'] / df['Close'].shift(1)) - 1) * 100
        df['Max_Apos_Abertura'] = ((df['High'] / df['Open']) - 1) * 100
        df['Queda_Apos_Abertura'] = ((df['Low'] / df['Open']) - 1) * 100
        
        eventos_digitados = df[(df['Gap'] <= gap_digitado + 0.1) & (df['Gap'] >= gap_digitado - 0.1)].copy()
        
        st.success(f"### 🎯 Detalhes do Ativo Selecionado: {ativo_selecionado}")
        if len(eventos_digitados) >= 3:
            y_dig, x_dig = calcular_melhor_performance(eventos_digitados)
            st.subheader(f"Para o GAP de {gap_digitado}%, a melhor performance é de {y_dig}% com {x_dig}% de acerto.")
            st.warning(f"Stop médio para este cenário: {round(eventos_digitados['Queda_Apos_Abertura'].mean(), 2)}%")
        
        # --- TABELA DE SUGESTÕES ADICIONAIS ---
        st.markdown("---")
        st.subheader("📋 Sugestões Adicionais (Range: +5% a -5%)")
        ranking = []
        for val in [x * 1.0 for x in range(-5, 6)]:
            t_gap = round(val, 2)
            ev_r = df[(df['Gap'] <= t_gap + 0.3) & (df['Gap'] >= t_gap - 0.3)]
            if len(ev_r) >= 5:
                ranking.append({
                    "Faixa de GAP": f"Próximo a {t_gap}%",
                    "Dias": len(ev_r),
                    "Acerto (Alvo 1%)": f"{round((len(ev_r[ev_r['Max_Apos_Abertura'] >= 1.0]) / len(ev_r)) * 100, 1)}%",
                    "Stop Médio": f"{round(ev_r['Queda_Apos_Abertura'].mean(), 2)}%"
                })
        st.table(pd.DataFrame(ranking))

        # --- GRÁFICO EM LINHA ---
        st.markdown("---")
        st.subheader("📈 Histórico de Performance em Linha")
        fig = px.line(eventos_digitados.sort_index(), y="Max_Apos_Abertura", markers=True)
        st.plotly_chart(fig, use_container_width=True)
