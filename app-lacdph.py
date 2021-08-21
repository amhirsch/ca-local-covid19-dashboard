import json
import os
import dash
import dash_core_components as dcc
from dash_core_components.RadioItems import RadioItems
import dash_html_components as html
from dash.dependencies import Input, Output
from dash_html_components.A import A
from dash_html_components.Div import Div
from dash_html_components.Label import Label
import plotly.express as px
import pandas as pd

EP_DATE = 'ep_date'
CSA = 'csa'
DPH_CASE_COLS = 'cases_{}day', 'case_{}day_rate', 'adj_case_{}day_rate'

YAXIS_RANGE = 400, 1000, 1600

LOW = 'Low'
MODERATE = 'Moderate'
SUBSTANTIAL = 'Substantial'
HIGH = 'High'
CDC_COMMUNITY_TRANSMISSION_COLORS = {
    LOW: '#1d8aff',
    MODERATE: '#fff70e',
    SUBSTANTIAL: '#ff7134',
    HIGH: '#ff0000'
}
CDC_COMMUNITY_TRANSMISSION_ORDER = {
    'Level of Community Transmission': [HIGH, SUBSTANTIAL, MODERATE, LOW]
}


def determine_cdc_community_transmission(case_rate: int) -> str:
    if case_rate < 10:
        return 'Low'
    if case_rate < 50:
        return 'Moderate'
    if case_rate < 100:
        return 'Substantial'
    if case_rate >= 100:
        return 'High'


px.set_mapbox_access_token(os.environ['MAPBOX_DASH_LAC'])

df_dph_7day, df_dph_14day = [
    pd.read_csv(f'LA_County_Covid19_CSA_{x}day_case_death_table.csv',
                parse_dates=[EP_DATE],
                infer_datetime_format=True) for x in (7, 14)
]

last_day = df_dph_7day[EP_DATE].max() - pd.Timedelta(5, 'days')
df_dph_7day = df_dph_7day[(df_dph_7day[EP_DATE].notna()) &
                          (df_dph_7day[EP_DATE] <= last_day)].copy()
df_dph_14day = df_dph_14day[(df_dph_14day[EP_DATE].notna()) &
                            (df_dph_14day[EP_DATE] <= last_day)].copy()

for df in df_dph_7day, df_dph_14day:
    df.drop(columns=['Unnamed: 0'], inplace=True)
    df.rename(columns={'geo_merge': CSA}, inplace=True)
    df.sort_values([EP_DATE, CSA], inplace=True)
    df.reset_index(drop=True, inplace=True)
    df[CSA] = df[CSA].convert_dtypes()
    df['population'] = df['population'].astype('int')
    for stat in 'case', 'death':
        df[f'{stat}_rate_unstable'] = df[f'{stat}_rate_unstable'].apply(
            lambda x: x == '^')

for col in DPH_CASE_COLS:
    df_dph_7day[col.format(7)] = df_dph_7day[col.format(7)].astype('int')
    df_dph_14day[col.format(14)] = df_dph_14day[col.format(14)] / 2

for df, col in (df_dph_7day, 'case_7day_rate'), (df_dph_14day,
                                                 'case_14day_rate'):
    df['Level of Community Transmission'] = df[col].apply(
        determine_cdc_community_transmission).convert_dtypes()

csa_list = list(df_dph_7day['csa'].unique())
csa_list.sort()

with open('lac-csa-orig.geojson') as f:
    geojson = json.load(f)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

LABEL = 'label'
VALUE = 'value'
app.layout = html.Div([
    dcc.Tabs([
        dcc.Tab([
            html.Div([
                html.Label('Countywide Statistical Area',
                           htmlFor='selected-csa'),
                dcc.Dropdown(id='selected-csa',
                             options=[{
                                 LABEL: i,
                                 VALUE: i
                             } for i in csa_list],
                             value='City of Burbank'),
                html.Div(
                    [
                        html.Div([
                            html.Label('Date Range', htmlFor='time-selector'),
                            dcc.RadioItems(
                                id='time-selector',
                                options=[{
                                    LABEL: 'All time',
                                    VALUE: 0
                                }, {
                                    LABEL: '4 months',
                                    VALUE: 120
                                }],
                                value=120,
                                labelStyle={'display': 'inline-block'})
                        ]),
                        html.Div([
                            html.Label('Observational Period',
                                       htmlFor='observational-period'),
                            dcc.RadioItems(
                                id='observational-period',
                                options=[{
                                    LABEL: '7 day',
                                    VALUE: 7
                                }, {
                                    LABEL: '14 day',
                                    VALUE: 14
                                }],
                                value=7,
                                labelStyle={'display': 'inline-block'})
                        ],)
                    ],
                    style={
                        'display': 'flex',
                        'flexDirection': 'row',
                        'columnGap': '1em',
                        'paddingLeft': '1em'
                    })
            ],
                     style={
                         'width': '35em',
                         'paddingLeft': '2em'
                     }),
            dcc.Graph(id='csa-ts', style={'maxWidth': '50em'})
        ],
                label='Time series'),
        dcc.Tab([
            html.Div(
                [
                    html.Div([
                        html.Label('Date (with 7 day lag)', htmlFor='map-date'),
                        dcc.RadioItems(id='map-date',
                                       options=[{
                                           LABEL: 'Current',
                                           VALUE: 0
                                       }, {
                                           LABEL: '30 days ago',
                                           VALUE: 30
                                       }],
                                       value=0)
                    ]),
                    html.Div([
                        html.Label('Color key', htmlFor='map-discreet-level'),
                        dcc.RadioItems(
                            id='map-discreet-level',
                            options=[{
                                LABEL: 'Choropleth',
                                VALUE: 0
                            }, {
                                LABEL: 'CDC Level of Community Transmission',
                                VALUE: 1
                            }],
                            value=0)
                    ])
                ],
                style={
                    'display': 'flex',
                    'flexDirection': 'row',
                    'columnGap': '1em',
                    'paddingLeft': '1em'
                }),
            dcc.Graph(id='csa-map', style={'maxHeight': '90%'})
        ],
                label='Choropleth'),
    ]),
    html.P(['Data through 6:00 PM PDT, ',
            html.Strong('August 18, 2021')]),
    html.P([
        'Source: Los Angeles County Department of Public Health ',
        html.
        A('COVID-19 Data Dashboard',
          href=
          'http://dashboard.publichealth.lacounty.gov/covid19_surveillance_dashboard/'
         ),
        html.P([
            'Github: ',
            html.A('amhirsch/lac-covid19-dashboard',
                   href='https://github.com/amhirsch/lac-covid19-dashboard')
        ])
    ])
])


@app.callback(Output('csa-ts', 'figure'), Input('selected-csa', 'value'),
              Input('time-selector', 'value'),
              Input('observational-period', 'value'))
def update_lacdph_graph(selected_csa, time_selector, observational_period):
    if observational_period == 7:
        df = df_dph_7day
    elif observational_period == 14:
        df = df_dph_14day
    else:
        raise ValueError('Invalid observational period. Options are 7 or 14.')

    df_csa = df[df['csa'] == selected_csa]
    dep_var = f'case_{observational_period}day_rate'

    if time_selector > 0:
        df_csa = df_csa[df_csa['ep_date'] >= (
            last_day - pd.Timedelta(time_selector, 'days'))]

    local_max = df_csa[dep_var].max()
    if local_max <= max(YAXIS_RANGE):
        yaxis_max = [x for x in YAXIS_RANGE if x >= local_max][0]
    else:
        yaxis_max = local_max * 1.05

    fig = px.line(
        df_csa,
        'ep_date',
        dep_var,
        hover_data=[f'cases_{observational_period}day', 'case_rate_unstable'])
    fig.update_layout(
        title_text=f'{selected_csa} COVID-19 Case Rate per 100,000 people')
    fig.update_xaxes(title_text='Episode date')
    fig.update_yaxes(
        title_text=f'7 day cumulative cases, {observational_period} day period',
        rangemode='tozero',
        range=[0, yaxis_max])

    return fig


@app.callback(Output('csa-map', 'figure'), Input('map-date', 'value'),
              Input('map-discreet-level', 'value'))
def update_csa_map(days_back, key):
    compare_date = last_day - pd.Timedelta(days_back + 7, 'days')
    df_geo = df_dph_14day[df_dph_14day[EP_DATE] == compare_date]

    kargs = {
        'color': 'case_14day_rate',
        'color_continuous_scale': px.colors.sequential.OrRd,
        'range_color': [0, 300]
    }
    title = '7 day case rate, 14 day period'

    # Use CDC Level of Community Transmission
    if key:
        kargs = {
            'color': 'Level of Community Transmission',
            'category_orders': CDC_COMMUNITY_TRANSMISSION_ORDER,
            'color_discrete_map': CDC_COMMUNITY_TRANSMISSION_COLORS
        }
        title = 'Level of Community Transmission'

    csa_map = px.choropleth_mapbox(
        df_geo,
        geojson,
        'properties.LABEL',
        CSA,
        opacity=0.9,
        zoom=8.75,
        center={
            'lat': 34.1,
            'lon': -118.25
        },
        mapbox_style='streets',
        title=f'COVID-19 in Los Angeles County {title}',
        width=1000,
        height=700,
        **kargs)

    return csa_map


if __name__ == '__main__':
    app.run_server(debug=True)
