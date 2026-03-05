import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz

# Configuração da página
st.set_page_config(page_title="Caçador de Performance B3", layout="wide")

st.title("🎯 Analisador de GAP e Sugestões de Performance")

# --- LISTA AMPLIADA DE ATIVOS (QUASE TODA A B3) ---
@st.cache_data
def carregar_lista_ativos():
    ibov = [
        "RRRP3", "ALOS3", "ALPA4", "ABEV3", "ARZZ3", "ASAI3", "AZUL4", "B3SA3", 
        "BBAS3", "BBDC3", "BBDC4", "BBSE3", "BEEF3", "BPAC11", "BRAP4", "BRFS3", 
        "BRKM5", "CCRO3", "CIEL3", "CMIG4", "CMIN3", "COGN3", "CPFE3", 
        "CPLE6", "CRFB3", "CSAN3", "CSNA3", "CVCB3", "CYRE3", "DXCO3", "ELET3", 
        "ELET6", "EMBR3", "ENGI11", "ENEV3", "EGIE3", "EQTL3", "EZTC3", "FLRY3", 
        "GGBR4", "GOAU4", "GOLL4", "HAPV3", "HYPE3", "ITSA4", "ITUB4", "JBSS3", 
        "KLBN11", "LREN3", "LWSA3", "MGLU3", "MRFG3", "MRVE3", "MULT3", "NTCO3", 
        "PETR3", "PETR4", "PRIO3", "PSSA3", "RADL3", "RAIZ4", "RENT3", "RAIL3", 
        "RDOR3", "SANB11", "SBSP3", "SUZB3", "TAEE11", "TIMS3", "TOTS3", "UGPA3", 
        "USIM5", "VALE3", "VBBR3", "VIVT3", "WEGE3", "YDUQ3"
    ]
    return sorted([f"{a}.SA" for a in ibov])

# --- FUNÇÃO PARA O GAP ATUAL ---
def obter_gap_hoje(ticker):
    try:
        # Puxa os últimos 2 dias para comparar
        dados = yf.download(ticker, period="2d", progress=False)
        if len(dados) < 2:
            return 0.0, "Dados insuficientes"
        
        fechamento_ontem = dados['Close'].iloc[-2]
        abertura_hoje = dados['Open'].iloc[-1]
        
        # Verifica se a data da última linha é hoje
        tz_br = pytz.timezone('America/Sao_Paulo')
        hoje = datetime.now(tz_br).date()
        data_dados = dados.index[-1].date()
        
        if data_dados == hoje:
            gap = ((abertura_hoje / fechamento_ontem) - 1) * 100
            return round(gap, 2), "Aberto"
        else:
            return 0.0, "Mercado Fechado"
    except:
        return 0.0, "Erro"

# --- BARRA LATERAL ---
st.sidebar.header("Configuração")
lista_completa = carregar_lista_ativos()
ativo = st.sidebar.selectbox("Escolha ou Digite o Ativo:", lista_completa, index=lista_completa.index("PETR4.SA"))
data_inicio = st.sidebar.date_input("Analisar desde:", datetime(2021, 1, 1))
gap_digitado = st.sidebar.number_input("Digite o GAP para análise principal (%):", value=-1.0, step=0.1)

# --- MONITOR EM TEMPO REAL (NOVO) ---
gap_atual, status_mercado = obter_gap_hoje(ativo)
st.sidebar.markdown("---")
st.sidebar.subheader("🕒 GAP de Hoje")
if status_mercado == "Aberto":
    cor = "green" if gap_atual >= 0 else "red"
    st.sidebar.markdown(f"<h2 style='color:{cor};'>{gap_atual}%</h2>", unsafe_allow_html=True)
else:
    st.sidebar.info(f"Status: {status_mercado}")

# --- BOTÃO DE EXECUÇÃO ---
if st.sidebar.button('Gerar Relatório Completo'):
    with st.spinner(f'Analisando {ativo}...'):
        df = yf.download(ativo, start=data_inicio, progress=False)
        
        if not df.empty:
            df = df[['Open', 'High', 'Low', 'Close']].copy()
            df.columns = ['Abertura', 'Maxima', 'Minima', 'Fechamento']
            df['Gap_Real'] = ((df['Abertura'] / df['Fechamento'].shift(1)) - 1) * 100
            df['Subida_Max'] = ((df['Maxima'] / df['Abertura']) - 1) * 100
            
            eventos_fixos = df[(df['Gap_Real'] <= gap_digitado + 0.05) & (df['Gap_Real'] >= gap_digitado - 0.05)].copy()
            
            if len(eventos_fixos) >= 3:
                melhor_y, melhor_x = 0, 0
                for alvo_teste in [x * 0.1 for x in range(1, 41)]:
                    taxa = (len(eventos_fixos[eventos_fixos['Subida_Max'] >= alvo_teste]) / len(eventos_fixos)) * 100
                    if taxa >= 70: 
                        melhor_y, melhor_x = round(alvo_teste, 2), round(taxa, 1)
                
                if melhor_y == 0: 
                    melhor_y = 0.5
                    melhor_x = round((len(eventos_fixos[eventos_fixos['Subida_Max'] >= 0.5]) / len(eventos_fixos)) * 100, 1)

                st.success(f"### ✨ Resultado da Pesquisa para {ativo}")
                st.subheader(f"Neste período, sempre que o ativo abriu com o GAP de {gap_digitado}%, ele acertou {melhor_x}% das vezes a porcentagem de {melhor_y}%, que foi a melhor performance dele.")
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Ocorrências deste GAP", f"{len(eventos_fixos)} dias")
                c2.metric("Subida Média Real", f"{eventos_fixos['Subida_Max'].mean():.2f}%")
                c3.metric("GAP de Hoje", f"{gap_atual}%" if status_mercado == "Aberto" else "---")
            else:
                st.warning("Poucas ocorrências para este GAP específico.")

            st.markdown("---")
            st.subheader("📋 Sugestões Adicionais")
            ranking = []
            for i in range(1, 16):
                teste_gap = round(i * -0.3, 2)
                eventos_rank = df[df['Gap_Real'] <= teste_gap].copy()
                if len(eventos_rank) >= 5:
                    taxa_padrao = (len(eventos_rank[eventos_rank['Subida_Max'] >= 1.0]) / len(eventos_rank)) * 100
                    ranking.append({
                        "Sugestão": f"GAP abaixo de {teste_gap}%",
                        "Dias": len(eventos_rank),
                        "Acerto (Alvo 1%)": f"{round(taxa_padrao, 1)}%",
                        "Subida Média Real": f"{round(eventos_rank['Subida_Max'].mean(), 2)}%"
                    })
            
            if ranking:
                st.table(pd.DataFrame(ranking).sort_values(by="Acerto (Alvo 1%)", ascending=False))
            
            fig = px.histogram(df[df['Gap_Real'] < 0], x="Subida_Max", title="Frequência de Altas (GAPs de Baixa)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Erro ao carregar dados.")
