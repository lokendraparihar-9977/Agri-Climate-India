import pandas as pd
import streamlit as st
import os

# Dynamic path — works both locally and on Streamlit Cloud
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR  = os.path.join(BASE_DIR, 'Data')

@st.cache_data
def load_all_data():
    crop_df  = pd.read_csv(os.path.join(DATA_DIR, 'crop_clean.csv'))
    rain_df  = pd.read_csv(os.path.join(DATA_DIR, 'rain_clean.csv'))
    temp_df  = pd.read_csv(os.path.join(DATA_DIR, 'temp_clean.csv'))
    water_df = pd.read_csv(os.path.join(DATA_DIR, 'water_clean.csv'))
    return crop_df, rain_df, temp_df, water_df

@st.cache_data
def get_state_yield_summary(crop_df):
    return (
        crop_df.groupby('State')['Yield']
        .mean().sort_values(ascending=False)
        .reset_index()
        .rename(columns={'Yield': 'avg_yield'})
    )

@st.cache_data
def get_yearly_trend(crop_df):
    return crop_df.groupby('Crop_Year')['Yield'].mean().reset_index()

@st.cache_data
def get_crop_summary(crop_df):
    return (
        crop_df.groupby('Crop')['Area']
        .sum().sort_values(ascending=False)
        .reset_index()
    )