import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Scanner Quant B3", layout="wide")

st.title("🔍 Scanner de Estatística de Abertura")

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("Configurações do Backtest")

# 1. Campo de Pesquisa de Ativos (Lista das principais da B3)
lista_ativos = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "ABEV3.SA", "BBAS3.SA", "MGLU3.SA", "WINV24.SA"] # Adicione mais aqui
ativo = st.sidebar.selectbox("Selecione o Ativo:", lista_ativos)

# 2. Data de Início
data_inicio = st.sidebar.date_input("Data de Início da Pesquisa:", datetime(2020, 1, 1))

# 3. Porcentagem do GAP
gap_desejado = st.sidebar.number_input("Porcentagem do GAP (ex: -2.0 ou 1.5):", value=-2.0, step=0.1)

# --- PROCESSAMENTO ---
if st.sidebar.button('Rodar Estatística'):
    with st.spinner('Consultando histórico da B3...'):
        # Busca os dados
        df = yf.download(ativo, start=data_inicio, progress=False)
        
        if not df.empty:
            # Cálculos de GAP e Máxima do Dia
            df['Gap'] = ((df['Open'] / df['Close'].shift(1)) - 1) * 100
            df['Max_Apos_Abertura'] = ((df['High'] / df['Open']) - 1) * 100
            
            # Filtrando os dias que tiveram o GAP que você pediu
            if gap_desejado < 0:
                eventos = df[df['Gap'] <= gap_desejado].copy()
            else:
                eventos = df[df['Gap'] >= gap_desejado].copy()
            
            total_eventos = len(eventos)
            
            if total_eventos > 0:
                # Calculando chances de acerto (se fechou acima da abertura)
                acertos = len(eventos[eventos['Close'] > eventos['Open']])
                taxa_acerto = (acertos / total_eventos) * 100
                maxima_media = eventos['Max_Apos_Abertura'].median()
                
                # --- RELATÓRIO ---
                col1, col2, col3 = st.columns(3)
                col1.metric("Ocorrências", f"{total_eventos} dias")
                col2.metric("Taxa de Acerto (Alta)", f"{taxa_acerto:.1f}%")
                col3.metric("Máxima Média após GAP", f"{maxima_media:.2f}%")
                
                st.subheader(f"📊 Comportamento de {ativo} após GAP de {gap_desejado}%")
                
                # Gráfico Simples de Dispersão
                fig = px.histogram(eventos, x="Max_Apos_Abertura", 
                                 title="Distribuição de quanto o papel subiu após abrir nesse GAP",
                                 labels={'Max_Apos_Abertura': 'Subida após abertura (%)'},
                                 color_discrete_sequence=['#00CC96'])
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabela de Detalhes
                st.write("Últimas ocorrências encontradas:")
                st.dataframe(eventos[['Gap', 'Max_Apos_Abertura']].tail(10))
            else:
                st.warning("Nenhum evento encontrado com esse critério no período selecionado.")
        else:
            st.error("Erro ao buscar dados. Verifique o ticker do ativo.")

else:
    st.info("Ajuste os filtros à esquerda e clique em 'Rodar Estatística'.")
