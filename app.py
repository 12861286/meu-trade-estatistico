import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. Configuração de layout
st.set_page_config(page_title="Scanner Quant B3", layout="wide")

st.title("🔍 Scanner de Estatística de Abertura")

# --- LISTA DE ATIVOS ---
@st.cache_data
def carregar_lista_ativos():
    ibov = ["PETR4", "VALE3", "ITUB4", "BBDC4", "BBAS3", "ABEV3", "MGLU3", "PRIO3", "WEGE3", "RENT3", "GGBR4", "CSNA3"]
    return sorted([f"{a}.SA" for a in ibov])

# --- FUNÇÃO DO GAP DE HOJE ---
def obter_gap_hoje(ticker):
    try:
        dados = yf.download(ticker, period="2d", progress=False)
        if len(dados) < 2: return 0.0
        fechamento_ontem = float(dados['Close'].iloc[-2])
        abertura_hoje = float(dados['Open'].iloc[-1])
        return round(((abertura_hoje / fechamento_ontem) - 1) * 100, 2)
    except: return 0.0

# --- BARRA LATERAL ---
st.sidebar.header("Configurações do Backtest")
lista_ativos = carregar_lista_ativos()
ativo = st.sidebar.selectbox("Selecione o Ativo:", lista_ativos)
data_inicio = st.sidebar.date_input("Data de Início da Pesquisa:", datetime(2020, 1, 1))
gap_digitado = st.sidebar.number_input("Porcentagem do GAP desejada:", value=-1.0, step=0.1)

# --- CAIXA DE GAP REAL DE HOJE (COLORIDA) ---
gap_atual = obter_gap_hoje(ativo)
cor_caixa = "#d4edda" if gap_atual >= 0 else "#f8d7da"
texto_cor = "#155724" if gap_atual >= 0 else "#721c24"

st.sidebar.markdown(f"""
    <div style="background-color:{cor_caixa}; padding:15px; border-radius:10px; border:1px solid {texto_cor}; text-align:center;">
        <span style="color:{texto_cor}; font-weight:bold; font-size:14px;">GAP REAL DE HOJE</span><br>
        <span style="color:{texto_cor}; font-size:24px; font-weight:bold;">{gap_atual}%</span>
    </div>
    """, unsafe_allow_html=True)

# --- PROCESSAMENTO ---
if st.sidebar.button('Rodar Estatística'):
    with st.spinner('Consultando histórico...'):
        df = yf.download(ativo, start=data_inicio, progress=False)
        
        if not df.empty:
            df = df[['Open', 'High', 'Low', 'Close']].copy()
            df.columns = ['Abertura', 'Maxima', 'Minima', 'Fechamento']
            
            df['Gap'] = ((df['Abertura'] / df['Fechamento'].shift(1)) - 1) * 100
            df['Max_Apos_Abertura'] = ((df['Maxima'] / df['Abertura']) - 1) * 100
            df['Queda_Apos_Abertura'] = ((df['Minima'] / df['Abertura']) - 1) * 100
            
            eventos = df[(df['Gap'] <= gap_digitado + 0.1) & (df['Gap'] >= gap_digitado - 0.1)].copy()
            
            if len(eventos) >= 3:
                # Melhor Alvo e Acerto
                melhor_y, melhor_x = 0, 0
                for alvo_t in [x * 0.1 for x in range(1, 41)]:
                    taxa = (len(eventos[eventos['Max_Apos_Abertura'] >= alvo_t]) / len(eventos)) * 100
                    if taxa >= 70: 
                        melhor_y, melhor_x = round(alvo_t, 2), round(taxa, 1)
                
                if melhor_y == 0: melhor_y, melhor_x = 0.5, round((len(eventos[eventos['Max_Apos_Abertura'] >= 0.5]) / len(eventos)) * 100, 1)
                
                queda_media = eventos['Queda_Apos_Abertura'].mean()

                st.success(f"### Resultado da Pesquisa para {ativo}")
                st.subheader(f"Neste período, sempre que o ativo abriu com o GAP de {gap_digitado}%, ele acertou {melhor_x}% das vezes a porcentagem de {melhor_y}%, que foi a melhor performance dele.")
                
                st.warning(f"💡 **Para o analista saber seu ponto de stop:** Para atingir esta estatística, o ativo teve uma queda média de **{queda_media:.2f}%**.")

                col1, col2, col3 = st.columns(3)
                col1.metric("Ocorrências", f"{len(eventos)} dias")
                col2.metric("Taxa de Acerto", f"{melhor_x}%")
                col3.metric("Máxima Média", f"{eventos['Max_Apos_Abertura'].mean():.2f}%")
                
                # --- TABELA DE SUGESTÕES (AGORA DE +5 A -5) ---
                st.markdown("---")
                st.subheader("📋 Sugestões Adicionais (Range: +5% a -5%)")
                ranking = []
                # Loop para testar de 5.0 positivo até -5.0 negativo
                for val in [x * 0.5 for x in range(-10, 11)]:
                    t_gap = round(val, 2)
                    ev_r = df[(df['Gap'] <= t_gap + 0.2) & (df['Gap'] >= t_gap - 0.2)]
                    if len(ev_r) >= 5:
                        ranking.append({
                            "Faixa de GAP": f"Próximo a {t_gap}%",
                            "Dias": len(ev_r),
                            "Acerto (Alvo 1%)": f"{round((len(ev_r[ev_r['Max_Apos_Abertura'] >= 1.0]) / len(ev_r)) * 100, 1)}%",
                            "Risco Médio (Stop)": f"{round(ev_r['Queda_Apos_Abertura'].mean(), 2)}%"
                        })
                if ranking:
                    st.table(pd.DataFrame(ranking).sort_values(by="Faixa de GAP", ascending=False))

                # --- GRÁFICO EM LINHA NO FINAL ---
                st.markdown("---")
                st.subheader(f"📈 Histórico de Performance em Linha (GAP {gap_digitado}%)")
                eventos = eventos.sort_index()
                fig = px.line(eventos, y="Max_Apos_Abertura", 
                             title="Evolução das máximas atingidas após este GAP ao longo do tempo",
                             labels={'Max_Apos_Abertura': 'Máxima atingida no dia (%)', 'Date': 'Data'},
                             markers=True)
                st.plotly_chart(fig, use_container_width=True)

            else:
                st.warning("Poucas ocorrências para este GAP específico.")
        else:
            st.error("Erro ao buscar dados.")
