import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Scanner B3 - Estatística", layout="wide")
st.title("🔍 Scanner de Abertura: Estatística Quant")

# --- O SEU LINK DA PLANILHA (Sempre atualizado aqui) ---
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTn6i6FnZ7awsqEZLkxsIRSFHgRonDnBrK33Jvi-gATeCnUbSgWQp3J0aMzr7VqC_b2hySzKN_LEMxS/pub?output=csv"

@st.cache_data(ttl=600)
def carregar_dados():
    try:
        # Lê a planilha publicada como CSV
        df = pd.read_csv(URL_PLANILHA)
        
        # Ajuste de colunas caso o Google envie tudo grudado
        if len(df.columns) == 1:
            col_id = df.columns[0]
            df = df[col_id].str.split(',', expand=True)
            df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Ativo', 'Gap', 'Max_A', 'Min_A']

        # Converte as colunas para o formato certo (Números e Data)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        cols_numericas = ['Open', 'High', 'Low', 'Close', 'Gap', 'Max_A', 'Min_A']
        for col in cols_numericas:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        return df.dropna(subset=['Ativo', 'Open'])
    except Exception as e:
        st.error(f"Erro ao carregar dados da planilha: {e}")
        return pd.DataFrame()

# --- INTERFACE DO USUÁRIO ---
df_mestre = carregar_dados()

if not df_mestre.empty:
    # Menu lateral para escolher o ativo
    lista_ativos = sorted(df_mestre['Ativo'].unique())
    ativo_selecionado = st.selectbox("Selecione o Ativo para análise:", lista_ativos)
    
    # Busca o preço de agora no Yahoo Finance para saber o GAP do dia
    try:
        dados_hoje = yf.download(ativo_selecionado, period="2d", progress=False)
        # Ajuste para evitar erro de nomes de colunas do Yahoo
        dados_hoje.columns = [c[0] if isinstance(c, tuple) else c for c in dados_hoje.columns]
        
        preco_abertura = dados_hoje['Open'].iloc[-1]
        preco_fechamento_ontem = dados_hoje['Close'].iloc[-2]
        gap_atual = round(((preco_abertura / preco_fechamento_ontem) - 1) * 100, 2)
    except:
        gap_atual = 0.0

    st.subheader(f"📊 Análise para {ativo_selecionado}")
    st.info(f"O GAP de hoje é de: **{gap_atual}%**")

    if st.button('🚀 Calcular Probabilidades Históricas'):
        # Filtra o histórico apenas para esse ativo e GAPs parecidos (margem de 0.15%)
        df_historico = df_mestre[df_mestre['Ativo'] == ativo_selecionado]
        eventos = df_historico[(df_historico['Gap'] <= gap_atual + 0.15) & 
                               (df_historico['Gap'] >= gap_atual - 0.15)]
        
        if not eventos.empty:
            # Mostra os resultados em cartões bonitos
            col1, col2, col3 = st.columns(3)
            col1.metric("Vezes que ocorreu", len(eventos))
            
            # Cálculo de assertividade (Alvo de 0.50% de lucro)
            acerto_compra = (len(eventos[eventos['Max_A'] >= 0.50]) / len(eventos)) * 100
            acerto_venda = (len(eventos[eventos['Min_A'] <= -0.50]) / len(eventos)) * 100
            
            col2.metric("Chance de Subir +0.50%", f"{round(acerto_compra, 1)}%")
            col3.metric("Chance de Cair -0.50%", f"{round(acerto_venda, 1)}%")
            
            # Gráfico de barras das últimas 30 vezes
            st.write("---")
            st.write("### Últimas 30 oscilações após esse GAP")
            fig = px.bar(df_historico.tail(30), x='Date', y=['Max_A', 'Min_A'], 
                         title="Máximas e Mínimas do Dia",
                         labels={'value': 'Oscilação %', 'Date': 'Data'},
                         barmode='group')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Não encontramos esse GAP exato no histórico. Tente outro ativo.")
else:
    st.error("A planilha está vazia ou o link está incorreto. Verifique se você publicou como CSV.")

st.markdown("---")
st.caption("Desenvolvido para análise quantitativa da B3.")
