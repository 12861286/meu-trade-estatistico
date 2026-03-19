import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime
import time

# 1. Configuração de layout (SEU VISUAL ORIGINAL)
st.set_page_config(page_title="Scanner Quant B3", layout="wide")
st.title("🔍 Scanner de Estatística de Abertura")

# Link da sua planilha Google Publicada como CSV
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSg04Li1XStwno4T5cQxMuUwDS35uzY2eRoLPi8zUIpxadZpBPTGMbd_IyftA-rbjpuc6_5TQfi0hXv/pub?output=csv"

@st.cache_data(ttl=3600)
def carregar_dados():
    try:
        # Lendo a planilha e tratando o ponto como separador de milhar (thousands='.')
        # Isso evita que o GAP e os Preços venham como "texto" e travem o site
        df = pd.read_csv(URL_PLANILHA, thousands='.')
        
        # Converte a coluna de data
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        # Garante que as colunas numéricas sejam lidas corretamente
        colunas_financeiras = ['Open', 'High', 'Low', 'Close', 'Gap', 'Max_A', 'Min_A']
        for col in colunas_financeiras:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df.dropna(subset=['Ativo', 'Open'])
    except Exception as e:
        st.error(f"Erro técnico ao carregar planilha: {e}")
        return pd.DataFrame()

def obter_gap_hoje(ticker):
    try:
        # Consulta rápida ao Yahoo Finance para o GAP de agora
        dados = yf.download(ticker, period="2d", progress=False, timeout=10)
        if dados.empty: return 0.0
        # Ajuste para garantir que pega as colunas certas independente do formato do yfinance
        dados.columns = [c[0] if isinstance(c, tuple) else c for c in dados.columns]
        fechamento_ontem = float(dados['Close'].iloc[-2])
        abertura_hoje = float(dados['Open'].iloc[-1])
        return round(((abertura_hoje / fechamento_ontem) - 1) * 100, 2)
    except:
        return 0.0

# --- EXECUÇÃO DO APP ---
df_mestre = carregar_dados()

if not df_mestre.empty:
    lista_ativos_full = sorted(df_mestre['Ativo'].unique())
    
    st.subheader("Configurações do Backtest")
    ativo = st.selectbox("Selecione a ação:", lista_ativos_full)

    gap_hoje = obter_gap_hoje(ativo)
    
    # Sua caixa de destaque colorida original
    cor_fundo = "#d4edda" if gap_hoje >= 0 else "#f8d7da"
    st.markdown(f'''
        <div style="background-color:{cor_fundo}; padding:15px; border-radius:10px; text-align:center; color: black; margin-bottom: 20px; border: 1px solid #ddd;">
            <h3 style="margin:0;">GAP HOJE EM {ativo}: {gap_hoje}%</h3>
        </div>
    ''', unsafe_allow_html=True)

    col_cfg1, col_cfg2, col_cfg3 = st.columns([1, 1, 1])
    with col_cfg1:
        data_inicio = st.date_input("Data de Início:", datetime(2020, 1, 1))
    with col_cfg2:
        gap_digitado = st.number_input("GAP para análise (%):", value=gap_hoje, step=0.1)
    with col_cfg3:
        filtro_radar = st.number_input("Mínimo de Acerto Radar (%):", value=80, step=5)

    if st.button('🚀 Rodar Estatística e Radar de Elite', use_container_width=True):
        # 1. Estatística do Ativo Selecionado
        df_ativo = df_mestre[(df_mestre['Ativo'] == ativo) & (df_mestre['Date'] >= pd.to_datetime(data_inicio))].copy()
        eventos = df_ativo[(df_ativo['Gap'] <= gap_digitado + 0.15) & (df_ativo['Gap'] >= gap_digitado - 0.15)]
        
        if not eventos.empty:
            st.success(f"### 🎯 Histórico para GAP de {gap_digitado}%")
            
            # Cálculo de assertividade (Alvo fixo de 0.5%)
            acc_buy = (len(eventos[eventos['Max_A'] >= 0.5]) / len(eventos)) * 100
            acc_sell = (len(eventos[eventos['Min_A'] <= -0.5]) / len(eventos)) * 100
            
            # Suas métricas originais em 3 colunas
            m1, m2, m3 = st.columns(3)
            m1.metric("Ocorrências", len(eventos))
            m2.metric("Acerto COMPRA (+0.5%)", f"{round(acc_buy, 1)}%")
            m3.metric("Acerto VENDA (-0.5%)", f"{round(acc_sell, 1)}%")
        else:
            st.warning("Não encontramos ocorrências desse GAP no período selecionado.")

        # 2. Radar de Elite (Bidirecional com Abas)
        st.markdown("---")
        st.subheader(f"🚀 Radar de Elite (> {filtro_radar}% de Acerto)")
        
        abas = st.tabs(["65%", "75%", "85%", "95%", "100%"])
        radar_lista = []
        
        # Escaneando os ativos (Limite de 35 para manter a velocidade)
        with st.spinner("Escaneando ativos..."):
            for t in lista_ativos_full[:35]:
                g_atual = obter_gap_hoje(t)
                hist_t = df_mestre[df_mestre['Ativo'] == t]
                similares = hist_t[(hist_t['Gap'] <= g_atual + 0.15) & (hist_t['Gap'] >= g_atual - 0.15)]
                
                if len(similares) >= 5:
                    p_buy = (len(similares[similares['Max_A'] >= 0.5]) / len(similares)) * 100
                    p_sell = (len(similares[similares['Min_A'] <= -0.5]) / len(similares)) * 100
                    
                    if p_buy >= p_sell and p_buy >= 65:
                        radar_lista.append({"Ativo": t, "GAP": f"{g_atual}%", "Lado": "🟢 COMPRA", "Acerto": p_buy})
                    elif p_sell > p_buy and p_sell >= 65:
                        radar_lista.append({"Ativo": t, "GAP": f"{g_atual}%", "Lado": "🔴 VENDA", "Acerto": p_sell})

        df_radar = pd.DataFrame(radar_lista)
        if not df_radar.empty:
            niveis = [65, 75, 85, 95, 100]
            for i, n in enumerate(niveis):
                with abas[i]:
                    dados_aba = df_radar[df_radar['Acerto'] >= n].sort_values('Acerto', ascending=False)
                    if not dados_aba.empty:
                        st.table(dados_aba)
                    else:
                        st.write("Nenhuma oportunidade neste nível.")

        # 3. Gráfico de Histórico Original
        st.markdown("---")
        st.subheader(f"📊 Histórico de Oscilação - {ativo}")
        fig = px.bar(df_ativo.tail(50), x='Date', y=['Max_A', 'Min_A'], barmode='group', 
                     title="Variação Máxima e Mínima após a Abertura")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.error("Aguardando dados da planilha... Verifique se ela está publicada como CSV no Google.")
