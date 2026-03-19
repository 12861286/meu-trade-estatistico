import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. Configuração de layout (Seu VISUAL Original)
st.set_page_config(page_title="Scanner Quant B3", layout="wide")

st.title("🔍 Scanner de Estatística de Abertura")

# --- O SEU LINK DA PLANILHA ---
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTn6i6FnZ7awsqEZLkxsIRSFHgRonDnBrK33Jvi-gATeCnUbSgWQp3J0aMzr7VqC_b2hySzKN_LEMxS/pub?output=csv"

@st.cache_data(ttl=600)
def carregar_banco_dados():
    try:
        # Lendo colunas conforme seu print (Date, Open, High, Low, Close, Ativo, Gap, Max_A, Min_A)
        df = pd.read_csv(URL_PLANILHA)
        df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Ativo', 'Gap', 'Max_A', 'Min_A']
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
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

def calcular_melhor_performance_bidirecional(df_ev):
    melhor_y, melhor_x = 0.5, 0.0
    if len(df_ev) >= 3:
        # Testa Alta (Usa Max_A da sua planilha)
        for alvo in [x * 0.1 for x in range(1, 41)]:
            taxa = (len(df_ev[df_ev['Max_A'] >= alvo]) / len(df_ev)) * 100
            if taxa >= 70: melhor_y, melhor_x = round(alvo, 2), round(taxa, 1)
        
        # Se Alta for ruim, testa Baixa (Usa Min_A da sua planilha)
        if melhor_x < 70:
            for alvo in [x * -0.1 for x in range(1, 41)]:
                taxa = (len(df_ev[df_ev['Min_A'] <= alvo]) / len(df_ev)) * 100
                if taxa >= 70: melhor_y, melhor_x = round(alvo, 2), round(taxa, 1)
    return melhor_y, melhor_x

# --- CONTROLES ---
st.subheader("Configurações do Backtest")
df_mestre = carregar_banco_dados()

if not df_mestre.empty:
    lista_sugerida = sorted(df_mestre['Ativo'].unique())
    ativo = st.selectbox("Selecione ou DIGITE a ação:", lista_sugerida)

    gap_atual = obter_gap_hoje(ativo)
    cor_caixa = "#d4edda" if gap_atual >= 0 else "#f8d7da"
    st.markdown(f'<div style="background-color:{cor_caixa}; padding:10px; border-radius:10px; text-align:center; color: black; margin-bottom: 20px;"><b>GAP HOJE: {gap_atual}%</b></div>', unsafe_allow_html=True)

    col_cfg1, col_cfg2, col_cfg3 = st.columns([1, 1, 1])
    with col_cfg1:
        data_inicio = st.date_input("Data de Início:", datetime(2020, 1, 1))
    with col_cfg2:
        gap_digitado = st.number_input("GAP desejado (%):", value=gap_atual, step=0.1)
    with col_cfg3:
        filtro_radar = st.number_input("Mínimo de Acerto Radar (%):", value=80, step=5)

    rodar = st.button('🚀 Rodar Estatística e Radar', use_container_width=True)

    if rodar:
        df_ativo = df_mestre[(df_mestre['Ativo'] == ativo) & (df_mestre['Date'] >= pd.to_datetime(data_inicio))]
        
        if not df_ativo.empty:
            # --- NOVO: RESULTADO ESPECÍFICO DO ATIVO SELECIONADO ---
            st.markdown("---")
            st.subheader(f"🎯 Estratégia para {ativo} (GAP de {gap_digitado}%)")
            
            # Filtra o histórico para o GAP que você digitou/selecionou
            ev_especifico = df_ativo[(df_ativo['Gap'] <= gap_digitado + 0.15) & (df_ativo['Gap'] >= gap_digitado - 0.15)]
            
            if len(ev_especifico) >= 3:
                y_r, x_r = calcular_melhor_performance_bidirecional(ev_especifico)
                direcao = "ALTA 🟢" if y_r > 0 else "BAIXA 🔴"
                st.info(f"Baseado em {len(ev_especifico)} dias históricos, a melhor probabilidade é de **{direcao}** com **{x_r}%** de acerto para o alvo de **{y_r}%**.")
            else:
                st.warning(f"Poucos dados históricos ({len(ev_especifico)} dias) para este GAP específico.")

            # --- MAPA DE GAPS ---
            st.markdown("---")
            st.subheader("📋 Mapa de GAPs (+5% a -5%)")
            ranking = []
            for val in [x * 0.5 for x in range(-10, 11)]:
                t_gap = round(val, 2)
                ev_r = df_ativo[(df_ativo['Gap'] <= t_gap + 0.2) & (df_ativo['Gap'] >= t_gap - 0.2)]
                if len(ev_r) >= 3:
                    y_r, x_r = calcular_melhor_performance_bidirecional(ev_r)
                    ranking.append({"GAP": f"{t_gap}%", "Dias": len(ev_r), "Alvo": f"{y_r}%", "Acerto": f"{x_r}%", "Direção": "Alta" if y_r > 0 else "Baixa"})
            if ranking: st.table(pd.DataFrame(ranking).sort_values(by="GAP", ascending=False))

            # --- RADAR DE ELITE ---
            st.markdown("---")
            st.subheader(f"🚀 Radar de Elite (> {filtro_radar}% Acerto)")
            radar_resumo = []
            for tk in lista_sugerida:
                g_tk = obter_gap_hoje(tk)
                df_r = df_mestre[df_mestre['Ativo'] == tk]
                f_h = df_r[(df_r['Gap'] <= g_tk + 0.15) & (df_r['Gap'] >= g_tk - 0.15)]
                if len(f_h) >= 5:
                    yr, xr = calcular_melhor_performance_bidirecional(f_h)
                    if xr >= filtro_radar:
                        radar_resumo.append({"Ativo": tk, "Direção": "Alta 🟢" if yr > 0 else "Baixa 🔴", "GAP": f"{g_tk}%", "Acerto": f"{xr}%", "Alvo": f"{yr}%"})
            if radar_resumo: st.table(pd.DataFrame(radar_resumo))

            st.markdown("---")
            st.subheader(f"📊 Histórico Visual - {ativo}")
            # Usando Max_A e Min_A que estão na sua planilha (image_d34a26)
            st.plotly_chart(px.bar(df_ativo.tail(50), x='Date', y=['Max_A', 'Min_A'], barmode='group'), use_container_width=True)

else:
    st.error("Erro ao carregar planilha.")
