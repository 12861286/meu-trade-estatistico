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

def obter_gap_hoje(ticker):
    try:
        dados = yf.download(ticker, period="2d", progress=False)
        if len(dados) < 2: return 0.0
        dados.columns = [c[0] if isinstance(c, tuple) else c for c in dados.columns]
        fechamento_ontem = float(dados['Close'].iloc[-2])
        abertura_hoje = float(dados['Open'].iloc[-1])
        return round(((abertura_hoje / fechamento_ontem) - 1) * 100, 2)
    except: return 0.0

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

rodar = st.sidebar.button('🚀 Rodar Estatística e Radar')

gap_atual = obter_gap_hoje(ativo)
cor_caixa = "#d4edda" if gap_atual >= 0 else "#f8d7da"
st.sidebar.markdown(f'<div style="background-color:{cor_caixa}; padding:10px; border-radius:10px; text-align:center; color: black;"><b>GAP HOJE: {gap_atual}%</b></div>', unsafe_allow_html=True)

if rodar:
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

            # --- ANÁLISE DO GAP DIGITADO ---
            eventos_digitados = df[(df['Gap'] <= gap_digitado + 0.15) & (df['Gap'] >= gap_digitado - 0.15)].copy()
            st.success(f"### 🎯 GAP Digitado: {gap_digitado}% | Ativo: {ativo}")
            
            if len(eventos_digitados) >= 3:
                y_dig, x_dig = calcular_melhor_performance(eventos_digitados)
                st.subheader(f"Probabilidade de {x_dig}% para atingir {y_dig}% de alvo.")
                
                f_pos_d = len(eventos_digitados[eventos_digitados['Resultado_Fechamento'] > 0])
                p_pos_d = round((f_pos_d / len(eventos_digitados)) * 100, 1)
                st.write(f"**Fechamento:** Positivo {p_pos_d}% | Negativo {round(100-p_pos_d, 1)}%")
                st.write(f"**Médias do dia:** Máxima {eventos_digitados['Max_Apos_Abertura'].mean():.2f}% | Mínima {eventos_digitados['Queda_Apos_Abertura'].mean():.2f}%")

            # --- TABELA DE SUGESTÕES ADICIONAIS ---
            st.markdown("---")
            st.subheader("📋 Mapa de GAPs (+5% a -5%)")
            ranking = []
            for val in [x * 0.5 for x in range(-10, 11)]:
                t_gap = round(val, 2)
                ev_r = df[(df['Gap'] <= t_gap + 0.2) & (df['Gap'] >= t_gap - 0.2)]
                if len(ev_r) >= 4:
                    y_r, x_r = calcular_melhor_performance(ev_r)
                    f_pos = len(ev_r[ev_r['Resultado_Fechamento'] > 0])
                    p_pos = round((f_pos / len(ev_r)) * 100, 1)
                    ranking.append({
                        "GAP": f"{t_gap}%", "Dias": len(ev_r), "Alvo": f"{y_r}%", "Acerto": f"{x_r}%",
                        "Máx Média": f"{round(ev_r['Max_Apos_Abertura'].mean(), 2)}%",
                        "Mín Média": f"{round(ev_r['Queda_Apos_Abertura'].mean(), 2)}%",
                        "% Fech Pos": f"{p_pos}%", "% Fech Neg": f"{round(100 - p_pos, 1)}%"
                    })
            if ranking:
                st.table(pd.DataFrame(ranking).sort_values(by="GAP", ascending=False))

            # --- RADAR HOJE E ONTEM ---
            st.markdown("---")
            st.subheader(f"🚀 Radar de Elite (> {filtro_radar}% Acerto)")
            
            dados_radar = yf.download(lista_sugerida, period="60d", progress=False)
            radar_oportunidades = []
            radar_ontem = []
            
            for t_radar in lista_sugerida:
                try:
                    df_tic = pd.DataFrame({
                        'Open': dados_radar['Open'][t_radar], 'High': dados_radar['High'][t_radar],
                        'Low': dados_radar['Low'][t_radar], 'Close': dados_radar['Close'][t_radar]
                    }).dropna()

                    if len(df_tic) < 5: continue
                    
                    g_h = round(((float(df_tic['Open'].iloc[-1]) / float(df_tic['Close'].iloc[-2])) - 1) * 100, 2)
                    g_o = round(((float(df_tic['Open'].iloc[-2]) / float(df_tic['Close'].iloc[-3])) - 1) * 100, 2)
                    d_o_str = df_tic.index[-2].strftime('%d/%m/%Y')

                    # Backtest simplificado para o radar (usando os dados já baixados do ativo principal se coincidir)
                    df_hist = yf.download(t_radar, start=data_inicio, progress=False)
                    df_hist.columns = [c[0] if isinstance(c, tuple) else c for c in df_hist.columns]
                    df_hist['Gap_H'] = ((df_hist['Open'] / df_hist['Close'].shift(1)) - 1) * 100
                    df_hist['Max_Apos_Abertura'] = ((df_hist['High'] / df_hist['Open']) - 1) * 100
                    df_hist['Resultado_Fechamento'] = ((df_hist['Close'] / df_hist['Open']) - 1) * 100
                    
                    # Hoje
                    f_h = df_hist[(df_hist['Gap_H'] <= g_h + 0.15) & (df_hist['Gap_H'] >= g_h - 0.15)]
                    if len(f_h) >= 5:
                        yr, xr = calcular_melhor_performance(f_h)
                        if xr >= filtro_radar:
                            radar_oportunidades.append({"Ativo": t_radar, "GAP": f"{g_h}%", "Acerto": f"{xr}%", "Alvo": f"{yr}%"})
                    
                    # Ontem
                    f_o = df_hist[(df_hist['Gap_H'] <= g_o + 0.15) & (df_hist['Gap_H'] >= g_o - 0.15)]
                    if len(f_o) >= 5:
                        yr_o, xr_o = calcular_melhor_performance(f_o)
                        if xr_o >= filtro_radar:
                            radar_ontem.append({"Data": d_o_str, "Ativo": t_radar, "GAP": f"{g_o}%", "Acerto": f"{xr_o}%", "Alvo": f"{yr_o}%", "dados": f_o})
                except: continue
                
            if radar_oportunidades: st.table(pd.DataFrame(radar_oportunidades))
            else: st.write("Nenhuma oportunidade clara agora.")

            st.markdown("---")
            st.subheader(f"⏪ Radar de Elite - Dia Anterior (> {filtro_radar}% Acerto)")
            if radar_ontem:
                df_ontem_tab = pd.DataFrame(radar_ontem).drop(columns=['dados'])
                st.table(df_ontem_tab)
                
                # --- ESTUDO DO ATIVO DE ONTEM ---
                ativo_estudo = st.selectbox("🔬 Escolha um ativo de ontem para estudar a estatística:", ["Selecione..."] + [x['Ativo'] for x in radar_ontem])
                
                if ativo_estudo != "Selecione...":
                    item = next(x for x in radar_ontem if x['Ativo'] == ativo_estudo)
                    dados_estudo = item['dados']
                    
                    st.success(f"### 🎯 GAP de Ontem ({item['Data']}): {item['GAP']} | Ativo: {ativo_estudo}")
                    st.subheader(f"Probabilidade de {item['Acerto']} para atingir {item['Alvo']} de alvo.")
                    
                    f_pos_o = len(dados_estudo[dados_estudo['Resultado_Fechamento'] > 0])
                    p_pos_o = round((f_pos_o / len(dados_estudo)) * 100, 1)
                    st.write(f"**Fechamento:** Positivo {p_pos_o}% | Negativo {round(100-p_pos_o, 1)}%")
                    st.write(f"**Médias históricas para este GAP:** Máxima {dados_estudo['Max_Apos_Abertura'].mean():.2f}%")
            else:
                st.write("Sem dados do dia anterior.")

            st.markdown("---")
            st.subheader("📊 Histórico Visual de Máximas")
            fig = px.bar(eventos_digitados.sort_index(), y="Max_Apos_Abertura", color_discrete_sequence=['#3366CC'])
            st.plotly_chart(fig, use_container_width=True)
