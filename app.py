import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="FUNASA Dashboard", layout="wide")

# =========================
# ESTILO GLOBAL
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
# HEADER BONITO
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
# BANCO (COM CACHE + LIMITE)
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
# KPIs BONITOS
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
# MAPA CORRIGIDO
# =========================
st.subheader("🗺️ Mapa de Investimentos")

df_geo = df_filtrado.dropna(subset=['latitude', 'longitude'])

fig_map = px.scatter_mapbox(
    df_geo,
    lat="latitude",
    lon="longitude",
    size="gasto",
    color="ano_aih",
    zoom=3.5,
    center={"lat": -14.2, "lon": -51.9},
    height=500
)

fig_map.update_layout(mapbox_style="carto-positron")

fig_map.update_traces(
    hovertemplate="<b>Município</b><br>Lat: %{lat}<br>Lon: %{lon}<br>Gasto: %{marker.size}<extra></extra>"
)

st.plotly_chart(fig_map, use_container_width=True)

# =========================
# TABELA
# =========================
st.subheader("📋 Dados detalhados")
st.dataframe(df_filtrado)