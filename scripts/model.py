from sklearn.metrics import mean_squared_error
from sklearn.linear_model import LinearRegression
import pandas as pd
from pathlib import Path
import joblib
import numpy as np

current_directory = Path(__file__).resolve().parent

past_year_data = pd.read_csv(current_directory.parent / "daten" / "opensensemap_org-download-Temperatur-lat-lon-boxName-boxId-unit-value-createdAt-20240608_122410.csv")

def make_features(df):
    df = df.copy()
    # Create lag features, up to 5 days back
    for i in range(1,3):
        df[f"t-{i*24}"] = df["value"].shift(+i*24)
    
    # Rolling mean feature
    df["prev_24h"] = df[["value"]].rolling(24).mean().shift()
    
    return df

def trainLM(df, mkplot=True):
    df = df.copy().set_index("createdAt")
    df.dropna(inplace=True)
    
    X = df.loc[:, df.columns != 'value'] # Use all columns except 'value' as inputs
    
    y = df.value
    model = LinearRegression().fit(X, y)
    eval_df = df[['value']].copy()
    eval_df['pred'] = model.predict(X)
    # print('Koeffizienten: ', model.coef_,' Intercept: ',model.intercept_)
    # print("Mean Squared Error: ",mean_squared_error(eval_df.value, eval_df.pred))
    # if mkplot:
    #     eval_df.iloc[1:100].plot(figsize=(15,5))
    #     eval_df.iloc[1:1000].plot(figsize=(15,5))
    #     eval_df.plot(figsize=(15,5))
        
    return model

# Prepcosessing
temperature_agg = past_year_data.copy()
temperature_agg["createdAt"] = pd.to_datetime(temperature_agg["createdAt"])

# Resample
temperature_agg.set_index("createdAt", inplace=True)
temperature_agg = temperature_agg["value"].resample('h').mean() 
temperature_agg = temperature_agg.to_frame().reset_index()

# Outlier removal with temperature difference test
temperature_agg['value_diff'] = temperature_agg['value'] - temperature_agg['value'].shift(1)
temperature_agg.loc[(temperature_agg['value_diff'].abs() > 10) | (temperature_agg['value'] == -143.42), 'value'] = np.nan # -143.42 is also considered NaN
temperature_agg.drop(columns=['value_diff'], inplace=True)

# Interpolation of NaN
temperature_agg['value'] = temperature_agg['value'].interpolate(method='linear')

# Restriction of data to specific timeframe
temperature_agg = temperature_agg[temperature_agg["createdAt"].dt.tz_localize(None) <= pd.Timestamp('2024-03-1')] # Rght after this date is a big data hole


df = temperature_agg.copy()
df = make_features(df)

model = trainLM(df)

joblib.dump(model, current_directory.parent / "model" / "model.joblib")
