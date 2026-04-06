import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.express as px
import pandas as pd
from sqlalchemy import create_engine

# ==========================================================
# 1. CONEXÃO E TRATAMENTO DE DADOS (SQL SERVER)
# ==========================================================
USUARIO, SENHA, HOST, PORTA, BANCO = "public_sqlserver", "funasa", "funasadb.dataiesb.com", "1433", "Saneamento"
URL_CONEXAO = f'mssql+pymssql://{USUARIO}:{SENHA}@{HOST}:{PORTA}/{BANCO}'

def carregar_dados():
    engine = create_engine(URL_CONEXAO)
    query = "SELECT * FROM dbo.sus_aih"
    df = pd.read_sql(query, engine)

    df['gasto'] = pd.to_numeric(df['vl_total'], errors='coerce').fillna(0)
    df['mes_aih'] = pd.to_numeric(df['mes_aih'], errors='coerce').astype(int)
    df['ano_aih'] = pd.to_numeric(df['ano_aih'], errors='coerce').astype(str).str.replace(".0", "", regex=False)

    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')

    df['gasto_label'] = df['gasto'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    # Mantendo apenas os anos desejados
    df = df[df['ano_aih'].isin(['2019', '2025'])]

    return df

df_raw = carregar_dados()

# ==========================================================
# 2. CONFIGURAÇÃO DE ESTILO
# ==========================================================
app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])

COLORS = {
    'bg': '#F4F7FC',
    'card': '#FFFFFF',
    'text': '#2D3748',
    'accent': '#0056b3',
    'border': '#E2E8F0',
    'success': '#28a745',
    'info': '#4299E1'
}

app.layout = html.Div(style={'backgroundColor': COLORS['bg'], 'minHeight': '100vh', 'fontFamily': 'Segoe UI, sans-serif'}, children=[

    # Navbar Superior
    html.Div(style={'backgroundColor': COLORS['accent'], 'padding': '15px 40px', 'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'boxShadow': '0 2px 10px rgba(0,0,0,0.1)'}, children=[
        html.Div([
            html.H3("FUNASA", style={'color': 'white', 'margin': '0', 'fontWeight': '600'}),
            html.P("Monitoramento Estratégico de Internações (AIH)", style={'color': 'rgba(255,255,255,0.8)', 'margin': '0', 'fontSize': '13px'})
        ]),
        html.Img(src="https://www.gov.br/funasa/pt-br/imagens/logo-funasa.png", style={'height': '40px', 'filter': 'brightness(0) invert(1)'})
    ]),

    # Container do Conteúdo
    html.Div(style={'padding': '20px 40px'}, children=[

        dcc.Tabs(id="tabs-navegacao", value='tab-1', children=[
            dcc.Tab(label='📈 Painel de Indicadores', value='tab-1',
                    style={'padding': '12px', 'border': 'none', 'backgroundColor': 'transparent', 'color': COLORS['text']},
                    selected_style={'padding': '12px', 'border': 'none', 'borderBottom': f'4px solid {COLORS["accent"]}', 'fontWeight': 'bold', 'color': COLORS['accent']}),
            dcc.Tab(label='🗺️ Distribuição Geográfica', value='tab-2',
                    style={'padding': '12px', 'border': 'none', 'backgroundColor': 'transparent', 'color': COLORS['text']},
                    selected_style={'padding': '12px', 'border': 'none', 'borderBottom': f'4px solid {COLORS["accent"]}', 'fontWeight': 'bold', 'color': COLORS['accent']}),
        ], style={'marginBottom': '20px'}),

        html.Div(id='conteudo-pagina')
    ])
])

# ==========================================================
# 3. LÓGICA E RENDERIZAÇÃO
# ==========================================================

@app.callback(Output('conteudo-pagina', 'children'),
              Input('tabs-navegacao', 'value'))
def renderizar_conteudo(tab):
    if tab == 'tab-1':
        return html.Div([
            # Linha de Filtros e KPIs
            html.Div(className='row', style={'marginBottom': '25px', 'display': 'flex', 'alignItems': 'stretch', 'gap': '20px'}, children=[
                # Menu de Filtros
                html.Div(className='four columns', style={'display': 'flex', 'flexDirection': 'column', 'gap': '15px'}, children=[
                    html.Div(style={'backgroundColor': COLORS['card'], 'padding': '20px', 'borderRadius': '15px', 'boxShadow': '0 4px 15px rgba(0,0,0,0.05)'}, children=[
                        html.Label("Selecione o Ano:", style={'fontWeight': '600', 'color': COLORS['text'], 'marginBottom': '5px', 'display': 'block'}),
                        dcc.Dropdown(
                            id='filtro-ano',
                            options=[{'label': i, 'value': i} for i in sorted(df_raw['ano_aih'].unique(), reverse=True)],
                            value=df_raw['ano_aih'].unique()[0],
                            style={'borderRadius': '8px'}
                        ),
                    ]),
                    html.Div(style={'backgroundColor': COLORS['card'], 'padding': '20px', 'borderRadius': '15px', 'boxShadow': '0 4px 15px rgba(0,0,0,0.05)'}, children=[
                        html.Label("Selecione a Região:", style={'fontWeight': '600', 'color': COLORS['text'], 'marginBottom': '5px', 'display': 'block'}),
                        dcc.Dropdown(
                            id='filtro-regiao',
                            options=[{'label': i, 'value': i} for i in sorted(df_raw['regiao_nome'].unique())],
                            value=df_raw['regiao_nome'].unique()[0],
                            style={'borderRadius': '8px'}
                        ),
                    ]),
                ]),
                # Cartões de Resumo Rápido
                html.Div(className='eight columns', style={'display': 'flex', 'gap': '20px'}, children=[
                    html.Div(style={'backgroundColor': COLORS['card'], 'padding': '25px', 'borderRadius': '15px', 'flex': '1', 'boxShadow': '0 4px 15px rgba(0,0,0,0.05)', 'borderTop': f'5px solid {COLORS["accent"]}'}, children=[
                        html.H6("Municípios Atendidos", style={'color': '#718096', 'margin': '0'}),
                        html.H3(id='kpi-municipios', style={'margin': '10px 0 0 0', 'fontWeight': 'bold'})
                    ]),
                    html.Div(style={'backgroundColor': COLORS['card'], 'padding': '25px', 'borderRadius': '15px', 'flex': '1', 'boxShadow': '0 4px 15px rgba(0,0,0,0.05)', 'borderTop': f'5px solid {COLORS["success"]}'}, children=[
                        html.H6("Representatividade no Estado (Percentual)", style={'color': '#718096', 'margin': '0'}),
                        html.H3(id='kpi-representatividade', style={'margin': '10px 0 0 0', 'fontWeight': 'bold'}),
                        html.P(id='texto-apoio-representatividade', style={'fontSize': '12px', 'color': '#718096', 'marginTop': '5px'})
                    ])
                ])
            ]),

            # Gráficos Dinâmicos
            html.Div(className='row', style={'marginBottom': '25px'}, children=[
                html.Div(className='seven columns', children=[
                    html.Div(style={'backgroundColor': COLORS['card'], 'padding': '20px', 'borderRadius': '15px', 'boxShadow': '0 4px 15px rgba(0,0,0,0.05)'}, children=[
                        dcc.Graph(id='grafico-barras-moderno')
                    ])
                ]),
                html.Div(className='five columns', children=[
                    html.Div(style={'backgroundColor': COLORS['card'], 'padding': '20px', 'borderRadius': '15px', 'boxShadow': '0 4px 15px rgba(0,0,0,0.05)'}, children=[
                        dcc.Graph(id='grafico-pizza-moderno')
                    ])
                ])
            ]),

            # Tabela
            html.Div(className='row', children=[
                html.Div(className='twelve columns', children=[
                    html.Div(style={'backgroundColor': COLORS['card'], 'padding': '20px', 'borderRadius': '15px', 'boxShadow': '0 4px 15px rgba(0,0,0,0.05)'}, children=[
                        html.H5("Detalhamento por Município", style={'color': COLORS['text'], 'fontWeight': '600', 'marginBottom': '15px'}),
                        dash_table.DataTable(
                            id='tabela-detalhada',
                            columns=[
                                {"name": "Município", "id": "nome_municipio"},
                                {"name": "UF", "id": "uf_sigla"},
                                {"name": "Mês", "id": "mes_aih"},
                                {"name": "Ano", "id": "ano_aih"},
                                {"name": "Investimento (R$)", "id": "gasto_label"}
                            ],
                            page_size=10,
                            sort_action="native",
                            # --- ALTERAÇÃO AQUI: ATIVA O FILTRO PARA ESCREVER O NOME ---
                            filter_action="native",
                            filter_options={"placeholder_text": "Filtrar..."},
                            # ---------------------------------------------------------
                            style_header={'backgroundColor': COLORS['bg'], 'fontWeight': 'bold', 'border': f'1px solid {COLORS["border"]}'},
                            style_cell={'textAlign': 'left', 'padding': '10px', 'fontFamily': 'Segoe UI, sans-serif', 'border': f'1px solid {COLORS["border"]}'},
                            style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': '#fcfdff'}],
                            style_as_list_view=True
                        )
                    ])
                ])
            ])
        ])

    elif tab == 'tab-2':
        df_geo = df_raw.dropna(subset=['latitude', 'longitude'])
        fig_mapa = px.scatter_mapbox(
            df_geo, lat="latitude", lon="longitude", color="ano_aih", size="gasto",
            hover_name="nome_municipio", custom_data=["gasto_label", "uf_sigla", "ano_aih"],
            mapbox_style="carto-positron",
            zoom=3.8, center={"lat": -14.2, "lon": -51.9}, height=750,
            color_discrete_map={'2019': '#FFA500', '2025': '#0056b3'}
        )
        fig_mapa.update_traces(hovertemplate="<b>%{hovertext}</b> (%{customdata[1]})<br>Ano: %{customdata[2]}<br>Gasto: <b>%{customdata[0]}</b><extra></extra>")
        fig_mapa.update_layout(
            margin={"r":0,"t":0,"l":0,"b":0},
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(title="Ano da AIH", yanchor="top", y=0.98, xanchor="left", x=0.02, bgcolor="white", font=dict(size=12)),
            mapbox=dict(bearing=0, pitch=0, zoom=3.8)
        )

        return html.Div(style={'backgroundColor': COLORS['card'], 'padding': '15px', 'borderRadius': '15px', 'boxShadow': '0 10px 25px rgba(0,0,0,0.05)', 'border': f'1px solid {COLORS["border"]}'}, children=[
            html.H4("Visualização Geoespacial de Investimentos", style={'textAlign': 'center', 'color': COLORS['text'], 'padding': '10px 0', 'fontWeight': '600'}),
            dcc.Graph(id='mapa-investimentos', figure=fig_mapa, config={'displayModeBar': True, 'scrollZoom': True})
        ])

@app.callback(
    [Output('kpi-municipios', 'children'),
     Output('kpi-representatividade', 'children'),
     Output('texto-apoio-representatividade', 'children'),
     Output('grafico-barras-moderno', 'figure'),
     Output('grafico-pizza-moderno', 'figure'),
     Output('tabela-detalhada', 'data')],
    [Input('filtro-ano', 'value'),
     Input('filtro-regiao', 'value')]
)
def atualizar_dash_e_charts(ano, regiao):
    dff = df_raw[(df_raw['ano_aih'] == ano) & (df_raw['regiao_nome'] == regiao)]

    gasto_regiao = dff['gasto'].sum()
    gasto_total_ano = df_raw[df_raw['ano_aih'] == ano]['gasto'].sum()

    if gasto_total_ano > 0:
        percentual = (gasto_regiao / gasto_total_ano) * 100
        representatividade_val = f"{percentual:.2f}%".replace(".", ",")
    else:
        representatividade_val = "0,00%"

    municipios_count = f"{dff['nome_municipio'].nunique()}"
    texto_apoio = f"Este investimento representa {representatividade_val} do total nacional no ano de {ano}."

    df_bar = dff.groupby('mes_aih')['gasto'].sum().reset_index()
    fig_bar = px.bar(df_bar, x='mes_aih', y='gasto',
                    title=f'Investimento Mensal em {ano}: {regiao}',
                    labels={'gasto': 'Investimento', 'mes_aih': 'Mês'},
                    color_discrete_sequence=[COLORS['accent']])
    fig_bar.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color=COLORS['text'], title_font_size=16)
    fig_bar.update_yaxes(tickprefix="R$ ", gridcolor='#EDF2F7')
    fig_bar.update_xaxes(tickmode='linear', tick0=1, dtick=1)

    df_uf = dff.groupby('uf_sigla')['gasto'].sum().reset_index()
    fig_pie = px.pie(df_uf, values='gasto', names='uf_sigla', hole=.5,
                    title=f'Distribuição por Estado ({regiao})',
                    color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_pie.update_traces(textinfo='percent', hovertemplate="UF: %{label}<br>Gasto: <b>R$ %{value:,.2f}</b><extra></extra>")
    fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color=COLORS['text'], title_font_size=16, showlegend=True, legend=dict(orientation="h", y=-0.1))

    tabela_data = dff.to_dict('records')

    return municipios_count, representatividade_val, texto_apoio, fig_bar, fig_pie, tabela_data

# ==========================================================
# 4. EXECUÇÃO
# ==========================================================
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8050)