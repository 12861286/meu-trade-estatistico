import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. Configuração de layout
st.set_page_config(page_title="Scanner Quant B3", layout="wide")

st.title("🔍 Scanner de Estatística de Abertura")

# --- O SEU LINK DA PLANILHA (Sempre atualizado aqui) ---
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTn6i6FnZ7awsqEZLkxsIRSFHgRonDnBrK33Jvi-gATeCnUbSgWQp3J0aMzr7VqC_b2hySzKN_LEMxS/pub?output=csv"

# --- LISTA EXTENSA DE AÇÕES B3 ---
@st.cache_data
def carregar_lista_ativos():
    # Tenta pegar da planilha primeiro para bater com o que você tem
    try:
        df_temp = pd.read_csv(URL_PLANILHA)
        if 'Ativo' in df_temp.columns:
            return sorted(df_temp['Ativo'].unique().tolist())
    except:
        pass
    return ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "ABEV3.SA"]

# --- FUNÇÃO DE CARREGAMENTO DO BANCO DE DADOS ---
@st.cache_data(ttl=600)
def carregar_banco_dados():
    try:
        df = pd.read_csv(URL_PLANILHA)
        # Ajuste técnico para garantir que os nomes das colunas batam com o seu visual
        df.columns = ['Date', 'Abertura', 'Maxima', 'Minima', 'Fechamento', 'Ativo', 'Gap', 'Max_Apos_Abertura', 'Queda_Apos_Abertura']
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df.dropna(subset=['Ativo'])
    except:
        return pd.DataFrame()

# --- FUNÇÃO DO GAP DE HOJE (Yahoo Finance) ---
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

# --- CONTROLES PRINCIPAIS ---
st.subheader("Configurações do Backtest")
df_mestre = carregar_banco_dados()

if not df_mestre.empty:
    lista_sugerida = sorted(df_mestre['Ativo'].unique())
    ativo = st.selectbox("Selecione ou DIGITE a ação:", lista_sugerida)

    # GAP HOJE (Igual ao seu original)
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

    # --- PROCESSAMENTO ---
    if rodar or conferir_data:
        # Filtra os dados da planilha
        df_ativo = df_mestre[(df_mestre['Ativo'] == ativo) & (df_mestre['Date'] >= pd.to_datetime(data_inicio))]

        if not df_ativo.empty:
            if conferir_data:
                st.markdown("---")
                data_busca = data_alvo.strftime('%Y-%m-%d')
                if data_busca in df_ativo['Date'].dt.strftime('%Y-%m-%d').values:
                    dia_sel = df_ativo[df_ativo['Date'].dt.strftime('%Y-%m-%d') == data_busca].iloc[0]
                    gap_dia, max_dia, min_dia = round(dia_sel['Gap'], 2), round(dia_sel['Max_Apos_Abertura'], 2), round(dia_sel['Queda_Apos_Abertura'], 2)
                    
                    eventos_data = df_ativo[(df_ativo['Gap'] <= gap_dia + 0.15) & (df_ativo['Gap'] >= gap_dia - 0.15)]
                    
                    st.info(f"### 📊 Resultado do Ativo em {data_alvo.strftime('%d/%m/%Y')}")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("GAP de Abertura", f"{gap_dia}%")
                    col2.metric("Máxima do Dia", f"{max_dia}%")
                    col3.metric("Mínima do Dia", f"{min_dia}%")
                    
                    if len(eventos_data) >= 3:
                        y_o, x_o = calcular_melhor_performance(eventos_data)
                        st.write(f"**Estatística Esperada:** {x_o}% de chance para buscar {y_o}% de alvo.")
                        if max_dia >= y_o: st.success("✅ **BATEU O ALVO!**")
                        else: st.error("❌ **NÃO BATEU.**")
                else: st.error("Data não encontrada no seu histórico.")

            if rodar:
                eventos_digitados = df_ativo[(df_ativo['Gap'] <= gap_digitado + 0.15) & (df_ativo['Gap'] >= gap_digitado - 0.15)].copy()
                st.success(f"### 🎯 GAP Analisado: {gap_digitado}% | Ativo: {ativo}")
                
                if len(eventos_digitados) >= 3:
                    y_dig, x_dig = calcular_melhor_performance(eventos_digitados)
                    st.subheader(f"Probabilidade de {x_dig}% para atingir {y_dig}% de alvo.")
                    
                    st.write(f"**Médias do dia:** Máxima {eventos_digitados['Max_Apos_Abertura'].mean():.2f}% | Mínima {eventos_digitados['Queda_Apos_Abertura'].mean():.2f}%")

                st.markdown("---")
                st.subheader("📋 Mapa de GAPs (+5% a -5%)")
                ranking = []
                for val in [x * 0.5 for x in range(-10, 11)]:
                    t_gap = round(val, 2)
                    ev_r = df_ativo[(df_ativo['Gap'] <= t_gap + 0.2) & (df_ativo['Gap'] >= t_gap - 0.2)]
                    if len(ev_r) >= 4:
                        y_r, x_r = calcular_melhor_performance(ev_r)
                        ranking.append({"GAP": f"{t_gap}%", "Dias": len(ev_r), "Alvo": f"{y_r}%", "Acerto": f"{x_r}%"})
                if ranking: st.table(pd.DataFrame(ranking).sort_values(by="GAP", ascending=False))

                # RADAR AUTOMÁTICO (Rápido pois usa a planilha)
                st.markdown("---")
                st.subheader(f"🚀 Radar de Elite (> {filtro_radar}% Acerto)")
                radar_hoje = []
                for tk in lista_sugerida:
                    g_tk = obter_gap_hoje(tk)
                    df_r = df_mestre[df_mestre['Ativo'] == tk]
                    f_h = df_r[(df_r['Gap'] <= g_tk + 0.15) & (df_r['Gap'] >= g_tk - 0.15)]
                    if len(f_h) >= 5:
                        yr, xr = calcular_melhor_performance(f_h)
                        if xr >= filtro_radar:
                            radar_hoje.append({"Ativo": tk, "GAP Hoje": f"{g_tk}%", "Acerto": f"{xr}%", "Alvo": f"{yr}%"})
                if radar_hoje: st.table(pd.DataFrame(radar_hoje))

            st.markdown("---")
            st.subheader(f"📊 Histórico Visual - {ativo}")
            fig = px.bar(df_ativo.tail(50), x='Date', y=['Max_Apos_Abertura', 'Queda_Apos_Abertura'], barmode='group')
            st.plotly_chart(fig, use_container_width=True)
else:
    st.error("Planilha não encontrada. Verifique o link no GitHub.")
