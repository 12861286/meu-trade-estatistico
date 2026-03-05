import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Scanner Quant Pro", layout="wide")

st.title("🚀 Scanner de Performance: Estatística de Abertura")

# --- LISTA DE ATIVOS ---
@st.cache_data
def carregar_lista_ativos():
    base = ["PETR4", "VALE3", "ITUB4", "BBDC4", "BBAS3", "ABEV3", "MGLU3", "PRIO3", "WEGE3", "RENT3", "GGBR4", "CSNA3"]
    return sorted([f"{a}.SA" for a in base])

# --- BARRA LATERAL ---
st.sidebar.header("Configurações")
ativo = st.sidebar.selectbox("Escolha o Ativo:", carregar_lista_ativos())
data_inicio = st.sidebar.date_input("Histórico desde:", datetime(2021, 1, 1))
alvo_gain = st.sidebar.number_input("Seu Alvo de Lucro (%):", value=1.0, step=0.1)

if st.sidebar.button('Rodar Análise Completa'):
    with st.spinner('Analisando dados reais...'):
        df = yf.download(ativo, start=data_inicio, progress=False)
        
        if not df.empty:
            # Organização e Cálculos Reais
            df = df[['Open', 'High', 'Low', 'Close']].copy()
            df.columns = ['Abertura', 'Maxima', 'Minima', 'Fechamento']
            df['Gap'] = ((df['Abertura'] / df['Fechamento'].shift(1)) - 1) * 100
            df['Subida_Real'] = ((df['Maxima'] / df['Abertura']) - 1) * 100
            df['Final_Dia_Real'] = ((df['Fechamento'] / df['Abertura']) - 1) * 100
            df['Atingiu_Alvo'] = df['Subida_Real'] >= alvo_gain
            
            ranking = []
            for i in range(1, 21):
                teste_gap = round(i * -0.2, 2)
                eventos = df[df['Gap'] <= teste_gap].copy()
                
                if len(eventos) >= 5:
                    taxa = (len(eventos[eventos['Atingiu_Alvo'] == True]) / len(eventos)) * 100
                    ranking.append({
                        "Sugestão": f"GAP abaixo de {teste_gap}%",
                        "GAP": teste_gap,
                        "Dias": len(eventos),
                        "Acerto_Alvo": round(taxa, 1),
                        "Subida_Media": round(eventos['Subida_Real'].mean(), 2),
                        "Fechamento_Medio": round(eventos['Final_Dia_Real'].mean(), 2)
                    })
            
            if ranking:
                df_ranking = pd.DataFrame(ranking).sort_values(by="Acerto_Alvo", ascending=False)
                melhor = df_ranking.iloc[0]
                
                # --- EXIBIÇÃO ---
                st.success(f"### ✨ Melhor Performance: {ativo}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Melhor GAP", f"{melhor['GAP']}%")
                c2.metric(f"Chance de {alvo_gain}%", f"{melhor['Acerto_Alvo']}%")
                c3.metric("Ocorrências", int(melhor['Dias']))

                st.markdown("---")
                st.subheader("📋 O que aconteceu na realidade (Não Alvo)")
                st.write(f"Sempre que o ativo abriu com GAP de **{melhor['GAP']}%**, este foi o comportamento real:")
                
                col_a, col_b = st.columns(2)
                col_a.info(f"**Subida Máxima Média:** {melhor['Subida_Media']}%")
                col_b.info(f"**Resultado Médio no Fechamento:** {melhor['Fechamento_Medio']}%")

                st.write("### Ranking de todos os GAPs testados:")
                st.table(df_ranking[['Sugestão', 'Dias', 'Acerto_Alvo', 'Subida_Media', 'Fechamento_Medio']])
                
                fig = px.bar(df_ranking, x="GAP", y="Acerto_Alvo", title="Taxa de Acerto por Nível de GAP", color="Acerto_Alvo")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Dados insuficientes para este ativo.")
        else:
            st.error("Erro ao buscar dados.")
