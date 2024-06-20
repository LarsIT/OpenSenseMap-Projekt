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
#TODO Prüfen der Pfade, Windows is blöd
#TODO Ausführungsreihenfolge einbauen, damit dataframe skripte ausgeführt werden

# date now
date_now = datetime.now().date()
print(date_now)
# Get the directory of the current script
current_directory = Path(__file__).resolve().parent
print(f"Current directory: {current_directory}")

csv_path = current_directory / 'daten' / 'past_week' / f'past_week_2024-06-20.csv'
print(csv_path)
past_week_data = pd.read_csv(csv_path)
print("YES")