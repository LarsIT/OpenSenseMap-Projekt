from dash import Dash, html, dash_table, dcc
import pandas as pd
from dash.dependencies import Input, Output
import plotly.express as px
from datetime import datetime, timedelta
import requests
from plotly import graph_objects as go
from pathlib import Path
import joblib
import numpy as np
import subprocess
import plotly.io as pio

pio.templates.default = "simple_white"
line_color = '#262626'


def make_features(df):
    df = df.copy()
    # Create lag features, up to 5 days back
    for i in range(1,3):
        df[f"t-{i*24}"] = df["value"].shift(+i*24)
    
    # Rolling mean feature
    df["prev_24h"] = df[["value"]].rolling(24).mean().shift()
    
    return df

# date now
date_now = datetime.now().date()

# Paths
current_directory = Path(__file__).resolve().parent
venv_path = current_directory / ".venv" / "scripts" / "python.exe"
# Scripts
subprocess.run([venv_path, current_directory / "scripts" / "box_data.py"])
subprocess.run([venv_path, current_directory / "scripts" / "history.py"])
subprocess.run([venv_path, current_directory / "scripts" / "model.py"])

# Data and model
past_week_data = pd.read_csv(current_directory / 'daten' / 'past_week' / f'past_week_{date_now}.csv')
box_data = pd.read_csv(current_directory / 'daten' / 'box_info' / 'box_info.csv')
model = joblib.load(current_directory / "model" / "model.joblib")

# Plotly configuration
# layout = {
#     "width": "90%",
#     "height": 250
# }

# Forecast
past_week_temperature = past_week_data
past_week_temperature = make_features(past_week_temperature).dropna()
past_week_temperature["createdAt"] = pd.to_datetime(past_week_temperature["createdAt"])
past_week_temperature.set_index("createdAt", inplace=True)
backup_past_week = past_week_temperature.copy()
target = past_week_temperature.pop("value")
features = ["t-24", "t-48", "prev_24h"]

# Initialize DataFrame for forecasted values
forecast_horizon = 72  # Forecast 72 hours into the future
forecast_start_date = past_week_temperature.index[-1] + pd.Timedelta(hours=1)  # Start forecasting from the next hour
forecast_df = pd.DataFrame(index=pd.date_range(start=forecast_start_date, periods=forecast_horizon, freq='h'), columns=["t-24", "t-48", "prev_24h"])
forecast_df = pd.concat([backup_past_week, forecast_df])
forecast_df.rename({"value":"predict"}, axis=1, inplace=True)

# Iteratively building the future 72h forecast
# Since we use features that would require to know for example for predicting t+25 the value of our prediction of t+1 (t+25-24)
# We have to use this for-loop to build it sequentially
current_index = len(forecast_df) - forecast_horizon

for timestep in range(1, forecast_horizon+1):
    
    # updating features in temporary columns   
    for i in range(1,3):
        forecast_df[f"t-{i*24}_2"] = forecast_df["predict"].shift(+i*24)

    forecast_df["prev_24h_2"] = forecast_df[["predict"]].rolling(24).mean().shift()

    # moving updated feature values into actual feature columns
    for i in features:
        forecast_df[i] = np.where(forecast_df[i].isna(), forecast_df[f"{i}_2"], forecast_df[i])
        
    # prediction
    forecast_df.iloc[current_index, 0] = model.predict(forecast_df.iloc[current_index:current_index+1][features]) # First Value to predict
    
    current_index += 1

forecast_df.reset_index(inplace=True)
##
axis_labels={
    "yaxis_title" : "Temperatur in °C",
    "xaxis_title" : "Datum"
}

# Application
app = Dash(__name__)

app.layout = html.Div(
    children=[
        html.Div(
            className="banner",
            children=[
                html.H1("Temperaturanzeige Köln"),
                html.Img(src="/assets/img/Wappen_Koeln.png", className="banner-img")
            ]
        ),
        html.Div(
            className="grid-container",
            children=[
                html.Div(
                    className="grid-item",
                    children=[
                        html.Iframe(id='html_file', style={'width': '100%', 'height': '100%', "border": "5px solid #ccc"}, srcDoc=open(current_directory / "graphs_static" / "location" / "map.html", 'r').read())
                    ]
                ),
                html.Div(
                    className="grid-item graph-container",
                    children=[
                        html.Div(
                            children=[
                                dcc.Graph(
                                    className="graph-item",
                                    figure=px.line(past_week_data, x="createdAt", y="value", color_discrete_sequence=[line_color], title="Temperatur der letzten Woche").update_layout(axis_labels))
                            ]
                        ),
                        html.Div(
                            children=[
                                dcc.Graph(
                                    className="graph-item",
                                    figure=px.line(forecast_df[-72:], x="index", y="predict", color_discrete_sequence=[line_color], title="Temperaturvorhersage für die nächsten 3 Tage").update_layout(axis_labels))
                            ]
                        ),
                        html.Div(
                            children=[
                                dcc.Graph(
                                    className="graph-item",
                                    id='live-graph'),
                                dcc.Interval(id='interval-component', interval=10_000, n_intervals=0)
                            ]
                        )
                    ]
                )
            ]
        )
    ]
)

# Initialize empty dataframe
live_data = pd.DataFrame(columns=['timestamp', 'value'])

# Define callback to update graph
@app.callback(
    Output('live-graph', 'figure'),
    [Input('interval-component', 'n_intervals')]
)

def update_graph(n):  # increment from intervals

    # Request API
    box_id = box_data["ID"][0]
    url = f"https://api.opensensemap.org/boxes/{box_id}?format=json"
    data = requests.get(url).json()
    value = data['sensors'][2]['lastMeasurement']['value']
    timestamp = datetime.now()

    global live_data
    live_data = pd.concat([live_data, pd.DataFrame([{'timestamp': timestamp, 'value': float(value)}])], ignore_index=True)

    # Plot data
    trace = go.Scatter(x=live_data['timestamp'], y=live_data['value'], mode='lines+markers', line_color=line_color)
    layout = go.Layout(title='Live Sensordaten aus Köln', xaxis=dict(title='Zeitstempel'), yaxis=dict(title='Temperatur in °C'))
    fig = go.Figure(data=[trace], layout=layout)
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)