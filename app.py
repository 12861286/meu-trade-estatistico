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

# --- FUNÇÃO PARA CALCULAR MELHOR PERFORMANCE (Y em X%) ---
def calcular_melhor_performance(df_eventos):
    melhor_y, melhor_x = 0, 0
    if len(df_eventos) >= 3:
        for alvo_t in [x * 0.1 for x in range(1, 41)]:
            taxa = (len(df_eventos[df_eventos['Max_Apos_Abertura'] >= alvo_t]) / len(df_eventos)) * 100
            if taxa >= 70: 
                melhor_y, melhor_x = round(alvo_t, 2), round(taxa, 1)
        if melhor_y == 0: 
            melhor_y = 0.5
            melhor_x = round((len(df_eventos[df_eventos['Max_Apos_Abertura'] >= 0.5]) / len(df_eventos)) * 100, 1)
    return melhor_y, melhor_x

# --- BARRA LATERAL ---
st.sidebar.header("Configurações do Backtest")
lista_ativos = carregar_lista_ativos()
ativo = st.sidebar.selectbox("Selecione o Ativo:", lista_ativos)
data_inicio = st.sidebar.date_input("Data de Início da Pesquisa:", datetime(2020, 1, 1))
gap_digitado = st.sidebar.number_input("Porcentagem do GAP desejada:", value=-1.0, step=0.1)
filtro_radar = st.sidebar.number_input("Mínimo de Acerto para o Radar (%):", value=80, step=5)

rodar = st.sidebar.button('🚀 Rodar Estatística e Radar')

# --- CAIXA DE GAP REAL DE HOJE ---
gap_atual = obter_gap_hoje(ativo)
cor_caixa = "#d4edda" if gap_atual >= 0 else "#f8d7da"
texto_cor = "#155724" if gap_atual >= 0 else "#721c24"

st.sidebar.markdown(f"""
    <div style="background-color:{cor_caixa}; padding:5px 10px; border-radius:8px; border:1px solid {texto_cor}; text-align:center; margin-top:10px;">
        <span style="color:{texto_cor}; font-weight:bold; font-size:12px;">GAP REAL HOJE: {gap_atual}%</span>
    </div>
    """, unsafe_allow_html=True)

# --- PROCESSAMENTO ---
if rodar:
    with st.spinner('Consultando histórico...'):
        df = yf.download(ativo, start=data_inicio, progress=False)
        
        if not df.empty:
            df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
            df = df[['Open', 'High', 'Low', 'Close']].copy()
            df.columns = ['Abertura', 'Maxima', 'Minima', 'Fechamento']
            df['Gap'] = ((df['Abertura'] / df['Fechamento'].shift(1)) - 1) * 100
            df['Max_Apos_Abertura'] = ((df['Maxima'] / df['Abertura']) - 1) * 100
            df['Queda_Apos_Abertura'] = ((df['Minima'] / df['Abertura']) - 1) * 100
            
            # --- ANÁLISE 1: GAP DIGITADO ---
            eventos_digitados = df[(df['Gap'] <= gap_digitado + 0.1) & (df['Gap'] >= gap_digitado - 0.1)].copy()
            st.success(f"### 🎯 Resultado para o GAP Digitado ({gap_digitado}%)")
            if len(eventos_digitados) >= 3:
                y_dig, x_dig = calcular_melhor_performance(eventos_digitados)
                st.subheader(f"Neste período, sempre que o ativo abriu com o GAP de {gap_digitado}%, ele acertou {x_dig}% das vezes a porcentagem de {y_dig}%, que foi a melhor performance dele.")
                st.warning(f"💡 **Ponto de Stop:** Queda média de **{eventos_digitados['Queda_Apos_Abertura'].mean():.2f}%**.")

            # --- ANÁLISE 2: GAP DE HOJE ---
            st.markdown("---")
            st.info(f"### 🕒 Análise Baseada na Abertura de HOJE ({gap_atual}%)")
            eventos_hoje = df[(df['Gap'] <= gap_atual + 0.1) & (df['Gap'] >= gap_atual - 0.1)].copy()
            if len(eventos_hoje) >= 3:
                y_hoje, x_hoje = calcular_melhor_performance(eventos_hoje)
                st.subheader(f"Com este gap da abertura de hoje ({gap_atual}%), o ativo teve sua melhor performance de acerto a {y_hoje}% em {x_hoje}% das vezes.")

            # --- SUGESTÕES ADICIONAIS (COLUNAS NOVAS) ---
            st.markdown("---")
            st.subheader("📋 Sugestões Adicionais (Range: +5% a -5%)")
            ranking = []
            for val in [x * 0.5 for x in range(-10, 11)]:
                t_gap = round(val, 2)
                ev_r = df[(df['Gap'] <= t_gap + 0.2) & (df['Gap'] >= t_gap - 0.2)]
                if len(ev_r) >= 4:
                    y_r, x_r = calcular_melhor_performance(ev_r)
                    ranking.append({
                        "Faixa de GAP": f"Próximo a {t_gap}%",
                        "Dias": len(ev_r),
                        "Melhor Porcentagem (Alvo)": f"{y_r}%",
                        "Acerto Histórico": f"{x_r}%",
                        "Stop Médio": f"{round(ev_r['Queda_Apos_Abertura'].mean(), 2)}%"
                    })
            if ranking:
                st.table(pd.DataFrame(ranking).sort_values(by="Faixa de GAP", ascending=False))

            # --- RADAR DE OPORTUNIDADES (MOVIDO PARA O FINAL) ---
            st.markdown("---")
            st.subheader(f"🚀 Radar de Oportunidades (Acerto > {filtro_radar}%)")
            radar_oportunidades = []
            for ticker in lista_ativos:
                try:
                    d_radar = yf.download(ticker, period="max", progress=False)
                    d_radar.columns = [c[0] if isinstance(c, tuple) else c for c in d_radar.columns]
                    g_h = round(((float(d_radar['Open'].iloc[-1]) / float(d_radar['Close'].iloc[-2])) - 1) * 100, 2)
                    d_radar['Gap_Hist'] = ((d_radar['Open'] / d_radar['Close'].shift(1)) - 1) * 100
                    d_radar['Max_Apos_Abertura'] = ((d_radar['High'] / d_radar['Open']) - 1) * 100
                    d_radar['Queda_Apos_Abertura'] = ((d_radar['Low'] / d_radar['Open']) - 1) * 100
                    f_radar = d_radar[(d_radar['Gap_Hist'] <= g_h + 0.1) & (d_radar['Gap_Hist'] >= g_h - 0.1)]
                    if len(f_radar) >= 5:
                        yr, xr = calcular_melhor_performance(f_radar)
                        if xr >= filtro_radar:
                            radar_oportunidades.append({"Ativo": ticker, "GAP Hoje": f"{g_h}%", "Acerto": f"{xr}%", "Alvo": f"{yr}%", "Stop": f"{round(f_radar['Queda_Apos_Abertura'].mean(), 2)}%"})
                except: continue
            if radar_oportunidades: st.table(pd.DataFrame(radar_oportunidades))
            else: st.write("Sem ativos de elite hoje.")

            # --- GRÁFICO FINAL ---
            st.markdown("---")
            st.subheader("📈 Histórico de Performance")
            fig = px.line(eventos_digitados.sort_index(), y="Max_Apos_Abertura", markers=True)
            st.plotly_chart(fig, use_container_width=True)
