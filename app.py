import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime
import time

# 1. Configuração de layout
st.set_page_config(page_title="Scanner Quant B3", layout="wide")
st.title("🔍 Scanner de Estatística: Compra e Venda")

# Link da sua planilha (Já com as colunas novas Max_A e Min_A)
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSg04Li1XStwno4T5cQxMuUwDS35uzY2eRoLPi8zUIpxadZpBPTGMbd_IyftA-rbjpuc6_5TQfi0hXv/pub?output=csv"

@st.cache_data(ttl=3600)
def carregar_dados():
    try:
        df = pd.read_csv(URL_PLANILHA)
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Limpeza de números: Remove pontos de milhar que o Google Sheets coloca
        colunas_num = ['Open', 'High', 'Low', 'Close', 'Gap', 'Max_A', 'Min_A']
        for col in colunas_num:
            if col in df.columns:
                # Transforma em texto, remove o ponto e converte em número real
                df[col] = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df.dropna(subset=['Open', 'Close'])
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

def obter_gap_hoje(ticker):
    try:
        # Consulta rápida ao Yahoo para o GAP de hoje
        d = yf.download(ticker, period="2d", progress=False, timeout=10)
        if len(d) < 2: return 0.0
        d.columns = [c[0] if isinstance(c, tuple) else c for c in d.columns]
        fechamento_ontem = float(d['Close'].iloc[-2])
        abertura_hoje = float(d['Open'].iloc[-1])
        return round(((abertura_hoje / fechamento_ontem) - 1) * 100, 2)
    except:
        return 0.0

# --- INÍCIO DO APP ---
df_mestre = carregar_dados()

if not df_mestre.empty:
    lista_ativos = sorted(df_mestre['Ativo'].unique())
    
    st.subheader("Configurações do Backtest")
    ativo = st.selectbox("Selecione a ação:", lista_ativos)
    
    gap_atual = obter_gap_hoje(ativo)
    cor_caixa = "#d4edda" if gap_atual >= 0 else "#f8d7da"
    st.markdown(f'<div style="background-color:{cor_caixa}; padding:10px; border-radius:10px; text-align:center; color: black; margin-bottom: 20px;">'
                f'<b>GAP HOJE EM {ativo}: {gap_atual}%</b></div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        data_ini = st.date_input("Início do Histórico:", datetime(2020, 1, 1))
    with c2:
        gap_alvo = st.number_input("GAP para analisar (%):", value=gap_atual, step=0.1)
    with c3:
        min_acerto = st.number_input("Min. Acerto Radar (%):", value=80)

    if st.button('🚀 Rodar Estatística e Radar', use_container_width=True):
        # 1. Estatística Individual
        df_a = df_mestre[(df_mestre['Ativo'] == ativo) & (df_mestre['Date'] >= pd.to_datetime(data_ini))]
        # Filtra dias com GAP similar (margem de 0.15)
        ev = df_a[(df_a['Gap'] <= gap_alvo + 0.15) & (df_a['Gap'] >= gap_alvo - 0.15)]
        
        if not ev.empty:
            st.success(f"### Resultados para {ativo} com GAP de {gap_alvo}%")
            # Probabilidades (Alvo fixo de 0.5%)
            prob_compra = (len(ev[ev['Max_A'] >= 0.5]) / len(ev)) * 100
            prob_venda = (len(ev[ev['Min_A'] <= -0.5]) / len(ev)) * 100
            
            res1, res2 = st.columns(2)
            res1.metric("Probabilidade COMPRA (+0.5%)", f"{round(prob_compra, 1)}%")
            res2.metric("Probabilidade VENDA (-0.5%)", f"{round(prob_venda, 1)}%")
            
            st.write(f"**Total de ocorrências desse GAP:** {len(ev)} dias")
        
        # 2. Radar de Elite por Abas
        st.markdown("---")
        st.subheader("🚀 Radar de Elite (Oportunidades de Agora)")
        abas = st.tabs(["65%", "75%", "85%", "95%", "100%"])
        
        radar_lista = []
        with st.spinner("Escaneando mercado..."):
            # Analisa os primeiros 40 ativos para não travar
            for t in lista_ativos[:40]:
                g_h = obter_gap_hoje(t)
                hist_t = df_mestre[df_mestre['Ativo'] == t]
                similares = hist_t[(hist_t['Gap'] <= g_h + 0.15) & (hist_t['Gap'] >= g_h - 0.15)]
                
                if len(similares) >= 5:
                    acc_c = (len(similares[similares['Max_A'] >= 0.5]) / len(similares)) * 100
                    acc_v = (len(similares[similares['Min_A'] <= -0.5]) / len(similares)) * 100
                    
                    if acc_c >= acc_v and acc_c >= 65:
                        radar_lista.append({"Ativo": t, "GAP": g_h, "Lado": "🟢 COMPRA", "Acerto": acc_c})
                    elif acc_v > acc_c and acc_v >= 65:
                        radar_lista.append({"Ativo": t, "GAP": g_h, "Lado": "🔴 VENDA", "Acerto": acc_v})

        df_radar = pd.DataFrame(radar_lista)
        if not df_radar.empty:
            for i, corte in enumerate([65, 75, 85, 95, 100]):
                with abas[i]:
                    final = df_radar[df_radar['Acerto'] >= corte].sort_values('Acerto', ascending=False)
                    if not final.empty:
                        st.table(final)
                    else:
                        st.write("Nenhuma oportunidade neste nível.")
        
        # 3. Gráfico Histórico
        st.markdown("---")
        st.subheader(f"📊 Histórico de Volatilidade - {ativo}")
        fig = px.bar(df_a.tail(60), x='Date', y=['Max_A', 'Min_A'], barmode='group', title="Máximas e Mínimas após abertura")
        st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Aguardando dados da planilha...")
