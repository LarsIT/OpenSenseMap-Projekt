import pandas as pd
from pathlib import Path
import joblib

def make_features(df):
    df = df.copy()
    # Create lag features, up to 5 days back
    for i in range(1,3):
        df[f"t-{i*24}"] = df["value"].shift(+i*24)
    
    # Rolling mean feature
    df["prev_24h"] = df[["value"]].rolling(24).mean().shift()
    
    return df

# Data and model
current_directory = Path(__file__).resolve().parent

model = joblib.load(current_directory.parent / "model" / "model.joblib")


past_week_temperature = pd.read_csv("daten/past_week/past_week_2024-06-21.csv")
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

# save df!