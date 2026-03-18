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

# --- FUNÇÃO DO GAP DE HOJE ---
def obter_gap_hoje(ticker):
    try:
        dados = yf.download(ticker, period="2d", progress=False)
        if len(dados) < 2: return 0.0
        dados.columns = [c[0] if isinstance(c, tuple) else c for c in dados.columns]
        fechamento_ontem = float(dados['Close'].iloc[-2])
        abertura_hoje = float(dados['Open'].iloc[-1])
        return round(((abertura_hoje / fechamento_ontem) - 1) * 100, 2)
    except: return 0.0

# --- FUNÇÃO PARA CALCULAR MELHOR PERFORMANCE ---
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

# --- BOTÕES ---
rodar = st.sidebar.button('🚀 Rodar Estatística e Radar')
conferir_ontem = st.sidebar.button('⏪ Conferir Resultado de Ontem')

# --- CAIXA DE GAP REAL ---
gap_atual = obter_gap_hoje(ativo)
cor_caixa = "#d4edda" if gap_atual >= 0 else "#f8d7da"
st.sidebar.markdown(f'<div style="background-color:{cor_caixa}; padding:10px; border-radius:10px; text-align:center; color: black;"><b>GAP HOJE: {gap_atual}%</b></div>', unsafe_allow_html=True)

# --- PROCESSAMENTO ---
if rodar or conferir_ontem:
    with st.spinner(f'Processando {ativo}...'):
        df = yf.download(ativo, start=data_inicio, progress=False)
        
        if not df.empty and len(df) > 10:
            df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
            df = df[['Open', 'High', 'Low', 'Close']].copy()
            df.columns = ['Abertura', 'Maxima', 'Minima', 'Fechamento']
            
            df['Gap'] = ((df['Abertura'] / df['Fechamento'].shift(1)) - 1) * 100
            df['Max_Apos_Abertura'] = ((df['Maxima'] / df['Abertura']) - 1) * 100
            df['Queda_Apos_Abertura'] = ((df['Minima'] / df['Abertura']) - 1) * 100
            df['Resultado_Fechamento'] = ((df['Fechamento'] / df['Abertura']) - 1) * 100
            df = df.dropna()

            # --- BLOCO EXCLUSIVO PARA CONFERIR O RESULTADO DE ONTEM ---
            if conferir_ontem:
                st.markdown("---")
                ultimo_gap = round(df['Gap'].iloc[-1], 2)
                ultima_max = round(df['Max_Apos_Abertura'].iloc[-1], 2)
                data_ontem = df.index[-1].strftime('%d/%m/%Y')
                
                historico = df.iloc[:-1]
                eventos_ontem = historico[(historico['Gap'] <= ultimo_gap + 0.15) & (historico['Gap'] >= ultimo_gap - 0.15)].copy()
                
                st.info(f"### 📊 Resultado do Ativo no Último Pregão ({data_ontem})")
                col1, col2 = st.columns(2)
                col1.metric("GAP de Abertura", f"{ultimo_gap}%")
                col2.metric("Máxima Atingida", f"{ultima_max}%")
                
                if len(eventos_ontem) >= 3:
                    y_o, x_o = calcular_melhor_performance(eventos_ontem)
                    st.write(f"**Estatística Esperada:** {x_o}% de chance para buscar {y_o}% de alvo.")
                    
                    if ultima_max >= y_o:
                        st.success(f"✅ **BATEU O ALVO!** O ativo superou a estatística de {y_o}%.")
                    else:
                        st.error(f"❌ **NÃO BATEU.** O ativo ficou abaixo do esperado de {y_o}%.")
                else:
                    st.warning("Histórico insuficiente para calcular estatística deste GAP específico.")

            # --- BLOCO ORIGINAL DO BOTÃO RODAR ---
            if rodar:
                eventos_digitados = df[(df['Gap'] <= gap_digitado + 0.15) & (df['Gap'] >= gap_digitado - 0.15)].copy()
                st.success(f"### 🎯 GAP Digitado: {gap_digitado}% | Ativo: {ativo}")
                
                if len(eventos_digitados) >= 3:
                    y_dig, x_dig = calcular_melhor_performance(eventos_digitados)
                    st.subheader(f"Probabilidade de {x_dig}% para atingir {y_dig}% de alvo.")
                    
                    # Correção: Fechamento Positivo e Negativo
                    qtd_pos = len(eventos_digitados[eventos_digitados['Resultado_Fechamento'] > 0])
                    perc_pos = round((qtd_pos / len(eventos_digitados)) * 100, 1)
                    perc_neg = round(100 - perc_pos, 1)
                    st.write(f"**Fechamento:** Positivo {perc_pos}% | Negativo {perc_neg}%")
                    
                    # Correção: Médias do dia Máxima e Mínima
                    media_max = eventos_digitados['Max_Apos_Abertura'].mean()
                    media_min = eventos_digitados['Queda_Apos_Abertura'].mean()
                    st.write(f"**Médias do dia:** Máxima {media_max:.2f}% | Mínima {media_min:.2f}%")

                # --- MAPA DE GAPS ---
                st.markdown("---")
                st.subheader("📋 Mapa de GAPs (+5% a -5%)")
                ranking = []
                for val in [x * 0.5 for x in range(-10, 11)]:
                    t_gap = round(val, 2)
                    ev_r = df[(df['Gap'] <= t_gap + 0.2) & (df['Gap'] >= t_gap - 0.2)]
                    if len(ev_r) >= 4:
                        y_r, x_r = calcular_melhor_performance(ev_r)
                        # Inclusão da coluna Mínima Média
                        ranking.append({
                            "GAP": f"{t_gap}%", 
                            "Dias": len(ev_r), 
                            "Alvo": f"{y_r}%", 
                            "Acerto": f"{x_r}%", 
                            "Máx Média": f"{round(ev_r['Max_Apos_Abertura'].mean(), 2)}%",
                            "Mín Média": f"{round(ev_r['Queda_Apos_Abertura'].mean(), 2)}%"
                        })
                if ranking: st.table(pd.DataFrame(ranking).sort_values(by="GAP", ascending=False))

                # --- RADAR DE HOJE ---
                st.markdown("---")
                st.subheader(f"🚀 Radar de Elite (> {filtro_radar}% Acerto)")
                dados_radar = yf.download(lista_sugerida, period="60d", progress=False)
                radar_hoje = []
                for ticker in lista_sugerida:
                    try:
                        df_tic = pd.DataFrame({'Open': dados_radar['Open'][ticker], 'Close': dados_radar['Close'][ticker]}).dropna()
                        g_hoje = round(((float(df_tic['Open'].iloc[-1]) / float(df_tic['Close'].iloc[-2])) - 1) * 100, 2)
                        df_r = yf.download(ticker, start=data_inicio, progress=False)
                        df_r.columns = [c[0] if isinstance(c, tuple) else c for c in df_r.columns]
                        df_r['Gap_H'] = ((df_r['Open'] / df_r['Close'].shift(1)) - 1) * 100
                        df_r['Max_Apos_Abertura'] = ((df_r['High'] / df_r['Open']) - 1) * 100
                        f_h = df_r[(df_r['Gap_H'] <= g_hoje + 0.15) & (df_r['Gap_H'] >= g_hoje - 0.15)]
                        if len(f_h) >= 5:
                            yr, xr = calcular_melhor_performance(f_h)
                            if xr >= filtro_radar: radar_hoje.append({"Ativo": ticker, "GAP Hoje": f"{g_hoje}%", "Acerto": f"{xr}%", "Alvo": f"{yr}%"})
                    except: continue
                if radar_hoje: st.table(pd.DataFrame(radar_hoje))

            # --- GRÁFICO (SEMPRE APARECE) ---
            st.markdown("---")
            st.subheader(f"📊 Histórico Visual de Máximas - {ativo}")
            fig = px.bar(df.sort_index(), y="Max_Apos_Abertura", color_discrete_sequence=['#3366CC'])
            st.plotly_chart(fig, use_container_width=True)
