import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import folium
from streamlit.components.v1 import html

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="FUNASA Dashboard", layout="wide")

# =========================
# ESTILO
# =========================
st.markdown("""
<style>
.main {
    background-color: #F4F7FC;
}
.card {
    background-color: white;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.markdown("""
<div style="
    background: linear-gradient(90deg, #0056b3, #4299E1);
    padding: 25px;
    border-radius: 15px;
    color: white;
    text-align: center;
    margin-bottom: 20px;
">
    <h1>📊 FUNASA Dashboard</h1>
    <p>Monitoramento Estratégico de Internações (AIH)</p>
</div>
""", unsafe_allow_html=True)

# =========================
# BANCO
# =========================
@st.cache_data
def carregar_dados():
    try:
        USUARIO, SENHA, HOST, PORTA, BANCO = "public_sqlserver", "funasa", "funasadb.dataiesb.com", "1433", "Saneamento"
        URL = f'mssql+pymssql://{USUARIO}:{SENHA}@{HOST}:{PORTA}/{BANCO}'

        engine = create_engine(URL)

        query = """
        SELECT TOP 10000 *
        FROM dbo.sus_aih
        WHERE ano_aih IN (2019, 2025)
        """

        df = pd.read_sql(query, engine)

        df['gasto'] = pd.to_numeric(df['vl_total'], errors='coerce').fillna(0)
        df['mes_aih'] = pd.to_numeric(df['mes_aih'], errors='coerce')
        df['ano_aih'] = df['ano_aih'].astype(str)

        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')

        return df

    except Exception as e:
        st.error(f"Erro ao conectar ao banco: {e}")
        return pd.DataFrame()

df = carregar_dados()

# =========================
# VERIFICAÇÃO
# =========================
if df.empty:
    st.warning("⚠️ Nenhum dado carregado.")
    st.stop()

# =========================
# FILTROS
# =========================
col1, col2 = st.columns(2)

with col1:
    ano = st.selectbox("Ano", sorted(df['ano_aih'].unique()))

with col2:
    regiao = st.selectbox("Região", df['regiao_nome'].unique())

df_filtrado = df[(df['ano_aih'] == ano) & (df['regiao_nome'] == regiao)]

# =========================
# FUNÇÃO REAL
# =========================
def formatar_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# =========================
# KPIs
# =========================
col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div class="card">
        <h4>Municípios</h4>
        <h2>{df_filtrado['nome_municipio'].nunique()}</h2>
    </div>
    """, unsafe_allow_html=True)

with col2:
    total = df[df['ano_aih'] == ano]['gasto'].sum()
    reg = df_filtrado['gasto'].sum()
    perc = (reg / total * 100) if total > 0 else 0

    st.markdown(f"""
    <div class="card">
        <h4>Representatividade</h4>
        <h2>{perc:.2f}%</h2>
    </div>
    """, unsafe_allow_html=True)

# =========================
# GRÁFICOS
# =========================
col1, col2 = st.columns(2)

with col1:
    df_bar = df_filtrado.groupby('mes_aih')['gasto'].sum().reset_index()
    fig_bar = px.bar(df_bar, x='mes_aih', y='gasto',
                     title="📊 Investimento por Mês")
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    df_pie = df_filtrado.groupby('uf_sigla')['gasto'].sum().reset_index()
    fig_pie = px.pie(df_pie, values='gasto', names='uf_sigla', hole=0.5,
                     title="📍 Distribuição por Estado")
    st.plotly_chart(fig_pie, use_container_width=True)

# =========================
# MAPA (FOLIUM TOP)
# =========================
st.subheader("🗺️ Mapa de Investimentos")

df_geo = df_filtrado.dropna(subset=['latitude', 'longitude'])

mapa = folium.Map(location=[-14.2, -51.9], zoom_start=4, tiles="cartodbpositron")

for _, row in df_geo.iterrows():

    cor = "#FFA500" if row['ano_aih'] == '2019' else "#0056b3"
    tamanho = max(4, min(row['gasto'] / 10000, 15))

    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=tamanho,
        color=cor,
        fill=True,
        fill_color=cor,
        fill_opacity=0.7,
        popup=f"""
        <b>{row['nome_municipio']}</b><br>
        UF: {row['uf_sigla']}<br>
        Ano: {row['ano_aih']}<br>
        Gasto: <b>{formatar_real(row['gasto'])}</b>
        """
    ).add_to(mapa)

html(mapa._repr_html_(), height=600)

# =========================
# TABELA
# =========================
st.subheader("📋 Dados detalhados")
st.dataframe(df_filtrado)