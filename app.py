import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Dashboard Quant", layout="wide")
st.title("📊 Meu Dashboard Quant: Abertura B3")

tickers = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA"]

def calcular_estatistica(ticker):
    try:
        data = yf.download(ticker, period="2y", interval="1d", progress=False)
        if len(data) < 2: return 0, 0, 0
        
        # Ajuste para pegar apenas o valor numérico
        abertura_hoje = float(data['Open'].iloc[-1])
        fechamento_ontem = float(data['Close'].iloc[-2])
        gap = ((abertura_hoje / fechamento_ontem) - 1) * 100
        
        casos_similares = data[((data['Open'] / data['Close'].shift(1)) - 1) * 100 < -1]
        acertos = len(casos_similares[casos_similares['Close'] > casos_similares['Open']])
        probabilidade = (acertos / len(casos_similares)) * 100 if len(casos_similares) > 0 else 0
        
        return round(gap, 2), round(probabilidade, 1), len(casos_similares)
    except:
        return 0, 0, 0

if st.button('Atualizar dados agora'):
    resultados = []
    for t in tickers:
        g, p, n = calcular_estatistica(t)
        resultados.append({"Ativo": t, "GAP Hoje %": g, "Prob. Alta %": p, "Amostra": n})
    
    df_final = pd.DataFrame(resultados)
    st.table(df_final)
