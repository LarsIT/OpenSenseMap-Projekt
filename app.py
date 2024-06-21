from dash import Dash, html, dash_table, dcc
import pandas as pd
from dash.dependencies import Input, Output
import plotly.express as px
from datetime import datetime, timedelta
import os
import requests
from plotly import graph_objects as go
from pathlib import Path



#TODO Vereinheitlichen der Plot Layouts!
#TODO Modell bauen, an großer Historie trainieren und anhand der letzten Woche an Daten die nächsten Tage vorhersagen
#TODO Ausführungsreihenfolge einbauen, damit dataframe skripte ausgeführt werden

# date now
date_now = datetime.now().date()
date_now = "2024-06-20" #TODO REMOVE THIS WHEN DONE PROTOTYPING

# File paths
current_directory = Path(__file__).resolve().parent

file_path = current_directory / 'daten' / 'past_week' / f'past_week_{date_now}.csv'
past_week_data = pd.read_csv(file_path)

file_path = current_directory / 'daten' / 'box_info' / 'box_info.csv'
box_data = pd.read_csv(file_path)

# Plotly configuration
layout = {
    "xaxis_title": "Datum",
    "yaxis_title": "Temperatur in Grad Celsius",
    "title": "Temperaturen der vergangenen Woche in Köln",
    "width": 1000,
    "height": 250
}


# Application
app = Dash(__name__)

app.layout = [
    html.Div([
        html.H1("Max Elden Ring Death-Counter: 19")
    ]),
    
    # Location
    html.Div([
        html.H1("Standort der OpenSenseBox"),
        html.Div([
            html.Iframe(
                id='html_file',
                style={'width': '33%', 'height':'800px',"border":"5px solid #ccc"},
                srcDoc=open(current_directory / "graphs_static" / "location" / "map.html", 'r').read()
            )
        ])
    ]),

    # History
    html.Div([
        html.Div(children='Historie'),
        dcc.Graph(figure=px.line(past_week_data, x="createdAt", y="value").update_layout(layout))
    ]),

    # Live
    html.Div([
        html.Div(children="Live Daten"),
            # Graph component
            dcc.Graph(id='live-graph'),

            # Triggers periodically
            dcc.Interval(   
            id='interval-component',
            interval=10_000,
            n_intervals=0)
    ]),
    

    # Forecast
    html.Div([
        html.Div(children="Vorhersage"),
    ])
]

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
    trace = go.Scatter(x=live_data['timestamp'], y=live_data['value'], mode='lines+markers')
    layout = go.Layout(title='Live Sensordaten aus Köln', xaxis=dict(title='Zeitstempel'), yaxis=dict(title='Temperatur in Grad Celsius'), width=1000, height=250)
    fig = go.Figure(data=[trace], layout=layout)
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)