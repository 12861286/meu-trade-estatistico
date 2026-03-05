import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Scanner Quant B3", layout="wide")

# Título e Estilo
st.title("🔍 Scanner de Estatística de Abertura")

# --- BUSCA AUTOMÁTICA DE ATIVOS ---
@st.cache_data
def carregar_lista_ativos():
    # Lista das principais ações da B3 (pode ser expandida)
    base_ativos = [
        "PETR4", "VALE3", "ITUB4", "BBDC4", "BBAS3", "ABEV3", "MGLU3", "VIIA3", 
        "HAPV3", "SANB11", "RENT3", "LREN3", "PRIO3", "WEGE3", "SUZB3", "ELET3"
    ]
    return [f"{a}.SA" for a in base_ativos]

# --- BARRA LATERAL ---
st.sidebar.header("Configurações do Backtest")

ativos_disponiveis = carregar_lista_ativos()
ativo = st.sidebar.selectbox("Selecione ou digite o Ativo:", ativos_disponiveis)

data_inicio = st.sidebar.date_input("Data de Início da Pesquisa:", datetime(2020, 1, 1))

gap_desejado = st.sidebar.number_input("GAP desejado % (ex: -2.0):", value=-2.0, step=0.1)

# --- PROCESSAMENTO ---
if st.sidebar.button('Rodar Estatística'):
    with st.spinner('Analisando dados...'):
        df = yf.download(ativo, start=data_inicio, progress=False)
        
        if not df.empty:
            # Organizando os dados para evitar o erro de visualização
            df = df[['Open', 'High', 'Low', 'Close']].copy()
            df.columns = ['Abertura', 'Maxima', 'Minima', 'Fechamento']
            
            # Cálculos
            df['Gap'] = ((df['Abertura'] / df['Fechamento'].shift(1)) - 1) * 100
            df['Max_Apos_Abertura'] = ((df['Maxima'] / df['Abertura']) - 1) * 100
            
            # Filtro do GAP
            if gap_desejado < 0:
                eventos = df[df['Gap'] <= gap_desejado].copy()
            else:
                eventos = df[df['Gap'] >= gap_desejado].copy()
            
            # Limpeza para o gráfico (remove valores vazios)
            eventos = eventos.dropna()
            
            if len(eventos) > 0:
                # Métricas
                total = len(eventos)
                acertos = len(eventos[eventos['Fechamento'] > eventos['Abertura']])
                taxa_acerto = (acertos / total) * 100
                max_frequente = eventos['Max_Apos_Abertura'].mode().iloc[0] if not eventos.empty else 0
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Ocorrências", f"{total} dias")
                col2.metric("Taxa de Acerto", f"{taxa_acerto:.1f}%")
                col3.metric("Máxima mais Comum", f"{max_frequente:.2f}%")
                
                st.subheader(f"Estatística: {ativo} abrindo com {gap_desejado}% de GAP")
                
                # Gráfico Corrigido
                hist_data = eventos['Max_Apos_Abertura'].astype(float)
                fig = px.histogram(hist_data, nbins=20, title="Distribuição de Altas após a Abertura",
                                 labels={'value': 'Subida (%)', 'count': 'Frequência'},
                                 color_discrete_sequence=['#00CC96'])
                st.plotly_chart(fig, use_container_width=True)
                
                st.write("### Últimas 10 vezes que isso aconteceu:")
                st.table(eventos[['Gap', 'Max_Apos_Abertura']].tail(10))
            else:
                st.warning("Nenhum dia encontrado com esse GAP no período.")
        else:
            st.error("Ativo não encontrado.")
