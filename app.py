import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from pandas._libs.missing import NA
import plotly.express as px
import pandas as pd

DATE = 'date'
COUNTY = 'county'
NAME = 'name'
ID = 'id'

EP_DATE = 'ep_date'
CSA = 'csa'
DPH_CASE_COLS = 'cases_{}day', 'case_{}day_rate', 'adj_case_{}day_rate'

YAXIS_RANGE = 400, 1000, 1600

# First Known COVID-19 Case in California
ABSOLUTE_FIRST_DAY = pd.to_datetime('2020-01-26')

df_times = pd.read_pickle('data/latimes-places-ts.pickle')
ABSOLUTE_LAST_DAY = df_times[DATE].max()

df_dph_7day, df_dph_14day = [
    pd.read_pickle(f'data/lacdph-{x}day.pickle') for x in (7, 14)
]

lacdph_csa_list = list(df_dph_7day['csa'].unique())
lacdph_csa_list.sort()

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

counties = list(df_times[COUNTY].unique())
counties.sort()


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


FOOTNOTES = '''
Sources:

* Los Angeles Times - [California Coronavirus Data](https://github.com/datadesk/california-coronavirus-data)
* Los Angeles County Department of Public Health - [COVID-19 Data Dashboard](http://dashboard.publichealth.lacounty.gov/covid19_surveillance_dashboard/)

GitHub: [amhirsch/ca-local-covid19-dashboard](https://github.com/amhirsch/ca-local-covid19-dashboard)
'''

LABEL = 'label'
VALUE = 'value'
app.layout = html.Div([
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
        dcc.Dropdown(id='selected-place-value', value='Burbank')
    ],
             style={'maxWidth': '35em'}),
    html.Div(
        [
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
                html.Label('Observational Period',
                           htmlFor='observational-period'),
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
                dcc.RadioItems(id='selected-data-source', value='latimes')
            ])
        ],
        style={
            'display': 'flex',
            'flexDirection': 'row',
            'columnGap': '1.5em',
            'paddingLeft': '1.5em'
        }),
    dcc.Graph(id='csa-ts', style={'maxWidth': '50em'}),
    dcc.Markdown(FOOTNOTES)
])


@app.callback(Output('selected-place-label', 'children'),
              Output('selected-place-value', 'options'),
              Output('selected-place-value', 'value'),
              Input('selected-county', 'value'),
              Input('selected-place-value', 'value'),
              Input('selected-data-source', 'value'))
def county_places(county, place_or_id, data_source):
    if data_source == 'latimes':
        places = list(df_times.loc[df_times[COUNTY] == county, NAME].unique())
        places.sort()
        if place_or_id in places:
            selected = place_or_id
        elif place_or_id in lacdph_csa_list:
            selected = id_to_place('Los Angeles', place_or_id)
        else:
            selected = places[0]
    else:
        places = lacdph_csa_list
        if place_or_id in places:
            selected = place_or_id
        elif place_or_id not in places:
            selected = place_to_id('Los Angeles', place_or_id)
            if selected not in places:
                selected = places[0]
        else:
            selected = places[0]

    return ('Place'
            if data_source == 'latimes' else 'Countywide Statistical Area', [{
                LABEL: x,
                VALUE: x
            } for x in places], selected)


@app.callback(Output('selected-data-source', 'options'),
              Input('selected-county', 'value'))
def data_source_options(county):
    options = [{LABEL: 'Los Angeles Times', VALUE: 'latimes'}]
    if county == 'Los Angeles':
        options.append({LABEL: 'LACDPH', VALUE: 'lacdph'})
    return options


@app.callback(Output('csa-ts', 'figure'), Input('selected-county', 'value'),
              Input('selected-place-value', 'value'),
              Input('time-selector', 'value'),
              Input('observational-period', 'value'),
              Input('selected-data-source', 'value'))
def update_general_graph(county, place, date_range, obs_period, data_source):
    if data_source == 'lacdph':
        return update_lacdph_graph(place, date_range, obs_period)
    return update_latimes_graph(county, place, date_range, obs_period)


def update_latimes_graph(county, place, date_range, obs_period):

    NEW_CASES_7DAY, NEW_CASES_14DAY = [f'new_cases_{x}day' for x in (7, 14)]
    CASE_RATE_7DAY, CASE_RATE_14DAY = [f'case_rate_{x}day' for x in (7, 14)]

    id_ = place_to_id(county, place)

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
    app.run_server(debug=False)
