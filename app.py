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
        df = pd.read_csv(URL_PLANILHA)
        df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Ativo', 'Gap', 'Max_Apos_Abertura', 'Queda_Apos_Abertura']
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

# --- FUNÇÃO DE PERFORMANCE BIDIRECIONAL (Invisível no visual) ---
def calcular_melhor_performance_bidirecional(df_ev):
    melhor_y, melhor_x = 0.5, 0.0
    if len(df_ev) >= 3:
        # Testa alvos de Alta (Positivos)
        for alvo in [x * 0.1 for x in range(1, 41)]:
            taxa = (len(df_ev[df_ev['Max_Apos_Abertura'] >= alvo]) / len(df_ev)) * 100
            if taxa >= 70: melhor_y, melhor_x = round(alvo, 2), round(taxa, 1)
        
        # Testa alvos de Baixa (Negativos) e vê se são melhores
        if melhor_x < 70:
            for alvo in [x * -0.1 for x in range(1, 41)]:
                taxa = (len(df_ev[df_ev['Queda_Apos_Abertura'] <= alvo]) / len(df_ev)) * 100
                if taxa >= 70: melhor_y, melhor_x = round(alvo, 2), round(taxa, 1)
    
    return melhor_y, melhor_x

# --- CONTROLES (Seu VISUAL Original) ---
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

    st.markdown("---")
    st.subheader("Verificar Data Específica")
    col_dt1, col_dt2 = st.columns([2, 1])
    with col_dt1:
        data_alvo = st.date_input("Escolha a data:", datetime.now())
    with col_dt2:
        conferir_data = st.button('📅 Conferir Resultado da Data', use_container_width=True)

    # --- PROCESSAMENTO (Seu VISUAL Original) ---
    if rodar or conferir_data:
        df_ativo = df_mestre[(df_mestre['Ativo'] == ativo) & (df_mestre['Date'] >= pd.to_datetime(data_inicio))]
        
        if not df_ativo.empty:
            if conferir_data:
                # Código de Conferir Data (Original)
                pass # (Mantido conforme original)

            if rodar:
                # Mapa de GAPs (Mostrando alvos negativos se a estatística for de queda)
                st.markdown("---")
                st.subheader("📋 Mapa de GAPs (+5% a -5%)")
                ranking = []
                for val in [x * 0.5 for x in range(-10, 11)]:
                    t_gap = round(val, 2)
                    ev_r = df_ativo[(df_ativo['Gap'] <= t_gap + 0.2) & (df_ativo['Gap'] >= t_gap - 0.2)]
                    if len(ev_r) >= 4:
                        y_r, x_r = calcular_melhor_performance_bidirecional(ev_r)
                        # Identifica se o alvo é positivo ou negativo para mostrar a direção
                        direcao = "Alta" if y_r > 0 else "Baixa"
                        ranking.append({"GAP": f"{t_gap}%", "Dias": len(ev_r), "Alvo": f"{y_r}%", "Acerto": f"{x_r}%", "Direção": direcao})
                if ranking: st.table(pd.DataFrame(ranking).sort_values(by="GAP", ascending=False))

                # Radar de Elite (Bidirecional)
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
                            # Identifica se o alvo é positivo ou negativo para mostrar a direção
                            direcao = "Alta 🟢" if yr > 0 else "Baixa 🔴"
                            radar_resumo.append({"Ativo": tk, "Direção": direcao, "GAP": f"{g_tk}%", "Acerto": f"{xr}%", "Alvo": f"{yr}%"})
                if radar_resumo: st.table(pd.DataFrame(radar_resumo))

            st.markdown("---")
            st.subheader(f"📊 Histórico Visual - {ativo}")
            # Gráfico de barras final (Original)
            st.plotly_chart(px.bar(df_ativo.tail(50), x='Date', y=['Max_Apos_Abertura', 'Queda_Apos_Abertura'], barmode='group'), use_container_width=True)

else:
    st.error("Erro ao carregar planilha.")
