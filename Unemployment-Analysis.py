# app.py
from dash import Dash, dcc, html, callback_context
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ------------------ LOAD DATA ------------------
df = pd.read_csv(
    "C:\\Users\\amanv\\OneDrive\\Desktop\\my-react-app\\Unemployment in India.csv"
)

# ------------------ CLEAN DATA ------------------
df.columns = df.columns.str.strip()
df = df.dropna(subset=['Region'])

df['Date'] = (
    df['Date']
    .astype(str)
    .str.strip()
    .pipe(pd.to_datetime, format="%d-%m-%Y", errors='coerce')
)
df = df.dropna(subset=['Date'])
df['Year'] = df['Date'].dt.year

# ------------------ CONSTANT ------------------
NATIONAL_AVG = 7.8

# ------------------ TURQUOISE BLUE THEME ------------------
PAGE_BG = "#CFFAFE"
CARD_BG = "#99F6E4"
CHART_BG = "#5EEAD4"
DROPDOWN_BG = "#2DD4BF"

TEXT_COLOR = "#000000"

AREA_COLORS = {
    "Rural": "#0F766E",
    "Urban": "#BE185D"
}

STATE_COLORS = px.colors.qualitative.Set3

# ------------------ APP INIT ------------------
app = Dash(__name__)

# ------------------ DROPDOWN STYLE ------------------
dropdown_style = {
    'backgroundColor': DROPDOWN_BG,
    'color': '#000000',
    'border': '1px solid #0F766E',
    'borderRadius': '6px',
    'padding': '6px',
    'fontWeight': 'bold'
}

# ------------------ LAYOUT ------------------
app.layout = html.Div(
    [
        html.H1(
            "Unemployment Analysis Dashboard",
            style={'textAlign': 'center', 'color': '#000000'}
        ),

        dcc.Dropdown(
            id='state-dropdown',
            options=[{'label': s, 'value': s} for s in sorted(df['Region'].unique())],
            multi=True,
            placeholder="Select State(s)",
            style=dropdown_style
        ),

        dcc.Dropdown(
            id='area-dropdown',
            options=[
                {'label': 'All', 'value': 'All'},
                {'label': 'Rural', 'value': 'Rural'},
                {'label': 'Urban', 'value': 'Urban'}
            ],
            value='All',
            style=dropdown_style
        ),

        dcc.Dropdown(
            id='year-dropdown',
            options=[{'label': str(y), 'value': y} for y in sorted(df['Year'].unique())],
            placeholder="Select Year",
            style=dropdown_style
        ),

        html.Div(
            [
                html.Button(
                    "Submit",
                    id="submit-button",
                    style={
                        'backgroundColor': '#0F766E',
                        'color': 'white',
                        'border': 'none',
                        'padding': '10px 22px',
                        'borderRadius': '8px',
                        'cursor': 'pointer',
                        'fontWeight': 'bold'
                    }
                ),
                html.Button(
                    "Clear",
                    id="clear-button",
                    style={
                        'backgroundColor': '#BE185D',
                        'color': 'white',
                        'border': 'none',
                        'padding': '10px 22px',
                        'borderRadius': '8px',
                        'cursor': 'pointer',
                        'fontWeight': 'bold'
                    }
                )
            ],
            style={
                'display': 'flex',
                'gap': '20px',
                'justifyContent': 'center',
                'marginTop': '20px'
            }
        ),

        html.Div(id='kpi-container', style={'marginTop': '20px'}),

        html.Div(
            dcc.Graph(id='trend-graph'),
            style={'backgroundColor': CARD_BG, 'padding': '12px', 'marginTop': '20px'}
        ),

        html.Div(id='area-bar-container'),

        html.Div(
            dcc.Graph(id='state-ranking'),
            style={'backgroundColor': CARD_BG, 'padding': '12px', 'marginTop': '20px'}
        )
    ],
    style={'backgroundColor': PAGE_BG, 'padding': '25px'}
)

# ------------------ CALLBACK ------------------
@app.callback(
    [
        Output('kpi-container', 'children'),
        Output('trend-graph', 'figure'),
        Output('area-bar-container', 'children'),
        Output('state-ranking', 'figure'),
        Output('state-dropdown', 'value'),
        Output('area-dropdown', 'value'),
        Output('year-dropdown', 'value')
    ],
    [
        Input('submit-button', 'n_clicks'),
        Input('clear-button', 'n_clicks')
    ],
    [
        State('state-dropdown', 'value'),
        State('area-dropdown', 'value'),
        State('year-dropdown', 'value')
    ]
)
def update_dashboard(submit, clear, states, area, year):

    if callback_context.triggered_id == "clear-button":
        empty = go.Figure()
        return [], empty, [], empty, None, 'All', None

    if not states or not year:
        empty = go.Figure()
        return [], empty, [], empty, states, area, year

    filtered = df[df['Year'] == year]
    if area != 'All':
        filtered = filtered[filtered['Area'] == area]

    filtered_states = filtered[filtered['Region'].isin(states)]

    peak_row = filtered_states.loc[
        filtered_states['Estimated Unemployment Rate (%)'].idxmax()
    ]

    kpis = html.Div([
        html.H4(f"Average Unemployment: {filtered_states['Estimated Unemployment Rate (%)'].mean():.2f}%"),
        html.H4(f"Highest Unemployment: {peak_row['Estimated Unemployment Rate (%)']:.2f}%"),
        html.H4(f"Peak Month: {peak_row['Date'].strftime('%B')}")
    ])

    trend_df = (
        filtered_states
        .groupby(['Date', 'Region'], as_index=False)
        ['Estimated Unemployment Rate (%)']
        .mean()
        .sort_values('Date')
    )

    trend_fig = px.line(
        trend_df,
        x='Date',
        y='Estimated Unemployment Rate (%)',
        color='Region',
        markers=True,
        title=f"Unemployment Trend ({year})"
    )

    dates = trend_df['Date'].unique()
    trend_fig.add_trace(
        go.Scatter(
            x=dates,
            y=[NATIONAL_AVG] * len(dates),
            mode='lines',
            name='National Average',
            line=dict(color='black', dash='dash', width=3)
        )
    )

    trend_fig.update_layout(
        plot_bgcolor=CHART_BG,
        paper_bgcolor=CHART_BG,
        font_color='#000000'
    )

    # ---------------- AREA BAR FIX ----------------
    area_charts = []

    for state in states:
        state_df = filtered_states[filtered_states['Region'] == state]

        area_df = (
            state_df
            .groupby('Area')['Estimated Unemployment Rate (%)']
            .mean()
            .reset_index()
        )

        area_fig = px.bar(
            area_df,
            x='Area',
            y='Estimated Unemployment Rate (%)',
            color='Area',
            color_discrete_map=AREA_COLORS,
            text=area_df['Estimated Unemployment Rate (%)'].round(2),
            title=f"Rural vs Urban Unemployment – {state}"
        )

        # ✅ BAR WIDTH FIX
        bar_width = 0.35 if len(area_df) == 1 else 0.7
        area_fig.update_traces(width=bar_width)

        area_fig.update_layout(
            plot_bgcolor=CHART_BG,
            paper_bgcolor=CHART_BG,
            font_color='#000000',
            showlegend=False
        )

        area_charts.append(
            html.Div(
                dcc.Graph(figure=area_fig),
                style={'backgroundColor': CARD_BG, 'padding': '12px', 'marginTop': '20px'}
            )
        )

    rank_df = (
        filtered
        .groupby('Region')['Estimated Unemployment Rate (%)']
        .mean()
        .reset_index()
        .sort_values('Estimated Unemployment Rate (%)', ascending=False)
        .head(5)
        .round(2)
    )

    rank_fig = px.bar(
        rank_df,
        x='Region',
        y='Estimated Unemployment Rate (%)',
        text='Estimated Unemployment Rate (%)',
        color='Region',
        color_discrete_sequence=STATE_COLORS,
        title=f"Top 5 States by Unemployment ({year})"
    )

    rank_fig.update_layout(
        plot_bgcolor=CHART_BG,
        paper_bgcolor=CHART_BG,
        font_color='#000000',
        showlegend=False
    )

    return kpis, trend_fig, area_charts, rank_fig, states, area, year


# ------------------ RUN ------------------
if __name__ == "__main__":
    app.run_server(debug=True)
