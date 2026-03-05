import streamlit as st
import yfinance as yf
import pandas as pd

st.title("📊 Meu Dashboard Quant: Abertura B3")

# 1. Escolha dos ativos (Pode ser uma lista fixa com todos da B3)
tickers = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA"]

def calcular_estatistica(ticker):
    # Busca histórico de 2 anos
    data = yf.download(ticker, period="2y", interval="1d")
    
    # Cálculo do GAP de hoje
    abertura_hoje = data['Open'].iloc[-1]
    fechamento_ontem = data['Close'].iloc[-2]
    gap = ((abertura_hoje / fechamento_ontem) - 1) * 100
    
    # Backtest rápido: Quantas vezes subiu após um GAP similar?
    # Ex: GAP menor que -1%
    casos_similares = data[((data['Open'] / data['Close'].shift(1)) - 1) * 100 < -1]
    acertos = len(casos_similares[casos_similares['Close'] > casos_similares['Open']])
    probabilidade = (acertos / len(casos_similares)) * 100 if len(casos_similares) > 0 else 0
    
    return gap, probabilidade, len(casos_similares)

# 2. Interface simples
if st.button('Atualizar Dados Agora'):
    resultados = []
    for t in tickers:
        g, p, n = calcular_estatistica(t)
        resultados.append({"Ativo": t, "GAP Hoje %": round(g, 2), "Prob. Alta %": round(p, 1), "Amostra": n})
    
    df_final = pd.DataFrame(resultados)
    st.table(df_final)
