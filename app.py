import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine

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
# BANCO (QUERY CORRIGIDA)
# =========================
@st.cache_data
def carregar_dados():
    try:
        USUARIO, SENHA, HOST, PORTA, BANCO = "public_sqlserver", "funasa", "funasadb.dataiesb.com", "1433", "Saneamento"
        URL = f'mssql+pymssql://{USUARIO}:{SENHA}@{HOST}:{PORTA}/{BANCO}'

        engine = create_engine(URL)

        # 🔥 QUERY PROFISSIONAL (SEM PERDER MUNICÍPIOS)
        query = """
        SELECT 
            nome_municipio,
            uf_sigla,
            regiao_nome,
            ano_aih,
            AVG(latitude) as latitude,
            AVG(longitude) as longitude,
            SUM(vl_total) as gasto
        FROM dbo.sus_aih
        WHERE ano_aih IN (2019, 2025)
        GROUP BY nome_municipio, uf_sigla, regiao_nome, ano_aih
        """

        df = pd.read_sql(query, engine)

        df['gasto'] = pd.to_numeric(df['gasto'], errors='coerce').fillna(0)
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
    fig_bar = px.bar(df_filtrado.groupby('ano_aih')['gasto'].sum().reset_index(),
                     x='ano_aih', y='gasto',
                     title="📊 Investimento por Ano")
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    fig_pie = px.pie(df_filtrado, values='gasto', names='uf_sigla',
                     title="📍 Distribuição por Estado")
    st.plotly_chart(fig_pie, use_container_width=True)

# =========================
# MAPA IGUAL AO DASH
# =========================
st.subheader("🗺️ Mapa de Investimentos")

df_geo = df_filtrado.dropna(subset=['latitude', 'longitude'])

fig_mapa = px.scatter_mapbox(
    df_geo,
    lat="latitude",
    lon="longitude",
    color="ano_aih",
    size="gasto",
    hover_name="nome_municipio",
    custom_data=["gasto", "uf_sigla", "ano_aih"],
    mapbox_style="carto-positron",
    zoom=3.8,
    center={"lat": -14.2, "lon": -51.9},
    height=700,
    color_discrete_map={
        '2019': '#FFA500',
        '2025': '#0056b3'
    }
)

fig_mapa.update_traces(
    marker=dict(opacity=0.7),
    hovertemplate=
    "<b>%{hovertext}</b> (%{customdata[1]})<br>" +
    "Ano: %{customdata[2]}<br>" +
    "Gasto: <b>R$ %{customdata[0]:,.2f}</b><extra></extra>"
)

fig_mapa.update_layout(
    margin={"r":0,"t":0,"l":0,"b":0},
    legend=dict(title="Ano da AIH", bgcolor="white")
)

st.plotly_chart(fig_mapa, use_container_width=True)

# =========================
# TABELA
# =========================
st.subheader("📋 Dados detalhados")
st.dataframe(df_filtrado)