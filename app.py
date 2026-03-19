import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURAÇÃO E DADOS ---
st.set_page_config(page_title="Scanner Quant B3", layout="wide")
st.title("🔍 Scanner de Estatística de Abertura")

URL_PLANILHA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTn6i6FnZ7awsqEZLkxsIRSFHgRonDnBrK33Jvi-gATeCnUbSgWQp3J0aMzr7VqC_b2hySzKN_LEMxS/pub?output=csv"

@st.cache_data(ttl=600)
def carregar_banco_dados():
    try:
        df = pd.read_csv(URL_PLANILHA)
        df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Ativo', 'Gap', 'Max_A', 'Min_A']
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Fech_Apos_Abertura'] = ((df['Close'] / df['Open']) - 1) * 100
        return df.dropna(subset=['Ativo'])
    except:
        return pd.DataFrame()

def obter_gap_hoje(ticker):
    try:
        dados = yf.download(ticker, period="2d", progress=False)
        if len(dados) < 2: return 0.0
        dados.columns = [c[0] if isinstance(c, tuple) else c for c in dados.columns]
        fechamento_ontem = float(dados['Close'].iloc[-2])
        abertura_hoje = float(dados['Open'].iloc[-1])
        return round(((abertura_hoje / fechamento_ontem) - 1) * 100, 2)
    except: return 0.0

def calcular_performance(df_ev):
    melhor_y, melhor_x = 0.5, 0.0
    if len(df_ev) >= 3:
        for alvo in [x * 0.1 for x in range(1, 41)]:
            taxa = (len(df_ev[df_ev['Max_A'] >= alvo]) / len(df_ev)) * 100
            if taxa >= 70: melhor_y, melhor_x = round(alvo, 2), round(taxa, 1)
        if melhor_x < 70:
            for alvo in [x * -0.1 for x in range(1, 41)]:
                taxa = (len(df_ev[df_ev['Min_A'] <= alvo]) / len(df_ev)) * 100
                if taxa >= 70: melhor_y, melhor_x = round(alvo, 2), round(taxa, 1)
    return melhor_y, melhor_x

# --- 2. CONFIGURAÇÕES ---
df_mestre = carregar_banco_dados()

if not df_mestre.empty:
    lista_ativos = sorted(df_mestre['Ativo'].unique())
    ativo_sel = st.selectbox("Ativo para análise detalhada:", lista_ativos)
    
    gap_hoje_sel = obter_gap_hoje(ativo_sel)
    st.info(f"GAP de hoje para {ativo_sel}: {gap_hoje_sel}%")

    col1, col2 = st.columns(2)
    with col1:
        data_ini = st.date_input("Início do Backtest:", datetime.now() - timedelta(days=3*365))
    with col2:
        min_radar = st.number_input("Mínimo de Acerto Radar (%):", value=80)

    btn_rodar = st.button("🚀 Rodar Estatística e Radar", use_container_width=True)

    if btn_rodar:
        # --- 3. RADAR DE ELITE (RECOMENDAÇÕES DO DIA) ---
        st.markdown("---")
        st.subheader(f"🚀 Radar de Elite (> {min_radar}% de Acerto)")
        st.write("Processando ativos da lista com o GAP de abertura de hoje...")
        
        radar_data = []
        progresso = st.progress(0)
        
        for i, tk in enumerate(lista_ativos):
            g_atual = obter_gap_hoje(tk)
            # Filtra histórico do ativo para GAPs similares ao de hoje (margem 0.15)
            df_hist = df_mestre[(df_mestre['Ativo'] == tk) & 
                                (df_mestre['Date'] >= pd.to_datetime(data_ini)) &
                                (df_mestre['Gap'] <= g_atual + 0.15) & 
                                (df_mestre['Gap'] >= g_atual - 0.15)]
            
            if len(df_hist) >= 5: # Mínimo de 5 ocorrências para ser confiável
                alvo, acerto = calcular_performance(df_hist)
                if acerto >= min_radar:
                    radar_data.append({
                        "Ativo": tk,
                        "GAP Hoje": f"{g_atual}%",
                        "Direção": "COMPRA 🟢" if alvo > 0 else "VENDA 🔴",
                        "Alvo Sugerido": f"{alvo}%",
                        "Assertividade": f"{acerto}%",
                        "Amostra": f"{len(df_hist)} dias"
                    })
            progresso.progress((i + 1) / len(lista_ativos))
        
        if radar_data:
            st.table(pd.DataFrame(radar_data).sort_values(by="Assertividade", ascending=False))
        else:
            st.warning("Nenhum ativo atingiu o critério de acerto hoje.")

        # --- 4. MAPA DE GAPS (ATIVO SELECIONADO) ---
        st.markdown("---")
        st.subheader(f"📋 Mapa de GAPs: {ativo_sel}")
        df_ativo = df_mestre[(df_mestre['Ativo'] == ativo_sel) & (df_mestre['Date'] >= pd.to_datetime(data_ini))]
        
        ranking = []
        for val in [x * 0.5 for x in range(-10, 11)]:
            t_gap = round(val, 2)
            ev_r = df_ativo[(df_ativo['Gap'] <= t_gap + 0.2) & (df_ativo['Gap'] >= t_gap - 0.2)]
            if len(ev_r) >= 3:
                yr, xr = calcular_performance(ev_r)
                ranking.append({"GAP Ref": f"{t_gap}%", "Dias": len(ev_r), "Alvo": f"{yr}%", "Acerto": f"{xr}%"})
        
        if ranking:
            st.table(pd.DataFrame(ranking).sort_values(by="GAP Ref", ascending=False))

else:
    st.error("Erro ao carregar banco de dados.")
