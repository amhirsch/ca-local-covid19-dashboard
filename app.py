from typing import Dict, Iterable, List, Tuple
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from pandas._libs.missing import NA
import plotly.express as px
import pandas as pd

LACDPH = 'lacdph'
LATIMES = 'latimes'

DATE = 'date'
COUNTY = 'county'
NAME = 'name'
ID = 'id'

EP_DATE = 'ep_date'
CSA = 'csa'
DPH_CASE_COLS = 'cases_{}day', 'case_{}day_rate', 'adj_case_{}day_rate'

LOS_ANGELES = 'Los Angeles'
YAXIS_RANGE = 300, 600, 1000, 1600

LABEL = 'label'
VALUE = 'value'

# First Known COVID-19 Case in California
ABSOLUTE_FIRST_DAY = pd.to_datetime('2020-01-26')

df_times = pd.read_pickle('data/latimes-places-ts.pickle')
ABSOLUTE_LAST_DAY = df_times[DATE].max()

df_dph_7day, df_dph_14day = [
    pd.read_pickle(f'data/lacdph-{x}day.pickle') for x in (7, 14)
]

LACDPH_CSA_LIST = list(df_dph_7day['csa'].unique())
LACDPH_CSA_LIST.sort()

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__,
                title='CA Local COVID-19 Dashboard',
                external_stylesheets=external_stylesheets)
server = app.server

counties = list(df_times[COUNTY].unique())
counties.sort()


def latimes_county_places(county: str) -> Tuple[str, ...]:
    places = list(df_times.loc[df_times[COUNTY] == county, NAME].unique())
    places.sort()
    return tuple(places)


def create_dash_options(iterable: Iterable) -> List[Dict[str, str]]:
    return [{LABEL: x, VALUE: x} for x in iterable]


def place_to_id(county, name):
    id_ = df_times.loc[(df_times[COUNTY] == county) & (df_times[NAME] == name),
                       ID].unique()
    if len(id_) == 1:
        return id_[0]
    elif len(id_) == 0:
        raise ValueError(f'{name} not found in {county} County')
    else:
        raise ValueError(
            f"Multiple ID's for {county}, {name}: {', '.join(map(str, id_))}")


def id_to_place(county, id_):
    place = list(df_times.loc[(df_times[COUNTY] == county) &
                              (df_times[ID] == id_), NAME].unique())
    if len(place) == 1:
        return place[0]
    raise ValueError(
        f'The ID {id_} in {county} County could not be converted to place.')


with open('footnotes.md') as f:
    FOOTNOTES = f.read()

CONTROLS = html.Div([
    html.Label('County', htmlFor='selected-county'),
    html.Div([
        dcc.Dropdown(id='selected-county',
                     options=[{
                         LABEL: i,
                         VALUE: i
                     } for i in counties],
                     value='Los Angeles'),
        html.Label(
            'Place', id='selected-place-label', htmlFor='selected-place-value'),
        dcc.Dropdown(id='selected-place-value', value='Claremont')
    ]),
    html.Div([
        html.Div([
            html.Label('Date Range', htmlFor='time-selector'),
            dcc.RadioItems(id='time-selector',
                           options=[{
                               LABEL: 'All time',
                               VALUE: 0
                           }, {
                               LABEL: '4 months',
                               VALUE: 120
                           }],
                           value=120)
        ]),
        html.Div([
            html.Label('Sample Period', htmlFor='observational-period'),
            dcc.RadioItems(id='observational-period',
                           options=[{
                               LABEL: '7 day',
                               VALUE: 7
                           }, {
                               LABEL: '14 day',
                               VALUE: 14
                           }],
                           value=7)
        ]),
        html.Div([
            html.Label('Data Source', htmlFor='selected-data-source'),
            dcc.RadioItems(id='selected-data-source', value=LATIMES)
        ])
    ],
             style={
                 'display': 'flex',
                 'columnGap': '2em'
             })
],
                    style={
                        'width': '32em',
                        'paddingLeft': '1em'
                    })

app.layout = html.Div(
    [
        html.Div([
            html.H1('California Local COVID-19 Dashboard'),
            html.Div([
                CONTROLS,
                dcc.Graph(id='csa-ts',
                          style={
                              'width': '50em',
                              'height': '35em',
                              'paddingLeft': '1em'
                          })
            ],
                     style={
                         'display': 'flex',
                         'flexWrap': 'wrap',
                         'justifyContent': 'left'
                     }),
            dcc.Markdown(FOOTNOTES, style={'maxWidth': '60em'})
        ])
    ],
    style={
        'paddingLeft': '1em',
        'display': 'flex',
        'justifyContent': 'center',
        'alignItems': 'center'
    })


@app.callback(Output('selected-data-source', 'options'),
              Output('selected-data-source', 'value'),
              Input('selected-county', 'value'))
def county_data_options(county):
    data_src_options = [{LABEL: 'Los Angeles Times', VALUE: LATIMES}]
    if county == LOS_ANGELES:
        data_src_options.append({LABEL: 'LACDPH', VALUE: LACDPH})
    return data_src_options, LATIMES


@app.callback(Output('selected-place-label', 'children'),
              Input('selected-data-source', 'value'))
def place_label(data_src):
    return 'Place' if data_src == LATIMES else 'Countywide Statistical Area'


@app.callback(Output('selected-place-value', 'options'),
              Output('selected-place-value', 'value'),
              Input('selected-county', 'value'),
              Input('selected-data-source', 'value'),
              Input('selected-place-value', 'value'))
def place_value(county, data_src, orig_place):
    if data_src == LACDPH:
        place_options = LACDPH_CSA_LIST
        if orig_place in latimes_county_places(LOS_ANGELES):
            orig_place = place_to_id(LOS_ANGELES, orig_place)
    else:
        place_options = latimes_county_places(county)
        if county == LOS_ANGELES and orig_place in LACDPH_CSA_LIST:
            orig_place = id_to_place(LOS_ANGELES, orig_place)
    if orig_place in place_options:
        place_selection = orig_place
    else:
        place_selection = place_options[0]
    return create_dash_options(place_options), place_selection


@app.callback(Output('csa-ts', 'figure'), Input('selected-county', 'value'),
              Input('selected-place-value', 'value'),
              Input('time-selector', 'value'),
              Input('observational-period', 'value'),
              Input('selected-data-source', 'value'))
def update_general_graph(county, place, date_range, obs_period, data_source):
    if data_source == LACDPH:
        return update_lacdph_graph(place, date_range, obs_period)
    return update_latimes_graph(county, place, date_range, obs_period)


def update_latimes_graph(county, place, date_range, obs_period):

    NEW_CASES_7DAY, NEW_CASES_14DAY = [f'new_cases_{x}day' for x in (7, 14)]
    CASE_RATE_7DAY, CASE_RATE_14DAY = [f'case_rate_{x}day' for x in (7, 14)]

    county_places = latimes_county_places(county)
    id_ = place_to_id(county,
                      place) if place in county_places else county_places[0]

    df_place = df_times[df_times[ID] == id_]
    dep_var, dep_var_raw = (CASE_RATE_7DAY,
                            NEW_CASES_7DAY) if obs_period == 7 else (
                                CASE_RATE_14DAY, NEW_CASES_14DAY)

    date_range_min = ABSOLUTE_FIRST_DAY
    if date_range > 0:
        date_range_min = ABSOLUTE_LAST_DAY - pd.Timedelta(date_range, 'days')
        df_place = df_place[df_place[DATE] >= date_range_min]

    local_max = df_place[dep_var].max()
    if local_max <= max(YAXIS_RANGE):
        yaxis_max = [x for x in YAXIS_RANGE if x >= local_max][0]
    else:
        yaxis_max = local_max * 1.05

    fig = px.line(df_place,
                  DATE,
                  dep_var,
                  hover_data=[dep_var_raw],
                  title=f'{place} COVID-19 Case Rate per 100,000 people')
    fig.update_xaxes(title_text='Reported date',
                     range=[date_range_min, ABSOLUTE_LAST_DAY])
    fig.update_yaxes(
        title_text=f'7 day cumulative cases, {obs_period} day period',
        rangemode='tozero',
        range=[0, yaxis_max])

    return fig


def update_lacdph_graph(csa, date_range, obs_period):
    if obs_period == 7:
        df = df_dph_7day
    elif obs_period == 14:
        df = df_dph_14day
    else:
        raise ValueError('Invalid observational period. Options are 7 or 14.')

    df_csa = df[df['csa'] == csa]
    dep_var = f'case_{obs_period}day_rate'

    date_range_min = ABSOLUTE_FIRST_DAY
    if date_range > 0:
        date_range_min = ABSOLUTE_LAST_DAY - pd.Timedelta(date_range, 'days')
        df_csa = df_csa[df_csa['ep_date'] >= date_range_min]

    local_max = df_csa[dep_var].max()
    if local_max <= max(YAXIS_RANGE):
        yaxis_max = [x for x in YAXIS_RANGE if x >= local_max][0]
    else:
        yaxis_max = local_max * 1.05

    fig = px.line(df_csa,
                  'ep_date',
                  dep_var,
                  hover_data=[f'cases_{obs_period}day', 'case_rate_unstable'],
                  title=f'{csa} COVID-19 Case Rate per 100,000 people')
    fig.update_xaxes(title_text='Episode date',
                     range=[date_range_min, ABSOLUTE_LAST_DAY])
    fig.update_yaxes(
        title_text=f'7 day cumulative cases, {obs_period} day period',
        rangemode='tozero',
        range=[0, yaxis_max])

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
