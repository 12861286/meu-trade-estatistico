import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURAÇÃO E CARREGAMENTO ---
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
    ativo_sel = st.selectbox("Selecione o Ativo:", lista_ativos)
    
    gap_hoje_sel = obter_gap_hoje(ativo_sel)
    st.info(f"GAP de hoje para {ativo_sel}: {gap_hoje_sel}%")

    col1, col2, col3 = st.columns(3)
    with col1:
        data_ini = st.date_input("Início do Backtest:", datetime.now() - timedelta(days=3*365))
    with col2:
        gap_manual = st.number_input("GAP para Análise (%):", value=gap_hoje_sel, step=0.1)
    with col3:
        min_radar = st.number_input("Mínimo de Acerto Radar (%):", value=80)

    # --- 3. PROCURAR POR DATA (RESTAURADO) ---
    st.markdown("---")
    st.subheader("📅 Verificar Resultado por Data")
    c_dt1, c_dt2 = st.columns([2, 1])
    with c_dt1:
        data_pesq = st.date_input("Escolha o dia para conferir:", datetime.now(), key="pesq_data")
    with c_dt2:
        btn_data = st.button("🔎 Conferir Data", use_container_width=True)

    if btn_data:
        res_dia = df_mestre[(df_mestre['Ativo'] == ativo_sel) & (df_mestre['Date'].dt.date == data_pesq)]
        if not res_dia.empty:
            obj, prob = calcular_performance(df_mestre[df_mestre['Ativo'] == ativo_sel])
            max_d = res_dia['Max_A'].iloc[0]
            min_d = res_dia['Min_A'].iloc[0]
            atingiu = "✅ SIM" if (obj > 0 and max_d >= obj) or (obj < 0 and min_d <= obj) else "❌ NÃO"
            
            st.success(f"Resultado de {ativo_sel} em {data_pesq.strftime('%d/%m/%Y')}")
            d1, d2, d3, d4 = st.columns(4)
            d1.metric("GAP Abertura", f"{res_dia['Gap'].iloc[0]:.2f}%")
            d2.metric("Objetivo", f"{obj}%")
            d3.metric("Atingiu?", atingiu)
            d4.metric("Máxima/Mínima", f"{max_d:.2f}% / {min_d:.2f}%")
        else:
            st.warning("Sem dados para esta data.")

    btn_rodar = st.button("🚀 Rodar Estatística e Radar", use_container_width=True)

    if btn_rodar:
        # --- 4. RESUMO ESTRATÉGICO ---
        st.markdown(f"## 📊 Estatística Detalhada: {ativo_sel}")
        df_ativo = df_mestre[(df_mestre['Ativo'] == ativo_sel) & (df_mestre['Date'] >= pd.to_datetime(data_ini))]
        ev_esp = df_ativo[(df_ativo['Gap'] <= gap_manual + 0.15) & (df_ativo['Gap'] >= gap_manual - 0.15)]
        
        if not ev_esp.empty:
            total = len(ev_esp)
            pos = len(ev_esp[ev_esp['Max_A'] > 0])
            alvo_n, acerto_n = calcular_performance(ev_esp)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Maior Alta Hist.", f"{ev_esp['Max_A'].max():.2f}%")
            m2.metric("Maior Mínima Hist.", f"{ev_esp['Min_A'].min():.2f}%")
            m3.metric("Frequência (+)", f"{pos} dias", f"{(pos/total)*100:.1f}%")
            m4.metric("Nível Alvo", f"{alvo_n}%", f"Acerto: {acerto_n}%")

        # --- 5. MAPA DE GAPS ---
        st.subheader("📋 Mapa de GAPs")
        ranking = []
        for val in [x * 0.5 for x in range(-10, 11)]:
            t_gap = round(val, 2)
            ev_r = df_ativo[(df_ativo['Gap'] <= t_gap + 0.2) & (df_ativo['Gap'] >= t_gap - 0.2)]
            if len(ev_r) >= 3:
                yr, xr = calcular_performance(ev_r)
                ranking.append({"GAP Ref": f"{t_gap}%", "Dias": len(ev_r), "Alvo": f"{yr}%", "Acerto": f"{xr}%"})
        if ranking: st.table(pd.DataFrame(ranking).sort_values(by="GAP Ref", ascending=False))

        # --- 6. RADAR DE ELITE ---
        st.markdown("---")
        st.subheader(f"🚀 Radar de Elite Hoje (> {min_radar}% Acerto)")
        radar_data = []
        with st.spinner("Escaneando mercado..."):
            for tk in lista_ativos:
                g_atual = obter_gap_hoje(tk)
                df_hist = df_mestre[(df_mestre['Ativo'] == tk) & (df_mestre['Gap'] <= g_atual + 0.15) & (df_mestre['Gap'] >= g_atual - 0.15)]
                if len(df_hist) >= 5:
                    alvo, acerto = calcular_performance(df_hist)
                    if acerto >= min_radar:
                        radar_data.append({"Ativo": tk, "GAP Hoje": f"{g_atual}%", "Direção": "COMPRA 🟢" if alvo > 0 else "VENDA 🔴", "Alvo": f"{alvo}%", "Acerto": f"{acerto}%"})
        if radar_data: st.table(pd.DataFrame(radar_data).sort_values(by="Acerto", ascending=False))
else:
    st.error("Erro ao carregar banco de dados.")
