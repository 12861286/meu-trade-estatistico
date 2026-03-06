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
    # Lista com as ações mais líquidas da B3
    acoes = [
        "RRRP3.SA", "ALOS3.SA", "ALPA4.SA", "ABEV3.SA", "ARZZ3.SA", "ASAI3.SA", "AZUL4.SA", "B3SA3.SA", 
        "BBAS3.SA", "BBDC3.SA", "BBDC4.SA", "BBSE3.SA", "BEEF3.SA", "BPAC11.SA", "BRAP4.SA", "BRFS3.SA", 
        "BRKM5.SA", "BRML3.SA", "CCRO3.SA", "CIEL3.SA", "CMIG4.SA", "CMIN3.SA", "COGN3.SA", "CPFE3.SA", 
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
ativo = st.sidebar.selectbox("Selecione ou DIGITE a ação (Ex: PETR4.SA):", lista_sugerida)
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
        <span style="color:{texto_cor}; font-weight:bold; font-size:12px;">GAP HOJE {ativo}: {gap_atual}%</span>
    </div>
    """, unsafe_allow_html=True)

# --- PROCESSAMENTO ---
if rodar:
    with st.spinner(f'Analisando {ativo}...'):
        df = yf.download(ativo, start=data_inicio, progress=False)
        
        if not df.empty and len(df) > 10:
            df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
            df = df[['Open', 'High', 'Low', 'Close']].copy()
            df.columns = ['Abertura', 'Maxima', 'Minima', 'Fechamento']
            
            df['Gap'] = ((df['Abertura'] / df['Fechamento'].shift(1)) - 1) * 100
            df['Max_Apos_Abertura'] = ((df['Maxima'] / df['Abertura']) - 1) * 100
            df['Queda_Apos_Abertura'] = ((df['Minima'] / df['Abertura']) - 1) * 100
            df['Resultado_Fechamento'] = ((df['Fechamento'] / df['Abertura']) - 1) * 100

            # --- ANÁLISE 1: GAP DIGITADO ---
            eventos_digitados = df[(df['Gap'] <= gap_digitado + 0.15) & (df['Gap'] >= gap_digitado - 0.15)].copy()
            
            st.success(f"### 🎯 Resultado para o GAP Digitado ({gap_digitado}%)")
            if len(eventos_digitados) >= 3:
                y_dig, x_dig = calcular_melhor_performance(eventos_digitados)
                st.subheader(f"Neste período, sempre que o ativo abriu com o GAP de {gap_digitado}%, ele acertou {x_dig}% das vezes a porcentagem de {y_dig}%, que foi a melhor performance dele.")
                st.warning(f"💡 **Ponto de Stop:** Queda média de **{eventos_digitados['Queda_Apos_Abertura'].mean():.2f}%**.")

                st.markdown("#### 🏁 Comportamento até o Fechamento")
                fech_pos = len(eventos_digitados[eventos_digitados['Resultado_Fechamento'] > 0])
                taxa_fech_pos = round((fech_pos / len(eventos_digitados)) * 100, 1)
                res_medio = eventos_digitados['Resultado_Fechamento'].mean()
                max_media = eventos_digitados['Max_Apos_Abertura'].mean()
                min_media = eventos_digitados['Queda_Apos_Abertura'].mean()
                
                st.write(f"O ativo fechou o dia positivo (em relação à abertura) em **{taxa_fech_pos}%** das vezes.")
                st.write(f"O resultado médio no fechamento foi de **{res_medio:.2f}%**, com uma **máxima média de {max_media:.2f}%** e **mínima média de {min_media:.2f}%**.")
            
            # --- ANÁLISE 2: GAP DE HOJE ---
            st.markdown("---")
            st.info(f"### 🕒 Análise Baseada na Abertura de HOJE ({gap_atual}%)")
            eventos_hoje = df[(df['Gap'] <= gap_atual + 0.15) & (df['Gap'] >= gap_atual - 0.15)].copy()
            if len(eventos_hoje) >= 3:
                y_hoje, x_hoje = calcular_melhor_performance(eventos_hoje)
                st.subheader(f"Com este gap de hoje ({gap_atual}%), a melhor performance histórica é de {y_hoje}% com {x_hoje}% de acerto.")

            # --- SUGESTÕES ADICIONAIS ---
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
                        "Melhor Alvo": f"{y_r}%",
                        "Acerto": f"{x_r}%",
                        "Stop Médio": f"{round(ev_r['Queda_Apos_Abertura'].mean(), 2)}%"
                    })
            if ranking:
                st.table(pd.DataFrame(ranking).sort_values(by="Faixa de GAP", ascending=False))

            # --- RADAR DE OPORTUNIDADES ---
            st.markdown("---")
            st.subheader(f"🚀 Radar de Oportunidades (Acerto > {filtro_radar}%)")
            radar_oportunidades = []
            for ticker in lista_sugerida:
                try:
                    d_radar = yf.download(ticker, period="3mo", progress=False) # Periodo menor para ser mais rapido
                    d_radar.columns = [c[0] if isinstance(c, tuple) else c for c in d_radar.columns]
                    g_h = round(((float(d_radar['Open'].iloc[-1]) / float(d_radar['Close'].iloc[-2])) - 1) * 100, 2)
                    
                    # Para o radar, usamos o historico completo
                    d_full = yf.download(ticker, period="max", progress=False)
                    d_full.columns = [c[0] if isinstance(c, tuple) else c for c in d_full.columns]
                    d_full['Gap_Hist'] = ((d_full['Open'] / d_full['Close'].shift(1)) - 1) * 100
                    d_full['Max_Apos_Abertura'] = ((d_full['High'] / d_full['Open']) - 1) * 100
                    
                    f_radar = d_full[(d_full['Gap_Hist'] <= g_h + 0.15) & (d_full['Gap_Hist'] >= g_h - 0.15)]
                    if len(f_radar) >= 5:
                        yr, xr = calcular_melhor_performance(f_radar)
                        if xr >= filtro_radar:
                            radar_oportunidades.append({"Ativo": ticker, "GAP Hoje": f"{g_h}%", "Acerto": f"{xr}%", "Alvo": f"{yr}%", "Stop": f"{round(f_radar['Low'].mean(), 2)}%"})
                except: continue
            if radar_oportunidades: st.table(pd.DataFrame(radar_oportunidades))
            else: st.write("Nenhum ativo de elite no radar agora.")

            # --- GRÁFICO FINAL ---
            st.markdown("---")
            st.subheader(f"📊 Histórico de Performance em Colunas (GAP {gap_digitado}%)")
            fig = px.bar(eventos_digitados.sort_index(), y="Max_Apos_Abertura", color_discrete_sequence=['#3366CC'])
            if 'y_dig' in locals():
                fig.add_hline(y=y_dig, line_dash="dash", line_color="red", annotation_text=f"Alvo: {y_dig}%")
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.error("Ativo não encontrado ou dados insuficientes.")
