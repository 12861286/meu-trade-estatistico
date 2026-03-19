import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURAÇÃO VISUAL (PADRÃO CARLOS) ---
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
    lista_sugerida = sorted(df_mestre['Ativo'].unique())
    ativo = st.selectbox("Selecione ou DIGITE a ação:", lista_sugerida)

    gap_atual = obter_gap_hoje(ativo)
    cor_caixa = "#d4edda" if gap_atual >= 0 else "#f8d7da"
    st.markdown(f'<div style="background-color:{cor_caixa}; padding:10px; border-radius:10px; text-align:center; color: black; margin-bottom: 20px;"><b>GAP HOJE: {gap_atual}%</b></div>', unsafe_allow_html=True)

    data_3_anos = datetime.now() - timedelta(days=3*365)

    col_cfg1, col_cfg2, col_cfg3 = st.columns([1, 1, 1])
    with col_cfg1:
        data_inicio = st.date_input("Data de Início:", data_3_anos)
    with col_cfg2:
        gap_digitado = st.number_input("GAP desejado (%):", value=gap_atual, step=0.1)
    with col_cfg3:
        filtro_radar = st.number_input("Mínimo de Acerto Radar (%):", value=80, step=5)

    rodar = st.button('🚀 Rodar Estatística e Radar', use_container_width=True)

    # --- 3. VERIFICAR RESULTADO POR DATA (SOLICITAÇÃO CARLOS) ---
    st.markdown("---")
    st.subheader("🔍 Verificar Resultado por Data Específica")
    col_dt1, col_dt2 = st.columns([2, 1])
    with col_dt1:
        data_pesquisa = st.date_input("Escolha a data:", datetime.now(), key="dt_pesq")
    with col_dt2:
        btn_conferir = st.button('📅 Conferir Resultado da Data', use_container_width=True)

    if btn_conferir:
        res_dia = df_mestre[(df_mestre['Ativo'] == ativo) & (df_mestre['Date'].dt.date == data_pesquisa)]
        if not res_dia.empty:
            # Pegamos o alvo estatístico para comparar
            alvo_ref, _ = calcular_performance(df_mestre[df_mestre['Ativo'] == ativo])
            
            # Verificamos se atingiu o objetivo
            atingiu = "✅ SIM" if (alvo_ref > 0 and res_dia['Max_A'].iloc[0] >= alvo_ref) or (alvo_ref < 0 and res_dia['Min_A'].iloc[0] <= alvo_ref) else "❌ NÃO"
            
            st.markdown(f"### Resultado de {data_pesquisa.strftime('%d/%m/%Y')} para {ativo}")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("GAP de Abertura", f"{res_dia['Gap'].iloc[0]:.2f}%")
            c2.metric("Atingiu Objetivo?", atingiu)
            c3.metric("Máxima do Dia (Max_A)", f"{res_dia['Max_A'].iloc[0]:.2f}%")
            c4.metric("Mínima do Dia (Min_A)", f"{res_dia['Min_A'].iloc[0]:.2f}%")
        else:
            st.warning(f"Sem dados para {ativo} na data selecionada.")

    # --- 4. RESULTADOS GERAIS ---
    if rodar:
        df_ativo = df_mestre[(df_mestre['Ativo'] == ativo) & (df_mestre['Date'] >= pd.to_datetime(data_inicio))]
        if not df_ativo.empty:
            ev_esp = df_ativo[(df_ativo['Gap'] <= gap_digitado + 0.15) & (df_ativo['Gap'] >= gap_digitado - 0.15)]
            if not ev_esp.empty:
                st.markdown(f"### 🎯 Resumo Estratégico: {ativo}")
                total = len(ev_esp)
                pos_count = len(ev_esp[ev_esp['Max_A'] > 0])
                neg_count = len(ev_esp[ev_esp['Min_A'] < 0])
                alvo_n, acerto_n = calcular_performance(ev_esp)

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Maior Alta Hist.", f"{ev_esp['Max_A'].max():.2f}%")
                m2.metric("Maior Mínima Hist.", f"{ev_esp['Min_A'].min():.2f}%")
                m3.metric("Frequência (+)", f"{pos_count} dias", f"{(pos_count/total)*100:.1f}%")
                m4.metric("Nível Alvo", f"{alvo_n}%", f"Acerto: {acerto_n}%")

            # Mapa de GAPs
            st.markdown("---")
            st.subheader("📋 Mapa de GAPs (+5% a -5%)")
            ranking = []
            for val in [x * 0.5 for x in range(-10, 11)]:
                t_gap = round(val, 2)
                ev_r = df_ativo[(df_ativo['Gap'] <= t_gap + 0.2) & (df_ativo['Gap'] >= t_gap - 0.2)]
                if len(ev_r) >= 3:
                    yr, xr = calcular_performance(ev_r)
                    ranking.append({"GAP": f"{t_gap}%", "Dias": len(ev_r), "Alvo": f"{yr}%", "Acerto": f"{xr}%", "Direção": "Alta" if yr > 0 else "Baixa"})
            if ranking: st.table(pd.DataFrame(ranking).sort_values(by="GAP", ascending=False))

            # Radar de Elite
            st.markdown("---")
            st.subheader(f"🚀 Radar de Elite (> {filtro_radar}% Acerto)")
            radar_resumo = []
            for tk in lista_sugerida:
                g_tk = obter_gap_hoje(tk)
                df_r = df_mestre[df_mestre['Ativo'] == tk]
                f_h = df_r[(df_r['Gap'] <= g_tk + 0.15) & (df_r['Gap'] >= g_tk - 0.15)]
                if len(f_h) >= 5:
                    yr, xr = calcular_performance(f_h)
                    if xr >= filtro_radar:
                        radar_resumo.append({"Ativo": tk, "Direção": "Alta 🟢" if yr > 0 else "Baixa 🔴", "GAP": f"{g_tk}%", "Acerto": f"{xr}%", "Alvo": f"{yr}%"})
            if radar_resumo: st.table(pd.DataFrame(radar_resumo))
else:
    st.error("Planilha não carregada.")
