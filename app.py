import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURAÇÃO VISUAL (SEU PADRÃO) ---
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
    return melhor_y, melhor_x # Corrigido aqui (estava mejor_x)

# --- 2. ÁREA DE CONFIGURAÇÃO ---
st.subheader("Configurações do Backtest")
df_mestre = carregar_banco_dados()

if not df_mestre.empty:
    lista_sugerida = sorted(df_mestre['Ativo'].unique())
    ativo = st.selectbox("Selecione ou DIGITE a ação:", lista_sugerida)

    gap_atual = obter_gap_hoje(ativo)
    cor_caixa = "#d4edda" if gap_atual >= 0 else "#f8d7da"
    st.markdown(f'<div style="background-color:{cor_caixa}; padding:10px; border-radius:10px; text-align:center; color: black; margin-bottom: 20px;"><b>GAP HOJE: {gap_atual}%</b></div>', unsafe_allow_html=True)

    data_3_anos_atras = datetime.now() - timedelta(days=3*365)

    col_cfg1, col_cfg2, col_cfg3 = st.columns([1, 1, 1])
    with col_cfg1:
        data_inicio = st.date_input("Data de Início:", data_3_anos_atras)
    with col_cfg2:
        gap_digitado = st.number_input("GAP desejado (%):", value=gap_atual, step=0.1)
    with col_cfg3:
        filtro_radar = st.number_input("Mínimo de Acerto Radar (%):", value=80, step=5)

    rodar = st.button('🚀 Rodar Estatística e Radar', use_container_width=True)

    if rodar:
        df_ativo = df_mestre[(df_mestre['Ativo'] == ativo) & (df_mestre['Date'] >= pd.to_datetime(data_inicio))]
        
        if not df_ativo.empty:
            # 3. RESUMO ESTRATÉGICO
            ev_esp = df_ativo[(df_ativo['Gap'] <= gap_digitado + 0.15) & (df_ativo['Gap'] >= gap_digitado - 0.15)]
            if not ev_esp.empty:
                st.markdown(f"### 🎯 Resumo Estratégico: {ativo}")
                
                total = len(ev_esp)
                pos_count = len(ev_esp[ev_esp['Max_A'] > 0])
                neg_count = len(ev_esp[ev_esp['Min_A'] < 0])
                alvo_n, acerto_n = calcular_performance(ev_esp)

                # Linha 1: Extremos
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Maior Alta", f"{ev_esp['Max_A'].max():.2f}%")
                c2.metric("Maior Mínima", f"{ev_esp['Min_A'].min():.2f}%")
                c3.metric("Fech. Médio Alta", f"{ev_esp[ev_esp['Fech_Apos_Abertura']>0]['Fech_Apos_Abertura'].mean():.2f}%")
                c4.metric("Fech. Médio Baixa", f"{ev_esp[ev_esp['Fech_Apos_Abertura']<0]['Fech_Apos_Abertura'].mean():.2f}%")

                # Linha 2: Frequência e Nível
                st.markdown("---")
                f1, f2, f3 = st.columns(3)
                f1.metric("Frequência Positiva", f"{pos_count} dias", f"{(pos_count/total)*100:.1f}%")
                f2.metric("Frequência Negativa", f"{neg_count} dias", f"-{(neg_count/total)*100:.1f}%")
                f3.metric("Nível (70% Acerto)", f"{alvo_n}%", f"Probabilidade: {acerto_n}%")

            # 4. MAPA DE GAPS
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

            # 5. PESQUISAR POR DATA (Sua solicitação)
            st.markdown("---")
            st.subheader("🔍 Verificar Resultado por Data")
            col_dt1, col_dt2 = st.columns([2, 1])
            with col_dt1:
                data_alvo = st.date_input("Escolha a data:", datetime.now())
            with col_dt2:
                if st.button('📅 Conferir Data', use_container_width=True):
                    res = df_ativo[df_ativo['Date'].dt.date == data_alvo]
                    if not res.empty: st.write(res[['Date', 'Ativo', 'Gap', 'Max_A', 'Min_A', 'Close']])
                    else: st.warning("Sem dados.")

            # 6. RADAR DE ELITE
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

            # 7. GRÁFICO
            st.markdown("---")
            st.subheader(f"📊 Histórico Visual - {ativo}")
            st.plotly_chart(px.bar(df_ativo.tail(50), x='Date', y=['Max_A', 'Min_A'], barmode='group'), use_container_width=True)
else:
    st.error("Erro no carregamento.")
