import pandas as pd
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from PIL import Image
import requests
from io import BytesIO

"""Creates a plotly dashboard granting the user the ability to interact with indicators of sunspot activity
"""


response = requests.get("https://soho.nascom.nasa.gov/data/realtime/hmi_igr/1024/latest.jpg")
img = Image.open(BytesIO(response.content))

# create the layout
app = Dash(__name__)

# define the layout
app.layout = html.Div([

    html.H1('SunDash: Monitoring and Analyzing Solar Activity'),

    html.Div([

    html.Div(children=[
        html.Div([

        html.Div(children = [
        html.Label('Select Observation Type',
                   style = {'margin': 20,
                              'textAlign': 'center'}),
        dcc.Dropdown(['days', 'months'],
                     value = 'days',
                     id = "SelObsType",
                     style = {'margin':15,
                              'textAlign': 'center'},
                     clearable = False
                     ),
        html.Br()
        ]),

        html.Div(children = [

        html.Label('Begin Date:',
                   style={'margin':20,
                          'textAlign': 'center'}),
        dcc.Dropdown(list(range(1818, 2024)),
                     value = 1818,
                     id="StartDateDrop",
                     clearable = False,
                     style={'margin':15,
                            'textAlign': 'center'}),

        html.Br()
            ]),

        html.Div(children = [

        html.Label('End Date:',
                   style={"margin-left": "25px"}),
        dcc.Dropdown(list(range(1818, 2024)),
                     value = 2023,
                     id = "EndDateDrop",
                     clearable = False,
                     style={'margin': 15,
                            'textAlign': 'center'}),

        html.Br()
            ])], style={'display': 'flex', 'flex-direction': 'row'}),

        html.Div([

        html.Div(children = [
        html.Label('Smoothening Time Domain:',
                   style={'margin': 25,
                          'textAlign': 'center'}
                   ),
        dcc.Dropdown(["days", "months"],
                     value = "days",
                     id = "SmootheningTypeDrop",
                     clearable = False,
                     style={'margin': 15,
                            'textAlign': 'center'}
                     ),

        html.Br()]),

        html.Div([

        html.Label('Smoothening Period:',
                   style={'margin': 25,
                          'textAlign': 'center'}
                   ),
        dcc.Dropdown(list(range(30)),
                         value = 5,
                         id = "SmootheningPeriodDrop",
                         clearable = False,
                     style={'margin': 20,
                            'textAlign': 'center'}
                     ),

        html.Br()
        ])], style={'display': 'flex', 'flex-direction': 'row'}),
        dcc.Graph(id = "graph")

    ], style={'padding': 10, 'flex': 1}),
    html.Div([

    html.Div(children=[

        html.Label('Sun Cycle Period',
                   id = "period_label"),
        html.Br(),
        html.Label('Select Domain for Sun Cycle Period',
                   id="cycle_domain_label"),
        dcc.Dropdown(["years"],
                     value = "years",
                     id = "CyclePeriodDomainDrop",
                     clearable = False),
        html.Label('Select Sun Cycle Time Period',
                   id = "sun_cycle_slider_label"),
        dcc.Slider(1, 30, 1,
                     value=11,
                     id="slider"),

        html.Br(),
        dcc.Graph(id="graph2")

    ])], style={'padding': 10, 'flex': 1}),

    html.Div(children = [
        html.Label("Current Real Image of Sun"),
        html.Br(),
        html.Img(src=img,
                 id = "image",
                 style = {"width": "60%", "height": "50%"}),
        html.Br(),
        html.Button('Refresh', id = 'refresh_button', n_clicks = 0)
    ], style={'padding': 10, 'flex': 1,
              'textAlign': 'center'
              })
], style={'display': 'flex', 'flex-direction': 'row',
          })],
    style ={'textAlign' : 'center'}
)

def read_sunspot_data(precision):

    """ read sunspot data in DataFrame

    :param
    precision (str): unit of time, frequency of measurement
    :return:
    df (pd.DataFrame): dataframe of sunspot data

    """

    if precision == "days":
        df = pd.read_fwf("SN_d_tot_V2.0.txt", header = None)
        df.columns = ["year", "month", "day", "frac_year", "Sn", "a", "b"]
        df = df.drop(["a", "b"], axis = 1)
    if precision == "months" or precision == "years":
        df = pd.read_fwf('SN_m_tot_V2.0.txt', header = None)
        df.columns = ["year", "month", "frac_year", "Sn", "a", "b"]
        df = df.drop(["a","b"], axis = 1)

    min_year = df["year"].min()
    max_year = df["year"].max()
    year_range = list(range(min_year, max_year + 1))

    return df

def smooth_data(df, time_unit, period):

    """ create dataframe of smoothed data

    :param
    df (pd.DataFrame): sunspot datafram
    time_unit (int): unit of time for smoothing
    period (int): quantity of time to smooth over

    :return:
    average_df (pd.DataFrame): dataframe with moving average sunspot data

    """

    if "day" in df.columns:
        domain = "days"
    else:
        domain = "months"

    if domain == "days":

        if time_unit == "days":

            df = df[["frac_year", "Sn"]]

            average_df = df.rolling(window = int(period) * 2, min_periods = int(period)).mean()

        if time_unit == "months":

            df = df[df["day"] == 1]
            df = df[["frac_year", "Sn"]]
            average_df = df.rolling(window=int(period) * 2, min_periods=int(period)).mean()

    if domain == "months":

        if time_unit == "months":
            df = df[["frac_year", "Sn"]]
            average_df = df.rolling(window=int(period) * 2, min_periods=int(period)).mean()

    return average_df


@app.callback(
    Output("graph", "figure"),
    Output("StartDateDrop", "options"),
    Output("EndDateDrop", "options"),
    Output("StartDateDrop", "value"),
    Output("EndDateDrop", "value"),
    Input("SelObsType", "value"),
    Input("StartDateDrop", "value"),
    Input("EndDateDrop", "value"),
    Input("SmootheningTypeDrop", "value"),
    Input("SmootheningPeriodDrop", "value")
)
def display_sunspot_figure(precision, lower_bound, upper_bound, time_unit, period):

    """ displays sunspot cycle plot

    :param
    precision (str): unit of time of data points (days or months)
    lower_bound (int): earliest year to include in plot
    upper_bound (int): latest year to include in plot
    time_unit (str): smoothing unit of time
    period (str): period over which smoothing should occur

    :return:
    fig (plotly.graph_objects): plot of sunspot data
    list_years (list): list of available years
    min_year (int): earliest year
    max_year (int): most recent year

    """

    df = read_sunspot_data(precision)
    min_year = df["year"].min()
    max_year = df["year"].max()
    list_years = list(range(min_year, max_year + 1))
    df = df[(df["frac_year"].astype(float) >= int(lower_bound)) & (df["frac_year"].astype(float) <= int(upper_bound))]
    smoothed_df = smooth_data(df, time_unit, period)
    fig = go.Figure(data=go.Scatter(x=df["frac_year"], y=df["Sn"], name = 'Raw Data'))
    trace2 = go.Scatter(
        x=smoothed_df["frac_year"],
        y=smoothed_df["Sn"],
        name='Smoothed Data')
    fig.add_trace(trace2)
    fig.update_layout(
        title=f"Average Sunspot Number: Mean by {precision}, smoothed by {str(period)} {time_unit}",
        xaxis_title="Year",
        yaxis_title="Sunspot Number")

    return fig, list_years, list_years, min_year, max_year

@app.callback(
    Output("graph2", "figure"),
    Input("CyclePeriodDomainDrop", "value"),
    Input("slider", "value")
)
def display_cycle_figure(precision, cycle_period):

    """ displays sunspot cycle plot. Plot overlays sunspot values at different parts of the set cycle

    :params
    precision (str): unit of time of data points
    cycle_period (int): number of months or years in a sun cycle

    :return:
    fig (plotly.graph_objects): plot of sunspot cycle

    """

    df = read_sunspot_data(precision)

    if precision == "years":
        df["cycle_month"] = df["frac_year"].astype(float) % int(cycle_period)
        fig = go.Figure(data = go.Scatter(x = df["cycle_month"],
                                          y = df["Sn"],
                                            mode='markers'))

    fig.update_layout(
        title=f"Sunspot Cycle: {str(cycle_period)} {precision}",
        title_x=0.5,
        xaxis_title=f"{precision}".capitalize(),
        yaxis_title="# of Sunspots"
    )
    return fig

@app.callback(
    Output("SmootheningTypeDrop", "options"),
    Output("SmootheningTypeDrop", "value"),
    Input("SelObsType", "value")
)
def get_smoothening_types(obs_type):

    """ either smooths over days or months
    :param
    obs_type (str): unit of time to smooth over

    :return:
    smooth_domain_list (list): list of possible smoothing domains
    default_value (str): value to start dropdown on

    """

    if obs_type == "days":
        smooth_domain_list = ["days", "months"]

    if obs_type == "months":
        smooth_domain_list = ["months"]

    default_value = smooth_domain_list[0]
    return smooth_domain_list, default_value

@app.callback(
    Output('image', 'src'),
    Output('image', 'n_clicks'),
    Input('refresh_button', 'n_clicks')

)
def refresh_image(n_clicks):
    if n_clicks is None:
        pass
    else:
        response = requests.get("https://soho.nascom.nasa.gov/data/realtime/hmi_igr/1024/latest.jpg")
        img = Image.open(BytesIO(response.content))
        reset_n_clicks = None

        return img, reset_n_clicks

# run the server
app.run_server(debug=True)

