import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 1. Configuração de layout
st.set_page_config(page_title="Scanner Quant B3", layout="wide")

st.title("🔍 Scanner de Estatística de Abertura")

@st.cache_data(ttl=3600) # Cache de 1 hora
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
    if len(df_eventos) < 3:
        return 0.0, 0.0
    
    melhor_y, melhor_x = 0, 0
    # Testa alvos de 0.1% a 4.0%
    for alvo_t in [x * 0.1 for x in range(1, 41)]:
        taxa = (len(df_eventos[df_eventos['Max_Apos_Abertura'] >= alvo_t]) / len(df_eventos)) * 100
        if taxa >= 70: 
            melhor_y, melhor_x = round(alvo_t, 2), round(taxa, 1)
    
    if melhor_y == 0: 
        melhor_y = 0.5
        melhor_x = round((len(df_eventos[df_eventos['Max_Apos_Abertura'] >= 0.5]) / len(df_eventos)) * 100, 1)
    return melhor_y, melhor_x

# --- BARRA LATERAL ---
st.sidebar.header("⚙️ Configurações")
lista_sugerida = carregar_lista_ativos()
ativo = st.sidebar.selectbox("Selecione o ativo:", lista_sugerida)
data_inicio = st.sidebar.date_input("Data de Início:", datetime(2020, 1, 1))
gap_digitado = st.sidebar.number_input("GAP desejado para análise (%):", value=-1.0, step=0.1)
filtro_radar = st.sidebar.slider("Mínimo de Acerto Radar (%):", 50, 95, 80)

rodar = st.sidebar.button('🚀 Rodar Scanner')

# --- DOWNLOAD DOS DADOS PARA O ATIVO PRINCIPAL ---
@st.cache_data
def get_data(ticker, start_date):
    df = yf.download(ticker, start=start_date, progress=False)
    if df.empty: return pd.DataFrame()
    # Limpeza de multi-index se houver
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    df = df[['Open', 'High', 'Low', 'Close']].copy()
    df.columns = ['Abertura', 'Maxima', 'Minima', 'Fechamento']
    
    # Cálculos Quant
    df['Gap'] = ((df['Abertura'] / df['Fechamento'].shift(1)) - 1) * 100
    df['Max_Apos_Abertura'] = ((df['Maxima'] / df['Abertura']) - 1) * 100
    df['Queda_Apos_Abertura'] = ((df['Minima'] / df['Abertura']) - 1) * 100
    df['Resultado_Fechamento'] = ((df['Fechamento'] / df['Abertura']) - 1) * 100
    return df.dropna()

if rodar:
    df_principal = get_data(ativo, data_inicio)
    
    if not df_principal.empty:
        # 1. Info do GAP de hoje
        gap_hoje = round(df_principal['Gap'].iloc[-1], 2)
        cor_caixa = "#d4edda" if gap_hoje >= 0 else "#f8d7da"
        st.markdown(f'<div style="background-color:{cor_caixa}; padding:20px; border-radius:10px; text-align:center; color: black; margin-bottom: 20px;">'
                    f'<h3>GAP Atual de {ativo}: {gap_hoje}%</h3></div>', unsafe_allow_html=True)

        # 2. Análise do GAP Específico
        eventos = df_principal[(df_principal['Gap'] <= gap_digitado + 0.2) & (df_principal['Gap'] >= gap_digitado - 0.2)].copy()
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"### Backtest: GAP {gap_digitado}%")
            if len(eventos) >= 3:
                alvo, taxa = calcular_melhor_performance(eventos)
                st.metric("Probabilidade de Alvo", f"{taxa}%", f"Alvo: {alvo}%")
                st.write(f"**Amostragem:** {len(eventos)} dias encontrados.")
            else:
                st.warning("Amostragem insuficiente para este GAP.")

        with col2:
            st.subheader("📊 Histórico de Máximas")
            fig = px.histogram(eventos, x="Max_Apos_Abertura", nbins=10, title="Distribuição de Máximas após este GAP")
            st.plotly_chart(fig, use_container_width=True)

        # 3. Radar de Elite (Otimizado)
        st.divider()
        st.subheader(f"🚀 Radar de Elite (Oportunidades com >{filtro_radar}% de acerto)")
        
        with st.spinner("Escaneando mercado..."):
            # Baixa os últimos 60 dias de todos para o radar (mais rápido que baixar 1 por 1)
            dados_radar = yf.download(lista_sugerida, period="60d", progress=False)
            oportunidades = []
            
            for t in lista_sugerida:
                try:
                    # Extrai dados do ticker específico do dataframe gigante
                    d_t = pd.DataFrame({
                        'Open': dados_radar['Open'][t],
                        'High': dados_radar['High'][t],
                        'Low': dados_radar['Low'][t],
                        'Close': dados_radar['Close'][t]
                    }).dropna()
                    
                    g_hoje = ((d_t['Open'].iloc[-1] / d_t['Close'].iloc[-2]) - 1) * 100
                    
                    # Backtest rápido no histórico do ativo principal (usando df de longo prazo se for o mesmo ativo)
                    # Para simplificar, compararemos apenas o GAP de hoje com a base histórica
                    df_hist = get_data(t, data_inicio)
                    f_r = df_hist[(df_hist['Gap'] <= g_hoje + 0.15) & (df_hist['Gap'] >= g_hoje - 0.15)]
                    
                    if len(f_r) >= 5:
                        yr, xr = calcular_melhor_performance(f_r)
                        if xr >= filtro_radar:
                            oportunidades.append({"Ativo": t, "GAP Hoje": f"{g_hoje:.2f}%", "Acerto": f"{xr}%", "Alvo Sugerido": f"{yr}%", "Dias": len(f_r)})
                except:
                    continue
            
            if oportunidades:
                st.dataframe(pd.DataFrame(oportunidades), use_container_width=True)
            else:
                st.write("Nenhuma oportunidade filtrada nos parâmetros atuais.")
