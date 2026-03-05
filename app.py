import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Scanner Quant Pro - Análise Real", layout="wide")

st.title("🚀 Otimizador de Entradas e Análise de Desfecho")

# --- LISTA DE ATIVOS ---
@st.cache_data
def carregar_lista_ativos():
    base = ["PETR4", "VALE3", "ITUB4", "BBDC4", "BBAS3", "ABEV3", "MGLU3", "PRIO3", "WEGE3", "RENT3", "GGBR4", "CSNA3"]
    return sorted([f"{a}.SA" for a in base])

# --- SIDEBAR ---
st.sidebar.header("Configurações do Robô")
ativo = st.sidebar.selectbox("Escolha o Ativo:", carregar_lista_ativos())
data_inicio = st.sidebar.date_input("Analisar histórico desde:", datetime(2021, 1, 1))
alvo_gain = st.sidebar.number_input("Seu Alvo de Lucro Pessoal (%):", value=1.0, step=0.1)

if st.sidebar.button('Gerar Relatório de Performance'):
    with st.spinner('Escaneando histórico e calculando desfechos reais...'):
        df = yf.download(ativo, start=data_inicio, progress=False)
        
        if not df.empty:
            df = df[['Open', 'High', 'Low', 'Close']].copy()
            df.columns = ['Abertura', 'Maxima', 'Minima', 'Fechamento']
            df['Gap'] = ((df['Abertura'] / df['Fechamento'].shift(1)) - 1) * 100
            
            # Cálculo do que aconteceu na realidade (sem filtro de alvo ainda)
            df['Subida_Real'] = ((df['Maxima'] / df['Abertura']) - 1) * 100
            df['Fechamento_Real'] = ((df['Fechamento'] / df['Abertura']) - 1) * 100
            df['Atingiu_Alvo'] = df['Subida_Real'] >= alvo_gain
            
            ranking = []
            for i in range(1, 21):
                teste_gap = round(i * -0.2, 2)
                eventos = df[df['Gap'] <= teste_gap].copy()
                
                if len(eventos) >= 5:
                    acertos_alvo = len(eventos[eventos['Atingiu_Alvo'] == True])
                    taxa_alvo = (acertos_alvo / len(eventos)) * 100
                    
                    # Análise do que aconteceu de verdade (Médias reais)
                    max_media = eventos['Subida_Real'].mean()
                    fechamento_medio = eventos['Fechamento_Real'].mean()
                    
                    ranking.append({
                        "Sugestão": f"GAP abaixo de {teste_gap}%",
                        "GAP (%)": teste_gap,
                        "Ocorrências": len(eventos),
                        "Taxa de Acerto (Seu Alvo)": round(taxa_alvo, 1),
                        "Máxima Média Real": round(max_media, 2),
                        "Final do Dia Médio": round(fechamento_medio, 2)
                    })
            
            if ranking:
                df_ranking = pd.DataFrame(ranking).sort_values(by="Taxa de Acerto (Seu Alvo)", ascending=False)
                melhor = df_ranking.iloc[0]
                
                # --- EXIBIÇÃO PRINCIPAL ---
                st.success(f"### ✨ Melhor Performance: {ativo}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Melhor GAP de Entrada", f"{melhor['GAP (%)']}%")
                c2.metric(f"Chance de bater {alvo_gain}%", f"{melhor['Taxa de Acerto (Seu Alvo)']}%")
                c3.metric("Amostragem", f"{int(melhor['Ocorrências'])} dias")

                # --- ANÁLISE DO DESFECHO (O QUE ACONTECEU NO ALVO) ---
                st.markdown("---")
                st.subheader("📈 Análise de Desfecho Real (O que acontece após a abertura)")
                st.write(f"Para o melhor GAP encontrado ({melhor['GAP (%)']}%), veja o comportamento real do preço:")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.info(f"**Subida Máxima Média:** {melhor['Máxima Média Real']}%")
                    st.write("Isso indica até onde o preço costuma "esticar" em média antes de parar.")
                with col_b:
                    st.info(f"**Resultado Médio no Fechamento:** {melhor['Final do Dia Médio']}%")
                    st.write("Se for positivo, o papel tende a segurar a alta. Se for negativo, ele tende a devolver.")

                # --- TABELA DE SUGESTÕES COMPLETA ---
                st.subheader("📋 Ranking de Performance por Nível de GAP")
                st.table(df_ranking.head(8)[['Sugestão', 'Ocorrências', 'Taxa de Acerto (Seu Alvo)', 'Máxima Média Real', 'Final do Dia Médio']])

                # Gráfico
                fig = px.bar(df_ranking, x="GAP (%)", y="Máxima Média Real", 
                            title="Potencial de Subida Real por Nível de GAP",
                            color="Taxa de Acerto (Seu Alvo)", color_continuous_scale="Viridis")
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.warning("Não encontramos ocorrências suficientes para gerar sugestões.")
        else:
            st.error("Erro ao buscar dados.")
