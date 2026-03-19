import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime
import time

# 1. Configuração de layout
st.set_page_config(page_title="Scanner Quant B3", layout="wide")

st.title("🔍 Scanner de Estatística de Abertura")

# --- LINK DA SUA PLANILHA PUBLICADA ---
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSg04Li1XStwno4T5cQxMuUwDS35uzY2eRoLPi8zUIpxadZpBPTGMbd_IyftA-rbjpuc6_5TQfi0hXv/pub?output=csv"

# --- FUNÇÃO PARA CARREGAR DADOS DA PLANILHA ---
@st.cache_data(ttl=3600)
def carregar_dados_planilha():
    try:
        df = pd.read_csv(URL_PLANILHA)
        # Converte Data
        df['Date'] = pd.to_datetime(df['Date'])
        # GARANTE QUE PREÇOS SÃO NÚMEROS (Resolve o erro TypeError)
        for col in ['Open', 'High', 'Low', 'Close']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df.dropna(subset=['Close'])
    except Exception as e:
        st.error(f"Erro ao carregar planilha: {e}")
        return pd.DataFrame()

# --- FUNÇÃO DO GAP DE HOJE (CONSULTA ÚNICA AO YAHOO) ---
def obter_gap_hoje(ticker):
    try:
        # Baixa apenas 2 dias para ser rápido e não ser bloqueado
        dados = yf.download(ticker, period="2d", progress=False, timeout=10)
        if len(dados) < 2: return 0.0
        # Limpa colunas multi-index do yfinance novo
        dados.columns = [c[0] if isinstance(c, tuple) else c for c in dados.columns]
        
        fechamento_ontem = float(dados['Close'].iloc[-2])
        abertura_hoje = float(dados['Open'].iloc[-1])
        return round(((abertura_hoje / fechamento_ontem) - 1) * 100, 2)
    except:
        return 0.0

# --- FUNÇÃO DE CÁLCULO DE PERFORMANCE ---
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

# --- CARREGAMENTO INICIAL ---
df_completo = carregar_dados_planilha()

if not df_completo.empty:
    # Pega a lista de ativos direto da sua planilha
    lista_ativos = sorted(df_completo['Ativo'].unique())
    
    st.subheader("Configurações do Backtest")
    ativo = st.selectbox("Selecione a ação:", lista_ativos)

    # Mostra o GAP de hoje em destaque
    gap_atual = obter_gap_hoje(ativo)
    cor_caixa = "#d4edda" if gap_atual >= 0 else "#f8d7da"
    st.markdown(f'<div style="background-color:{cor_caixa}; padding:15px; border-radius:10px; text-align:center; color: black; margin-bottom: 20px; border: 1px solid #ccc;">'
                f'<b>GAP DE HOJE EM {ativo}: {gap_atual}%</b></div>', unsafe_allow_html=True)

    col_cfg1, col_cfg2, col_cfg3 = st.columns([1, 1, 1])
    with col_cfg1:
        data_inicio = st.date_input("Data de Início:", datetime(2020, 1, 1))
    with col_cfg2:
        gap_digitado = st.number_input("GAP desejado (%):", value=gap_atual if gap_atual != 0 else -1.0, step=0.1)
    with col_cfg3:
        filtro_radar = st.number_input("Mínimo de Acerto Radar (%):", value=80, step=5)

    rodar = st.button('🚀 Rodar Estatística e Radar', use_container_width=True)

    if rodar:
        # Filtra histórico do ativo selecionado
        df_ativo = df_completo[(df_completo['Ativo'] == ativo) & (df_completo['Date'] >= pd.to_datetime(data_inicio))].copy()
        df_ativo = df_ativo.sort_values('Date')

        # Cálculos de Colunas
        df_ativo['Gap'] = ((df_ativo['Open'] / df_ativo['Close'].shift(1)) - 1) * 100
        df_ativo['Max_Apos_Abertura'] = ((df_ativo['High'] / df_ativo['Open']) - 1) * 100
        df_ativo['Queda_Apos_Abertura'] = ((df_ativo['Low'] / df_ativo['Open']) - 1) * 100
        df_ativo['Resultado_Fechamento'] = ((df_ativo['Close'] / df_ativo['Open']) - 1) * 100
        df_ativo = df_ativo.dropna()

        # 1. ESTATÍSTICA DO GAP
        eventos = df_ativo[(df_ativo['Gap'] <= gap_digitado + 0.15) & (df_ativo['Gap'] >= gap_digitado - 0.15)]
        
        st.success(f"### 🎯 Resultados para GAP próximo de {gap_digitado}%")
        if len(eventos) >= 3:
            y_dig, x_dig = calcular_melhor_performance(eventos)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Ocorrências", len(eventos))
            c2.metric("Probabilidade", f"{x_dig}%")
            c3.metric("Alvo Sugerido", f"{y_dig}%")
            
            # Gráfico de Histórico
            st.markdown("---")
            st.subheader("📊 Histórico de Máximas e Mínimas (pós-abertura)")
            fig = px.bar(eventos, x=eventos.index, y=['Max_Apos_Abertura', 'Queda_Apos_Abertura'],
                         title="Variação Máxima e Mínima em dias similares",
                         labels={'value': 'Percentual', 'Date': 'Data'}, barmode='group')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Poucos dados históricos para este GAP específico.")

        # 2. RADAR DE ELITE (USANDO A PLANILHA)
        st.markdown("---")
        st.subheader(f"🚀 Radar de Elite (Acerto > {filtro_radar}%)")
        radar_lista = []
        progresso = st.progress(0)
        
        # Filtramos o Radar para os 50 ativos mais comuns para evitar lentidão
        ativos_radar = lista_ativos[:50] 
        
        with st.spinner("Analisando mercado..."):
            for i, t in enumerate(ativos_radar):
                progresso.progress((i + 1) / len(ativos_radar))
                
                g_hoje = obter_gap_hoje(t)
                if g_hoje == 0: continue
                
                # Filtra histórico na memória (sem download novo!)
                df_h = df_completo[df_completo['Ativo'] == t].copy().sort_values('Date')
                df_h['G'] = ((df_h['Open'] / df_h['Close'].shift(1)) - 1) * 100
                df_h['M'] = ((df_h['High'] / df_h['Open']) - 1) * 100
                
                similares = df_h[(df_h['G'] <= g_hoje + 0.15) & (df_h['G'] >= g_hoje - 0.15)]
                
                if len(similares) >= 5:
                    # Cálculo simplificado para o Radar ser rápido
                    taxa = (len(similares[similares['M'] >= 0.5]) / len(similares)) * 100
                    if taxa >= filtro_radar:
                        radar_lista.append({"Ativo": t, "GAP Hoje": f"{g_hoje}%", "Confiança": f"{round(taxa,1)}%", "Alvo": "0.5%"})
                
                time.sleep(0.05) # Pequena pausa apenas por segurança

        if radar_lista:
            st.table(pd.DataFrame(radar_lista))
        else:
            st.info("Nenhuma oportunidade detectada no momento.")
else:
    st.error("Não foi possível carregar os dados da planilha. Verifique se ela está publicada como CSV.")
