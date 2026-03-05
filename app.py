import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Scanner Quant Pro - Sugestões", layout="wide")

st.title("🚀 Otimizador de Entradas: Estatística de Abertura")

# --- LISTA DE ATIVOS ---
@st.cache_data
def carregar_lista_ativos():
    # Adicionei mais alguns ativos líquidos da B3
    base = ["PETR4", "VALE3", "ITUB4", "BBDC4", "BBAS3", "ABEV3", "MGLU3", "PRIO3", "WEGE3", "RENT3", "GGBR4", "CSNA3"]
    return sorted([f"{a}.SA" for a in base])

# --- SIDEBAR ---
st.sidebar.header("Configurações do Robô")
ativo = st.sidebar.selectbox("Escolha o Ativo:", carregar_lista_ativos())
data_inicio = st.sidebar.date_input("Analisar histórico desde:", datetime(2021, 1, 1))
alvo_gain = st.sidebar.number_input("Alvo de Lucro desejado (%):", value=1.0, step=0.1)

if st.sidebar.button('Gerar Relatório de Performance'):
    with st.spinner('Escaneando histórico e calculando probabilidades...'):
        df = yf.download(ativo, start=data_inicio, progress=False)
        
        if not df.empty:
            # Organização dos dados
            df = df[['Open', 'High', 'Low', 'Close']].copy()
            df.columns = ['Abertura', 'Maxima', 'Minima', 'Fechamento']
            df['Gap'] = ((df['Abertura'] / df['Fechamento'].shift(1)) - 1) * 100
            
            # Cálculo de atingimento do alvo (High vs Abertura)
            df['Atingiu_Alvo'] = ((df['Maxima'] / df['Abertura']) - 1) * 100 >= alvo_gain
            
            # --- LOOP DE TESTES (OTIMIZAÇÃO) ---
            ranking = []
            # Testa gaps de -0.2% até -4.0% com passo de 0.2%
            for i in range(1, 21):
                teste_gap = round(i * -0.2, 2)
                eventos = df[df['Gap'] <= teste_gap]
                
                if len(eventos) >= 5: # Filtro de confiança: no mínimo 5 ocorrências
                    acertos = len(eventos[eventos['Atingiu_Alvo'] == True])
                    taxa = (acertos / len(eventos)) * 100
                    ranking.append({
                        "Sugestão": f"GAP abaixo de {teste_gap}%",
                        "GAP (%)": teste_gap,
                        "Ocorrências": len(eventos),
                        "Taxa de Acerto": round(taxa, 1)
                    })
            
            if ranking:
                # Ordena pela maior taxa de acerto
                df_ranking = pd.DataFrame(ranking).sort_values(by="Taxa de Acerto", ascending=False)
                melhor = df_ranking.iloc[0]
                
                # --- EXIBIÇÃO PRINCIPAL ---
                st.success(f"### ✨ Melhor Performance Encontrada: {ativo}")
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Melhor GAP de Entrada", f"{melhor['GAP (%)']}%")
                c2.metric("Taxa de Acerto", f"{melhor['Taxa de Acerto']}%")
                c3.metric("Amostragem", f"{int(melhor['Ocorrências'])} dias")

                # --- NOVA SEÇÃO: SUGESTÕES ADICIONAIS ---
                st.markdown("---")
                st.subheader("📋 Outras Sugestões de Entrada para este Ativo")
                st.write(f"Considerando um alvo de **{alvo_gain}%**, estas foram as melhores variações encontradas:")
                
                # Mostra o Top 5 sugestões formatado
                st.table(df_ranking.head(5)[['Sugestão', 'Ocorrências', 'Taxa de Acerto']])

                # Gráfico de Probabilidade
                fig = px.bar(df_ranking.sort_values(by="GAP (%)", ascending=False), 
                            x="GAP (%)", y="Taxa de Acerto", 
                            title="Probabilidade de Acerto por Nível de GAP",
                            color="Taxa de Acerto", color_continuous_scale="Viridis")
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.warning("Não encontramos ocorrências suficientes (mínimo 5) para gerar sugestões seguras.")
        else:
            st.error("Erro ao buscar dados do ativo.")
