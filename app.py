import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime
import time

# 1. Configuração de layout
st.set_page_config(page_title="Scanner Quant B3", layout="wide")

st.title("🔍 Scanner de Estatística de Abertura")

# --- LINK DA SUA PLANILHA ---
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSg04Li1XStwno4T5cQxMuUwDS35uzY2eRoLPi8zUIpxadZpBPTGMbd_IyftA-rbjpuc6_5TQfi0hXv/pub?output=csv"

# --- CARREGAR DADOS DA PLANILHA (MUITO MAIS RÁPIDO) ---
@st.cache_data(ttl=3600) # Guarda os dados por 1 hora
def carregar_dados_planilha():
    try:
        df = pd.read_csv(URL_PLANILHA)
        # Converte a coluna Date para data real
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except Exception as e:
        st.error(f"Erro ao carregar planilha: {e}")
        return pd.DataFrame()

# --- FUNÇÃO DO GAP DE HOJE (ÚNICA CONSULTA AO YAHOO) ---
def obter_gap_hoje(ticker):
    try:
        dados = yf.download(ticker, period="2d", progress=False)
        if len(dados) < 2: return 0.0
        dados.columns = [c[0] if isinstance(c, tuple) else c for c in dados.columns]
        fechamento_ontem = float(dados['Close'].iloc[-2])
        abertura_hoje = float(dados['Open'].iloc[-1])
        return round(((abertura_hoje / fechamento_ontem) - 1) * 100, 2)
    except:
        return 0.0

# --- FUNÇÃO PARA CALCULAR MELHOR PERFORMANCE ---
def calcular_melhor_performance(df_eventos):
    melhor_y, melhor_x = 0, 0
    if len(df_eventos) >= 3:
        for alvo_t in [x * 0.1 for x in range(1, 41)]:
            taxa = (len(df_eventos[df_eventos['Max_Apos_Abertura'] >= alvo_t]) / len(df_eventos)) * 100
            if taxa >= 70: 
                melhor_y, melhor_x = round(alvo_t, 2), round(taxa, 1)
        if melhor_y == 0: 
            melhor_y = 0.5
            melhor_x = round((len(df_eventos[df_eventos['Max_Apos_Abertura'] >= 0.5]) / len(df_eventos)) * 100, 1)
    return melhor_y, melhor_x

# --- INÍCIO DO APP ---
df_completo = carregar_dados_planilha()

if not df_completo.empty:
    lista_ativos = sorted(df_completo['Ativo'].unique())
    
    st.subheader("Configurações do Backtest")
    ativo = st.selectbox("Selecione a ação:", lista_ativos)

    gap_atual = obter_gap_hoje(ativo)
    cor_caixa = "#d4edda" if gap_atual >= 0 else "#f8d7da"
    st.markdown(f'<div style="background-color:{cor_caixa}; padding:10px; border-radius:10px; text-align:center; color: black; margin-bottom: 20px;"><b>GAP HOJE: {gap_atual}%</b></div>', unsafe_allow_html=True)

    col_cfg1, col_cfg2, col_cfg3 = st.columns([1, 1, 1])
    with col_cfg1:
        data_inicio = st.date_input("Data de Início:", datetime(2020, 1, 1))
    with col_cfg2:
        gap_digitado = st.number_input("GAP desejado (%):", value=-1.0, step=0.1)
    with col_cfg3:
        filtro_radar = st.number_input("Mínimo de Acerto Radar (%):", value=80, step=5)

    rodar = st.button('🚀 Rodar Estatística e Radar', use_container_width=True)

    if rodar:
        # Filtrar dados do ativo selecionado direto do DataFrame da Planilha
        df_ativo = df_completo[(df_completo['Ativo'] == ativo) & (df_completo['Date'] >= pd.to_datetime(data_inicio))].copy()
        
        # Recalcular Gaps e Máximas (caso não estejam prontos na planilha)
        df_ativo = df_ativo.sort_values('Date')
        df_ativo['Gap'] = ((df_ativo['Open'] / df_ativo['Close'].shift(1)) - 1) * 100
        df_ativo['Max_Apos_Abertura'] = ((df_ativo['High'] / df_ativo['Open']) - 1) * 100
        df_ativo['Queda_Apos_Abertura'] = ((df_ativo['Low'] / df_ativo['Open']) - 1) * 100
        df_ativo['Resultado_Fechamento'] = ((df_ativo['Close'] / df_ativo['Open']) - 1) * 100
        df_ativo = df_ativo.dropna()

        # ESTATÍSTICA DO GAP DIGITADO
        eventos_digitados = df_ativo[(df_ativo['Gap'] <= gap_digitado + 0.15) & (df_ativo['Gap'] >= gap_digitado - 0.15)]
        st.success(f"### 🎯 GAP Digitado: {gap_digitado}% | Ativo: {ativo}")
        
        if len(eventos_digitados) >= 3:
            y_dig, x_dig = calcular_melhor_performance(eventos_digitados)
            st.subheader(f"Probabilidade de {x_dig}% para atingir {y_dig}% de alvo.")
            
        # --- NOVO RADAR (SEM BLOQUEIO) ---
        st.markdown("---")
        st.subheader(f"🚀 Radar de Elite (> {filtro_radar}% Acerto)")
        radar_hoje = []
        
        # 1. Pegamos os GAPs de hoje de uma vez só (Pacote de ativos)
        with st.spinner("Lendo GAPs de hoje..."):
            # Limitamos a 40 ativos para o Radar não ficar lento
            top_ativos = lista_ativos[:40] 
            for ticker in top_ativos:
                g_hoje = obter_gap_hoje(ticker)
                
                # Filtra o histórico desse ticker na planilha (Sem perguntar ao Yahoo!)
                df_hist = df_completo[df_completo['Ativo'] == ticker].copy().sort_values('Date')
                df_hist['Gap_H'] = ((df_hist['Open'] / df_hist['Close'].shift(1)) - 1) * 100
                df_hist['Max_Apos_Abertura'] = ((df_hist['High'] / df_hist['Open']) - 1) * 100
                
                # Procura casos similares
                f_h = df_hist[(df_hist['Gap_H'] <= g_hoje + 0.15) & (df_hist['Gap_H'] >= g_hoje - 0.15)]
                
                if len(f_h) >= 4:
                    yr, xr = calcular_melhor_performance(f_h)
                    if xr >= filtro_radar:
                        radar_hoje.append({"Ativo": ticker, "GAP Hoje": f"{g_hoje}%", "Acerto": f"{xr}%", "Alvo": f"{yr}%"})
        
        if radar_hoje:
            st.table(pd.DataFrame(radar_hoje))
        else:
            st.write("Nenhuma oportunidade encontrada com este filtro.")
