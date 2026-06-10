# pages/3_Predictor.py
import streamlit as st
import pandas as pd
import numpy as np
import pickle, json, os, sys
import plotly.express as px
import plotly.graph_objects as go

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import load_all_data

st.set_page_config(
    page_title="Yield Predictor | AgriClimate India",
    page_icon="🔮",
    layout="wide"
)

# ── Load model and config ──
DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'Data'
)

@st.cache_resource
def load_model():
    with open(os.path.join(DATA_PATH, 'xgboost_model.pkl'), 'rb') as f:
        model = pickle.load(f)
    with open(os.path.join(DATA_PATH, 'model_config.json')) as f:
        config = json.load(f)
    with open(os.path.join(DATA_PATH, 'label_encoders.pkl'), 'rb') as f:
        encoders = pickle.load(f)
    with open(os.path.join(DATA_PATH, 'ml_features.json')) as f:
        features = json.load(f)
    return model, config, encoders, features

model, config, encoders, feat_config = load_model()
le_crop  = encoders['crop']
le_state = encoders['state']
ML_FEATURES = feat_config['features']

# ── Header ──
st.markdown("## 🔮 Crop Yield Predictor")
st.markdown("Enter climate and location details to predict expected crop yield.")
st.divider()

# ── Model performance banner ──
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("Model",      "XGBoost v2")
col_m2.metric("R² Score",   f"{config['r2_score']:.4f}")
col_m3.metric("RMSE",       f"{config['rmse']:.4f} kg/ha")
col_m4.metric("CV R²",      f"{config['cv_mean_r2']:.4f}")
st.divider()

# ════════════════════════════════
# INPUT SECTION
# ════════════════════════════════
st.subheader("📥 Input Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Location & Crop**")
    selected_state = st.selectbox(
        "State",
        options=sorted(le_state.classes_)
    )
    selected_crop = st.selectbox(
        "Crop",
        options=sorted(le_crop.classes_)
    )
    selected_season = st.selectbox(
        "Season",
        options=['Kharif', 'Rabi', 'Summer', 'Winter', 'Autumn', 'Whole Year']
    )
    selected_year = st.slider(
        "Year",
        min_value=1997, max_value=2030,
        value=2024
    )

with col2:
    st.markdown("**Rainfall (mm)**")
    annual_rain = st.slider(
        "Annual Rainfall",
        min_value=200, max_value=4000,
        value=1000, step=50
    )
    monsoon_rain = st.slider(
        "Monsoon Rainfall (Jun–Sep)",
        min_value=100, max_value=3000,
        value=700, step=50
    )
    winter_rain = st.slider(
        "Winter Rainfall (Oct–Dec)",
        min_value=0, max_value=500,
        value=80, step=10
    )
    summer_rain = st.slider(
        "Summer Rainfall (Mar–May)",
        min_value=0, max_value=500,
        value=50, step=10
    )

with col3:
    st.markdown("**Temperature (°C)**")
    mean_temp = st.slider(
        "Annual Mean Temperature",
        min_value=5.0, max_value=35.0,
        value=24.0, step=0.5
    )
    summer_temp = st.slider(
        "Summer Temperature (Mar–May)",
        min_value=10.0, max_value=45.0,
        value=30.0, step=0.5
    )
    monsoon_temp = st.slider(
        "Monsoon Temperature (Jun–Sep)",
        min_value=15.0, max_value=35.0,
        value=26.0, step=0.5
    )
    winter_temp = st.slider(
        "Winter Temperature (Oct–Jan)",
        min_value=0.0, max_value=25.0,
        value=18.0, step=0.5
    )

st.divider()

# ════════════════════════════════
# PREDICTION
# ════════════════════════════════
predict_btn = st.button("🔮 Predict Yield", type="primary",
                         use_container_width=True)

if predict_btn:
    # Encode inputs
    state_enc  = le_state.transform([selected_state])[0]
    crop_enc   = le_crop.transform([selected_crop])[0]
    season_map = {
        'Kharif':1,'Rabi':2,'Whole Year':3,
        'Summer':4,'Winter':5,'Autumn':6
    }
    temp_range = summer_temp - winter_temp

    feature_values = {
        'Crop_encoded'        : crop_enc,
        'Season_num'          : season_map.get(selected_season, 1),
        'State_encoded'       : state_enc,
        'year_trend'          : selected_year - 1997,
        'annual_rain'         : annual_rain,
        'monsoon_rain'        : monsoon_rain,
        'winter_rain'         : winter_rain,
        'summer_rain'         : summer_rain,
        'monsoon_rain_ratio'  : monsoon_rain / (annual_rain + 1),
        'annual_mean_temp'    : mean_temp,
        'summer_temp'         : summer_temp,
        'monsoon_temp'        : monsoon_temp,
        'winter_temp'         : winter_temp,
        'temp_range'          : temp_range,
        'heat_stress_index'   : summer_temp / (annual_rain / 100 + 1),
        'growing_season_score': monsoon_rain * monsoon_temp / 1000,
        'avg_ph'              : 7.2,
        'avg_nitrate'         : 1.5,
        'avg_dissolved_o2'    : 7.0,
        'total_area'          : 50000,
        'district_count'      : 10,
    }

    features_df = pd.DataFrame([feature_values])[ML_FEATURES]
    prediction  = float(model.predict(features_df)[0])
    prediction  = max(0.1, prediction)  # floor at 0.1

    # ── Result display ──
    st.success(f"### 🌾 Predicted Yield: **{prediction:.3f} kg/ha**")

    # Context metrics
    crop_df, _, _, _ = load_all_data()
    national_avg = crop_df['Yield'].mean()
    crop_avg     = crop_df[crop_df['Crop']==selected_crop]['Yield'].mean()
    state_avg    = crop_df[crop_df['State']==selected_state]['Yield'].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Your Prediction",   f"{prediction:.3f} kg/ha")
    c2.metric("National Average",  f"{national_avg:.3f} kg/ha",
              f"{((prediction-national_avg)/national_avg*100):+.1f}%")
    c3.metric(f"{selected_crop} Average", f"{crop_avg:.3f} kg/ha",
              f"{((prediction-crop_avg)/crop_avg*100):+.1f}%")
    c4.metric(f"{selected_state} Average", f"{state_avg:.3f} kg/ha",
              f"{((prediction-state_avg)/state_avg*100):+.1f}%")

    st.divider()

    # ── Scenario analysis ──
    st.subheader("📊 Rainfall Scenario Analysis")
    st.caption("How does yield change if rainfall increases or decreases?")

    scenarios = []
    for pct in [-40, -30, -20, -10, 0, 10, 20, 30, 40]:
        rain_adj    = annual_rain * (1 + pct/100)
        monsoon_adj = monsoon_rain * (1 + pct/100)

        fv = feature_values.copy()
        fv['annual_rain']        = rain_adj
        fv['monsoon_rain']       = monsoon_adj
        fv['monsoon_rain_ratio'] = monsoon_adj / (rain_adj + 1)
        fv['growing_season_score'] = monsoon_adj * monsoon_temp / 1000

        fdf  = pd.DataFrame([fv])[ML_FEATURES]
        pred = float(model.predict(fdf)[0])
        scenarios.append({
            'Rainfall Change': f"{pct:+d}%",
            'Predicted Yield': round(max(0.1, pred), 3),
            'pct'            : pct
        })

    scenario_df = pd.DataFrame(scenarios)
    colors = ['#e74c3c' if p < 0 else '#2ecc71' if p > 0 else '#3498db'
              for p in scenario_df['pct']]

    fig = go.Figure(go.Bar(
        x=scenario_df['Rainfall Change'],
        y=scenario_df['Predicted Yield'],
        marker_color=colors,
        text=scenario_df['Predicted Yield'],
        textposition='outside',
        texttemplate='%{text:.2f}'
    ))
    fig.add_hline(y=prediction, line_dash='dash',
                  line_color='white', opacity=0.5,
                  annotation_text='Baseline prediction')
    fig.update_layout(
        template='plotly_dark',
        height=380,
        margin=dict(l=0, r=0, t=20, b=0),
        xaxis_title='Rainfall Change from Input',
        yaxis_title='Predicted Yield (kg/ha)'
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Temperature scenario ──
    st.subheader("🌡️ Temperature Scenario Analysis")
    st.caption("How does yield change with rising temperatures?")

    temp_scenarios = []
    for delta in [-3, -2, -1, 0, 1, 2, 3, 4, 5]:
        fv = feature_values.copy()
        fv['annual_mean_temp'] = mean_temp   + delta
        fv['summer_temp']      = summer_temp + delta
        fv['monsoon_temp']     = monsoon_temp + delta
        fv['winter_temp']      = winter_temp + delta
        fv['heat_stress_index'] = (summer_temp+delta) / (annual_rain/100 + 1)
        fv['growing_season_score'] = monsoon_rain * (monsoon_temp+delta) / 1000

        fdf  = pd.DataFrame([fv])[ML_FEATURES]
        pred = float(model.predict(fdf)[0])
        temp_scenarios.append({
            'Temp Change': f"{delta:+d}°C",
            'Predicted Yield': round(max(0.1, pred), 3),
            'delta': delta
        })

    temp_df = pd.DataFrame(temp_scenarios)
    t_colors = ['#3498db' if d < 0 else '#e74c3c' if d > 2 else '#2ecc71'
                for d in temp_df['delta']]

    fig2 = go.Figure(go.Bar(
        x=temp_df['Temp Change'],
        y=temp_df['Predicted Yield'],
        marker_color=t_colors,
        text=temp_df['Predicted Yield'],
        textposition='outside',
        texttemplate='%{text:.2f}'
    ))
    fig2.add_hline(y=prediction, line_dash='dash',
                   line_color='white', opacity=0.5,
                   annotation_text='Baseline prediction')
    fig2.update_layout(
        template='plotly_dark',
        height=380,
        margin=dict(l=0, r=0, t=20, b=0),
        xaxis_title='Temperature Change from Input',
        yaxis_title='Predicted Yield (kg/ha)'
    )
    st.plotly_chart(fig2, use_container_width=True)

else:
    # Placeholder before prediction
    st.info("👆 Set your parameters above and click **Predict Yield** to see results.")
    st.markdown("""
    **What this predictor does:**
    - Takes climate inputs (rainfall, temperature) and location
    - Passes them through a trained XGBoost model
    - Returns predicted crop yield in kg/ha
    - Shows how yield changes under different climate scenarios

    **Model details:**
    - Algorithm: XGBoost Regressor
    - Training data: 5,486 samples, 1997–2020
    - Features: 21 climate, agricultural, and temporal variables
    """)

# ── Footer ──
st.divider()
st.caption("📊 Model trained on data.gov.in | XGBoost v2 | "
           "Agri-Climate Analysis Project")