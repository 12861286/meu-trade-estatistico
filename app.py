import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. Configuração de layout
st.set_page_config(page_title="Scanner Quant B3", layout="wide")

st.title("🔍 Scanner de Estatística de Abertura")

# --- LISTA EXTENSA DE AÇÕES B3 ---
@st.cache_data
def carregar_lista_ativos():
    acoes = [
        "RRRP3.SA", "ALOS3.SA", "ALPA4.SA", "ABEV3.SA", "ARZZ3.SA", "ASAI3.SA", "AZUL4.SA", "B3SA3.SA", 
        "BBAS3.SA", "BBDC3.SA", "BBDC4.SA", "BBSE3.SA", "BEEF3.SA", "BPAC11.SA", "BRAP4.SA", "BRFS3.SA", 
        "BRKM5.SA", "CCRO3.SA", "CIEL3.SA", "CMIG4.SA", "CMIN3.SA", "COGN3.SA", "CPFE3.SA", 
        "CPLE6.SA", "CRFB3.SA", "CSAN3.SA", "CSNA3.SA", "CVCB3.SA", "CYRE3.SA", "DXCO3.SA", "ECOR3.SA", 
        "EGIE3.SA", "ELET3.SA", "ELET6.SA", "EMBR3.SA", "ENEV3.SA", "ENGI11.SA", "EQTL3.SA", "EZTC3.SA", 
        "FLRY3.SA", "GGBR4.SA", "GOAU4.SA", "GOLL4.SA", "HAPV3.SA", "HYPE3.SA", "IGTI11.SA", "IRBR3.SA", 
        "ITSA4.SA", "ITUB4.SA", "JBSS3.SA", "KLBN11.SA", "LREN3.SA", "LWSA3.SA", "MGLU3.SA", "MRFG3.SA", 
        "MRVE3.SA", "MULT3.SA", "NTCO3.SA", "PCAR3.SA", "PETR3.SA", "PETR4.SA", "PRIO3.SA", "PSSA3.SA", 
        "RADL3.SA", "RAIL3.SA", "RAIZ4.SA", "RENT3.SA", "SANB11.SA", "SBSP3.SA", "SLCE3.SA", "SMTO3.SA", 
        "SOMA3.SA", "SUZB3.SA", "TAEE11.SA", "TIMS3.SA", "TOTS3.SA", "TRPL4.SA", "UGPA3.SA", "USIM5.SA", 
        "VALE3.SA", "VAMO3.SA", "VBBR3.SA", "VIVA3.SA", "VIVT3.SA", "WEGE3.SA", "YDUQ3.SA"
    ]
    return sorted(list(set(acoes)))

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
lista_sugerida = carregar_lista_ativos()
ativo = st.sidebar.selectbox("Selecione ou DIGITE a ação:", lista_sugerida)
data_inicio = st.sidebar.date_input("Data de Início:", datetime(2020, 1, 1))
gap_digitado = st.sidebar.number_input("GAP desejado (%):", value=-1.0, step=0.1)
filtro_radar = st.sidebar.number_input("Mínimo de Acerto Radar (%):", value=80, step=5)

# BOTÕES
rodar = st.sidebar.button('🚀 Rodar Estatística e Radar')
rodar_ontem = st.sidebar.button('⏪ Ver Resultado de Ontem')

# --- LOGICA DE PROCESSAMENTO ---
if rodar or rodar_ontem:
    with st.spinner('Processando dados...'):
        # Download do histórico
        df = yf.download(ativo, start=data_inicio, progress=False)
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        df = df[['Open', 'High', 'Low', 'Close']].copy()
        df.columns = ['Abertura', 'Maxima', 'Minima', 'Fechamento']
        df['Gap'] = ((df['Abertura'] / df['Fechamento'].shift(1)) - 1) * 100
        df['Max_Apos_Abertura'] = ((df['Maxima'] / df['Abertura']) - 1) * 100
        df['Resultado_Fechamento'] = ((df['Fechamento'] / df['Abertura']) - 1) * 100
        df = df.dropna()

        # SE CLICOU EM RODAR HOJE
        if rodar:
            eventos = df[(df['Gap'] <= gap_digitado + 0.15) & (df['Gap'] >= gap_digitado - 0.15)].copy()
            st.success(f"### 🎯 GAP Digitado: {gap_digitado}% | Ativo: {ativo}")
            if len(eventos) >= 3:
                y, x = calcular_melhor_performance(eventos)
                st.subheader(f"Probabilidade de {x}% para atingir {y}% de alvo.")
                st.write(f"Médias do dia: Máxima {eventos['Max_Apos_Abertura'].mean():.2f}%")
            
            # Radar Hoje
            st.markdown("---")
            st.subheader(f"🚀 Radar de Elite Hoje (> {filtro_radar}% Acerto)")
            dados_radar = yf.download(lista_sugerida, period="5d", progress=False)
            radar_lista = []
            for t in lista_sugerida:
                try:
                    p_h = dados_radar['Open'][t].iloc[-1]
                    p_f = dados_radar['Close'][t].iloc[-2]
                    g_h = round(((p_h / p_f) - 1) * 100, 2)
                    # Filtro rápido no histórico do ativo principal ou download se for outro
                    # (Para velocidade, aqui usamos o download direto)
                    df_r = yf.download(t, start=data_inicio, progress=False)
                    df_r.columns = [c[0] if isinstance(c, tuple) else c for c in df_r.columns]
                    df_r['G'] = ((df_r['Open'] / df_r['Close'].shift(1)) - 1) * 100
                    df_r['Max_Apos_Abertura'] = ((df_r['High'] / df_r['Open']) - 1) * 100
                    f_r = df_r[(df_r['G'] <= g_h + 0.15) & (df_r['G'] >= g_h - 0.15)]
                    if len(f_r) >= 5:
                        yr, xr = calcular_melhor_performance(f_r)
                        if xr >= filtro_radar:
                            radar_lista.append({"Ativo": t, "GAP": f"{g_h}%", "Acerto": f"{xr}%", "Alvo": f"{yr}%"})
                except: continue
            if radar_lista: st.table(pd.DataFrame(radar_lista))
            else: st.write("Nenhuma oportunidade para o GAP de hoje.")

        # SE CLICOU EM RODAR ONTEM
        if rodar_ontem:
            st.markdown("---")
            # Identifica os dados de ontem
            gap_ontem = round(df['Gap'].iloc[-1], 2)
            max_ontem = round(df['Max_Apos_Abertura'].iloc[-1], 2)
            data_ontem = df.index[-1].strftime('%d/%m/%Y')
            
            # Faz o backtest histórico para o GAP que aconteceu ontem
            eventos_o = df.iloc[:-1] # Remove o dia de hoje para não viciar o backtest
            eventos_o = eventos_o[(eventos_o['Gap'] <= gap_ontem + 0.15) & (eventos_o['Gap'] >= gap_ontem - 0.15)]
            
            st.info(f"### ⏪ Resultado de Ontem ({data_ontem}) | Ativo: {ativo}")
            st.write(f"**GAP de Abertura:** {gap_ontem}% | **Máxima do Dia:** {max_ontem}%")
            
            if len(eventos_o) >= 3:
                y_o, x_o = calcular_melhor_performance(eventos_o)
                st.subheader(f"Estatística p/ este GAP: {x_o}% de chance para buscar {y_o}%")
                
                # VERIFICAÇÃO DE ACERTO
                if max_ontem >= y_o:
                    st.success(f"✅ **ACERTOU!** A máxima de ontem ({max_ontem}%) atingiu o alvo estatístico de {y_o}%.")
                else:
                    st.error(f"❌ **FALHOU!** A máxima de ontem ({max_ontem}%) não atingiu o alvo estatístico de {y_o}%.")
            else:
                st.warning("Pouca amostragem histórica para o GAP de ontem.")

        # GRÁFICO (Sempre mostra o histórico do ativo selecionado)
        st.markdown("---")
        st.subheader(f"📊 Histórico de Máximas - {ativo}")
        fig = px.bar(df.sort_index(), y="Max_Apos_Abertura", color_discrete_sequence=['#3366CC'])
        st.plotly_chart(fig, use_container_width=True)
