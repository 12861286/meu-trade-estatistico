import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Scanner Quant Profissional", layout="wide")

st.title("🚀 Scanner de Otimização Quantitativa")

# --- LISTA DE ATIVOS ---
@st.cache_data
def carregar_lista_ativos():
    # Você pode adicionar qualquer ticker da B3 aqui
    base = ["PETR4", "VALE3", "ITUB4", "BBDC4", "BBAS3", "ABEV3", "MGLU3", "PRIO3", "WEGE3", "RENT3"]
    return [f"{a}.SA" for a in base]

# --- SIDEBAR ---
st.sidebar.header("Parâmetros do Robô")
ativo = st.sidebar.selectbox("Escolha o Ativo:", carregar_lista_ativos())
data_inicio = st.sidebar.date_input("Pesquisar desde:", datetime(2021, 1, 1))
alvo_gain = st.sidebar.number_input("Alvo de Saída (% de lucro):", value=1.0, step=0.1)

if st.sidebar.button('Encontrar Melhor Entrada'):
    with st.spinner('Calculando probabilidades...'):
        df = yf.download(ativo, start=data_inicio, progress=False)
        
        if not df.empty:
            df = df[['Open', 'High', 'Low', 'Close']].copy()
            df.columns = ['Abertura', 'Maxima', 'Minima', 'Fechamento']
            df['Gap'] = ((df['Abertura'] / df['Fechamento'].shift(1)) - 1) * 100
            # Verifica se atingiu o alvo de lucro durante o dia
            df['Atingiu_Alvo'] = ((df['Maxima'] / df['Abertura']) - 1) * 100 >= alvo_gain
            
            # --- LÓGICA DE OTIMIZAÇÃO ---
            resultados_otimizacao = []
            # Testa gaps de -0.5% até -5.0%
            for teste_gap in [x * -0.5 for x in range(1, 11)]:
                eventos = df[df['Gap'] <= teste_gap]
                if len(eventos) >= 5: # Mínimo de 5 ocorrências para ser estatística
                    acertos = len(eventos[eventos['Atingiu_Alvo'] == True])
                    taxa = (acertos / len(eventos)) * 100
                    resultados_otimizacao.append({
                        "GAP de Entrada": teste_gap,
                        "Ocorrências": len(eventos),
                        "Taxa de Acerto": taxa
                    })
            
            if resultados_otimizacao:
                df_otimizado = pd.DataFrame(resultados_otimizacao)
                melhor_estratégia = df_otimizado.sort_values(by="Taxa de Acerto", ascending=False).iloc[0]
                
                # --- EXIBIÇÃO ---
                st.success(f"### ✨ Melhor Entrada Encontrada para {ativo}")
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Melhor GAP de Entrada", f"{melhor_estratégia['GAP de Entrada']}%")
                c2.metric("Taxa de Acerto", f"{melhor_estratégia['Taxa de Acerto']:.1f}%")
                c3.metric("Frequência (Dias)", int(melhor_estratégia['Ocorrências']))

                st.info(f"💡 **Conclusão:** Sempre que o ativo {ativo} abriu com GAP de {melhor_estratégia['GAP de Entrada']}% ou mais, ele buscou o seu alvo de {alvo_gain}% em {melhor_estratégia['Taxa de Acerto']:.1f}% das vezes.")

                # Gráfico de Otimização
                fig = px.line(df_otimizado, x="GAP de Entrada", y="Taxa de Acerto", 
                             title="Probabilidade por Nível de GAP", markers=True)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Dados insuficientes para encontrar um padrão estatístico.")
        else:
            st.error("Erro ao carregar dados.")
