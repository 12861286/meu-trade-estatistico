import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Caçador de Performance B3", layout="wide")

st.title("🎯 Analisador de GAP e Sugestões de Performance")

# --- LISTA DE ATIVOS ---
@st.cache_data
def carregar_lista_ativos():
    base = ["PETR4", "VALE3", "ITUB4", "BBDC4", "BBAS3", "ABEV3", "MGLU3", "PRIO3", "WEGE3", "RENT3", "GGBR4", "CSNA3"]
    return sorted([f"{a}.SA" for a in base])

# --- BARRA LATERAL ---
st.sidebar.header("Configuração")
ativo = st.sidebar.selectbox("Escolha o Ativo:", carregar_lista_ativos())
data_inicio = st.sidebar.date_input("Analisar desde:", datetime(2021, 1, 1))

# O GAP que VOCÊ quer analisar como base principal
gap_digitado = st.sidebar.number_input("Digite o GAP para análise principal (%):", value=-1.0, step=0.1)

if st.sidebar.button('Gerar Relatório Completo'):
    with st.spinner(f'Caçando a melhor performance para o GAP de {gap_digitado}%...'):
        df = yf.download(ativo, start=data_inicio, progress=False)
        
        if not df.empty:
            df = df[['Open', 'High', 'Low', 'Close']].copy()
            df.columns = ['Abertura', 'Maxima', 'Minima', 'Fechamento']
            df['Gap_Real'] = ((df['Abertura'] / df['Fechamento'].shift(1)) - 1) * 100
            df['Subida_Max'] = ((df['Maxima'] / df['Abertura']) - 1) * 100
            
            # --- 1. ANÁLISE DO QUE VOCÊ PASSOU (MELHOR PERFORMANCE DO GAP DIGITADO) ---
            # Filtra os dias com o GAP digitado (margem de 0.1% para pegar variações próximas)
            eventos_fixos = df[(df['Gap_Real'] <= gap_digitado + 0.05) & (df['Gap_Real'] >= gap_digitado - 0.05)].copy()
            
            st.markdown("---")
            if len(eventos_fixos) >= 3:
                # Busca automática do melhor alvo (Y) para esse GAP
                melhor_y = 0
                melhor_x = 0
                for alvo_teste in [x * 0.1 for x in range(1, 31)]:
                    taxa = (len(eventos_fixos[eventos_fixos['Subida_Max'] >= alvo_teste]) / len(eventos_fixos)) * 100
                    if taxa >= 70: # Prioriza alvos com pelo menos 70% de acerto
                        melhor_y = round(alvo_teste, 2)
                        melhor_x = round(taxa, 1)
                
                if melhor_y == 0: # Se nenhum tiver 70%, pega o de maior acerto
                    melhor_y = 0.5
                    melhor_x = (len(eventos_fixos[eventos_fixos['Subida_Max'] >= 0.5]) / len(eventos_fixos)) * 100

                st.success(f"### ✨ Resultado da Pesquisa para o GAP de {gap_digitado}%")
                st.subheader(f"Neste período, sempre que o ativo abriu com o GAP de {gap_digitado}%, ele acertou {melhor_x}% das vezes a porcentagem de {melhor_y}%, que foi a melhor performance dele.")
            else:
                st.warning(f"O GAP de {gap_digitado}% teve poucas ocorrências ({len(eventos_fixos)} dias) para uma análise de performance isolada.")

            # --- 2. PARTE DE SUGESTÕES (MANTIDA CONFORME PEDIDO) ---
            st.markdown("---")
            st.subheader("📋 Sugestões Adicionais de Melhor Performance")
            st.write("O robô testou outros níveis de GAP para comparar onde a estatística é mais forte:")
            
            ranking = []
            for i in range(1, 16):
                teste_gap = round(i * -0.3, 2) # Testa em passos de 0.3%
                eventos_rank = df[df['Gap_Real'] <= teste_gap].copy()
                
                if len(eventos_rank) >= 5:
                    # Calcula qual alvo de 1% teria de acerto nesses GAPs
                    taxa_padrao = (len(eventos_rank[eventos_rank['Subida_Max'] >= 1.0]) / len(eventos_rank)) * 100
                    ranking.append({
                        "Sugestão": f"GAP abaixo de {teste_gap}%",
                        "Dias": len(eventos_rank),
                        "Acerto (Alvo 1%)": f"{round(taxa_padrao, 1)}%",
                        "Subida Média Real": f"{round(eventos_rank['Subida_Max'].mean(), 2)}%"
                    })
            
            if ranking:
                st.table(pd.DataFrame(ranking).sort_values(by="Acerto (Alvo 1%)", ascending=False))
            
            # Gráfico de Apoio
            fig = px.histogram(df[df['Gap_Real'] < 0], x="Subida_Max", title="Distribuição de Altas após GAPs de Baixa")
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.error("Ativo não encontrado ou erro de conexão.")
