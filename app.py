import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import googlemaps

# 1. Configurações
st.set_page_config(page_title="Router Master Pro", layout="wide")
api_key = "AIzaSyD5AiteGn7kOWmdLT3qgF5d1ODaxMxVMAM"
gmaps = googlemaps.Client(key=api_key)

st.title("🚚 Roteirizador Shopee: Otimização por Vizinhança")

uploaded_file = st.file_uploader("Suba sua planilha", type=['csv', 'xlsx'])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    
    # IMPORTANTE: Agrupar por Bairro antes de otimizar evita que ele saia da zona e volte
    if 'Bairro' in df.columns:
        df = df.sort_values(by=['Bairro']).reset_index(drop=True)
    
    if 'Parada Original' not in df.columns:
        df['Parada Original'] = range(1, len(df) + 1)

    locais = df[['Latitude', 'Longitude']].values.tolist()
    df_final = pd.DataFrame()
    polylines_totais = []
    tamanho_lote = 23 

    try:
        with st.spinner('Refinando rota por bairros...'):
            for i in range(0, len(locais), tamanho_lote):
                fim = min(i + tamanho_lote, len(locais))
                lote = locais[i:fim]
                if len(lote) < 2: continue

                res = gmaps.directions(lote[0], lote[-1], waypoints=lote[1:-1], optimize_waypoints=True, mode="driving")

                if res:
                    ordem = res[0]['waypoint_order']
                    indices = [0] + [idx + 1 for idx in ordem] + [len(lote) - 1]
                    pedaco = df.iloc[i:fim].iloc[indices].copy()
                    df_final = pd.concat([df_final, pedaco])
                    
                    caminho = googlemaps.convert.decode_polyline(res[0]['overview_polyline']['points'])
                    polylines_totais.append([(p['lat'], p['lng']) for p in caminho])

        df_final = df_final.drop_duplicates(subset=['Latitude', 'Longitude']).reset_index(drop=True)
        df_final['Nova_Sequencia'] = range(1, len(df_final) + 1)

        m = folium.Map(location=[df_final['Latitude'].mean(), df_final['Longitude'].mean()], zoom_start=13)

        for linha in polylines_totais:
            folium.PolyLine(linha, color="#007AFF", weight=5, opacity=0.7).add_to(m)

        for i, row in df_final.iterrows():
            seq, orig = int(row['Nova_Sequencia']), int(row['Parada Original'])
            
            # Balão Bicolor com Números Reforçados (Z-index alto)
            icon_html = f'''
                <div style="position: relative; width: 42px; height: 52px;">
                    <svg viewBox="0 0 384 512" style="width: 42px; height: 52px; position: absolute; z-index: 1;">
                        <defs>
                            <linearGradient id="grad{i}" x1="0%" y1="0%" x2="0%" y2="100%">
                                <stop offset="50%" style="stop-color:#007AFF;stop-opacity:1" />
                                <stop offset="50%" style="stop-color:#343a40;stop-opacity:1" />
                            </linearGradient>
                        </defs>
                        <path fill="url(#grad{i})" d="M172.268 501.67C26.97 291.031 0 269.413 0 192 0 85.961 85.961 0 192 0s192 85.961 192 192c0 77.413-26.97 99.031-172.268 309.67-9.535 13.774-29.93 13.773-39.464 0z"/>
                    </svg>
                    <div style="position: absolute; top: 5px; width: 42px; text-align: center; color: white; font-weight: bold; font-size: 12px; z-index: 10; pointer-events: none;">{seq}</div>
                    <div style="position: absolute; top: 20px; width: 42px; text-align: center; color: #00FF00; font-weight: bold; font-size: 10px; z-index: 10; pointer-events: none;">{orig}</div>
                </div>'''
            folium.Marker([row['Latitude'], row['Longitude']], icon=folium.DivIcon(icon_size=(42, 52), icon_anchor=(21, 52), html=icon_html)).add_to(m)

        folium_static(m, width=1100)
        
        # Lista de GPS
        for _, row in df_final.iterrows():
            c1, c2 = st.columns([5, 1])
            c1.write(f"**{int(row['Nova_Sequencia'])}º** — {row['Destination Address']}")
            c2.link_button("🚗 GPS", f"https://www.google.com/maps/dir/?api=1&destination={row['Latitude']},{row['Longitude']}&travelmode=driving")

    except Exception as e:
        st.error(f"Erro: {e}")
