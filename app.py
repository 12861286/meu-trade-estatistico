import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. CONFIGURAÇÃO MOBILE-FIRST E CSS CUSTOMIZADO ---
st.set_page_config(page_title="Quant B3 Mobile", layout="wide", initial_sidebar_state="collapsed")

# CSS para visual profissional e responsivo em celulares (Dark Mode e Cards)
st.markdown("""
    <style>
    /* Fundo escuro e fontes limpas */
    .main { background-color: #0e1117; color: #fafafa; font-family: 'Inter', sans-serif; }
    h1, h2, h3, h4 { color: #fafafa; font-weight: 700; }
    
    /* Configuração de Título Principal */
    .stApp header { display: none; } /* Esconde o header padrão do Streamlit */
    .app-header { text-align: center; padding: 1rem 0; background-color: #161b22; border-bottom: 1px solid #30363d; margin-bottom: 1rem; }
    .app-title { font-size: 1.5rem; margin: 0; color: #fafafa; }

    /* Estilização de Métricas (Cards) */
    [data-testid="stMetric"] { background-color: #161b22; padding: 1rem; border-radius: 8px; border: 1px solid #30363d; text-align: center; }
    div[data-testid="stMetricValue"] { color: #00ffcc; font-size: 1.8rem; }
    div[data-testid="stMetricLabel"] { color: #8b949e; font-size: 0.9rem; }

    /* Estilização de Inputs (Selectbox, DateInput, NumberInput) */
    .stSelectbox, .stDateInput, .stNumberInput { margin-bottom: 1rem; }
    div[data-baseweb="select"] { background-color: #161b22; border: 1px solid #30363d; border-radius: 4px; }
    input { background-color: #161b22 !important; color: #fafafa !important; border: 1px solid #30363d !important; }

    /* Estilização de Botões (Largo e Visível) */
    .stButton>button { width: 100% !important; border-radius: 4px; height: 3rem; background-color: #1f6feb; color: white; border: none; font-weight: 600; font-size: 1rem; }
    .stButton>button:hover { background-color: #388bfd; }

    /* Tabelas e Dataframes (Responsivos) */
    .stDataFrame, table { border: 1px solid #30363d !important; border-radius: 4px; }
    th { background-color: #161b22 !important; color: #fafafa !important; font-size: 0.8rem; }
    td { font-size: 0.8rem; color: #c9d1d9 !important; }
    
    /* Outros ajustes */
    div.stSuccess, div.stWarning, div.stInfo { background-color: #161b22 !important; color: #fafafa !important; border: 1px solid #30363d !important; }
    </style>
    """, unsafe_allow_html=True)

# Header Customizado no topo
st.markdown('<div class="app-header"><h1 class="app-title">🔍 Scanner Quant B3</h1></div>', unsafe_allow_html=True)

# --- 2. FUNÇÕES CORE (INALTERADAS) ---
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTn6i6FnZ7awsqEZLkxsIRSFHgRonDnBrK33Jvi-gATeCnUbSgWQp3J0aMzr7VqC_b2hySzKN_LEMxS/pub?output=csv"

@st.cache_data(ttl=600)
def carregar_dados():
    try:
        df = pd.read_csv(URL_PLANILHA)
        df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Ativo', 'Gap', 'Max_A', 'Min_A']
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Fech_Apos_Abertura'] = ((df['Close'] / df['Open']) - 1) * 100
        return df.dropna(subset=['Ativo'])
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

def obter_gap_hoje(ticker):
    try:
        dados = yf.download(ticker, period="2d", progress=False)
        if len(dados) < 2: return 0.0
        dados.columns = [c[0] if isinstance(c, tuple) else c for c in dados.columns]
        return round(((float(dados['Open'].iloc[-1]) / float(dados['Close'].iloc[-2])) - 1) * 100, 2)
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

# --- 3. FLUXO PRINCIPAL (PÁGINA ÚNICA, MOBILE-FIRST) ---
df_mestre = carregar_dados()
if not df_mestre.empty:
    lista_ativos = sorted(df_mestre['Ativo'].unique())
    
    # SELEÇÃO DO ATIVO (BEM VISÍVEL NO TOPO)
    st.subheader("Ativo Principal")
    ativo_principal = st.selectbox("Selecione ou digite o nome do ativo:", lista_ativos, key="main_ativo")
    
    gap_atual_ativo = obter_gap_hoje(ativo_principal)
    st.markdown(f'<div style="background-color:#161b22; padding:10px; border-radius:4px; text-align:center; color:#fafafa; border:1px solid #30363d; margin-bottom:1rem;"><b>GAP de hoje para {ativo_principal}: {gap_atual_ativo}%</b></div>', unsafe_allow_html=True)

    # PARÂMETROS DE CONFIGURAÇÃO (EMPILHADOS)
    with st.expander("⚙️ Configurações Globais", expanded=False):
        data_ini = st.date_input("Início do Backtest:", datetime.now() - timedelta(days=3*365), key="d_ini")
        min_acerto_r = st.number_input("Mínimo Acerto Radar (%)", 50, 95, 80, key="min_r")

    # BOTÃO AÇÃO (LARGO)
    st.markdown("<div style='margin-bottom: 2rem;'>", unsafe_allow_html=True)
    rodar_tudo = st.button("🚀 Rodar Estatística e Radar", use_container_width=True, key="run_all")
    st.markdown("</div>", unsafe_allow_html=True)

    # --- PROCESSAMENTO ---
    if rodar_tudo:
        # 1. RADAR DO DIA (RESULTADO GERAL PRIMEIRO)
        st.subheader("🚀 Radar do Dia")
        radar_data = []
        barra_r = st.progress(0)
        for i, tk in enumerate(lista_ativos):
            g_hoje = obter_gap_hoje(tk)
            df_h = df_mestre[(df_mestre['Ativo'] == tk) & (df_mestre['Date'] >= pd.to_datetime(data_ini)) & (df_mestre['Gap'] <= g_hoje + 0.15) & (df_mestre['Gap'] >= g_hoje - 0.15)]
            if len(df_h) >= 5:
                alvo, acerto = calcular_performance(df_h)
                if acerto >= min_acerto_r:
                    radar_data.append({"Ativo": tk, "Sinal": "COMPRA 🟢" if alvo > 0 else "VENDA 🔴", "Alvo": f"{alvo}%", "Acerto": f"{acerto}%"})
            barra_r.progress((i + 1) / len(lista_ativos))
        
        if radar_data:
            st.dataframe(pd.DataFrame(radar_data).sort_values("Acerto", ascending=False), use_container_width=True, hide_index=True)
        else:
            st.warning("Nenhuma oportunidade encontrada com os critérios definidos.")
        st.markdown("---")

        # 2. BACKTEST DETALHADO (DO ATIVO SELECIONADO)
        st.subheader(f"📊 Backtest: {ativo_principal}")
        st.markdown(f"**Amostra Baseada no GAP de Hoje ({gap_atual_ativo}%)**")
        
        df_hist = df_mestre[(df_mestre['Ativo'] == ativo_principal) & (df_mestre['Date'] >= pd.to_datetime(data_ini))]
        ev_esp = df_hist[(df_hist['Gap'] <= gap_atual_ativo + 0.15) & (df_hist['Gap'] >= gap_atual_ativo - 0.15)]
        
        if not ev_esp.empty:
            total = len(ev_esp)
            pos = len(ev_esp[ev_esp['Max_A'] > 0])
            alvo_f, acerto_f = calcular_performance(ev_esp)

            # Métricas em Cards (Empilhadas verticalmente no celular)
            c1, c2, c3, c4 = st.columns(4) # O Streamlit empilha automaticamente columns em mobile
            c1.metric("Amostra", f"{total} dias")
            c2.metric("Nível Alvo", f"{alvo_f}%")
            c3.metric("Assertividade", f"{acerto_f}%")
            c4.metric("Freq. Positiva", f"{(pos/total)*100:.1f}%")

            # Mapa de GAPs (Tabela compacta)
            st.markdown("---")
            st.markdown("**📋 Mapa de GAPs Histórico**")
            ranking = []
            for val in [x * 0.5 for x in range(-10, 11)]:
                t_gap = round(val, 2)
                ev_r = df_hist[(df_hist['Gap'] <= t_gap + 0.2) & (df_hist['Gap'] >= t_gap - 0.2)]
                if len(ev_r) >= 3:
                    yr, xr = calcular_performance(ev_r)
                    ranking.append({"GAP": f"{t_gap}%", "Dias": len(ev_r), "Alvo": f"{yr}%", "Acerto": f"{xr}%"})
            
            if ranking:
                st.dataframe(pd.DataFrame(ranking).sort_values("GAP", ascending=False), use_container_width=True, hide_index=True)
        st.markdown("---")

        # 3. CONFERIR DATA (Abaixo de tudo)
        st.subheader("🔍 Conferir Resultado por Data")
        with st.form("conferir_data_form"):
            col_d1, col_d2 = st.columns([1.5,1])
            with col_d1:
                data_sel = st.date_input("Data do Pregão:", datetime.now())
            with col_d2:
                # Botão submit dentro do form funciona bem no mobile
                st.markdown("<br>", unsafe_allow_html=True) # Ajuste visual
                verificar = st.form_submit_button("Consultar")
            
            if verificar:
                res = df_mestre[(df_mestre['Ativo'] == ativo_principal) & (df_mestre['Date'].dt.date == data_sel)]
                if not res.empty:
                    # Busca alvo estatístico antes desse dia
                    df_prev = df_mestre[(df_mestre['Ativo'] == ativo_principal) & (df_mestre['Date'] < pd.to_datetime(data_sel))]
                    alvo_p, _ = calcular_performance(df_prev)
                    max_r = res['Max_A'].iloc[0]
                    min_r = res['Min_A'].iloc[0]
                    ganhou = (alvo_p > 0 and max_r >= alvo_p) or (alvo_p < 0 and min_r <= alvo_p)
                    
                    st.markdown(f"### Detalhes de {data_sel.strftime('%d/%m/%Y')} - {ativo_principal}")
                    if ganhou: st.success("✅ OBJETIVO ATINGIDO")
                    else: st.warning("❌ NÃO ATINGIU")
                    
                    v1, v2 = st.columns(2)
                    v1.metric("GAP Abertura", f"{res['Gap'].iloc[0]}%")
                    v1.metric("Objetivo na Época", f"{alvo_p}%")
                    v2.metric("Máxima Real", f"{max_r}%")
                    v2.metric("Mínima Real", f"{min_r}%")
                else:
                    st.error("Dados não encontrados para esta data e ativo.")
else:
    st.error("Erro crítico: Banco de dados não carregado.")
