# app.py — Main entry point for the Streamlit dashboard
import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os

# Add utils to path so we can import data_loader
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.data_loader import load_all_data, get_state_yield_summary, get_yearly_trend

# ── Page configuration ──
# This must be the FIRST streamlit command in the file
st.set_page_config(
    page_title     = "AgriClimate India",
    page_icon      = "🌾",
    layout         = "wide",          # use full browser width
    initial_sidebar_state = "expanded"
)

# ── Custom CSS ──
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2C3E50;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #7F8C8D;
        margin-top: 0;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
    }
    .metric-label {
        font-size: 0.85rem;
        opacity: 0.85;
    }
</style>
""", unsafe_allow_html=True)

# ── Load data ──
crop_df, rain_df, temp_df, water_df = load_all_data()

# ── Header ──
st.markdown("## 🌾 AgriClimate India")
st.markdown("Crop Yield & Climate Analysis Dashboard · 1997–2020")

st.divider()

# ── Key metrics row ──
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(label="📋 Total Records",
              value=f"{len(crop_df):,}")
with col2:
    st.metric(label="🗺️ States Covered",
              value=crop_df['State'].nunique())
with col3:
    st.metric(label="🌱 Crops Tracked",
              value=crop_df['Crop'].nunique())
with col4:
    st.metric(label="📅 Year Range",
              value="1997–2020")
with col5:
    st.metric(label="📈 Avg National Yield",
              value=f"{crop_df['Yield'].mean():.2f} kg/ha")

st.divider()

# ── Two column layout ──
col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("National Yield Trend")
    yearly = get_yearly_trend(crop_df)
    fig = px.area(
        yearly,
        x='Crop_Year', y='Yield',
        labels={'Crop_Year': 'Year', 'Yield': 'Avg Yield (kg/ha)'},
        color_discrete_sequence=['#2E86AB'],
        template='plotly_white'
    )
    fig.update_traces(line_width=2.5)
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=320)
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("Production by Season")
    season_data = crop_df.groupby('Season')['Production'].sum().reset_index()
    fig2 = px.pie(
        season_data,
        values='Production', names='Season',
        color_discrete_sequence=px.colors.qualitative.Set2,
        template='plotly_white',
        hole=0.4   # donut chart looks cleaner
    )
    fig2.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=320)
    st.plotly_chart(fig2, use_container_width=True)

# ── Top states table ──
st.divider()
st.subheader("Top 10 States by Average Yield")

state_yield = get_state_yield_summary(crop_df)
top10 = state_yield.head(10).copy()
top10['avg_yield'] = top10['avg_yield'].round(3)
top10.index = range(1, 11)   # rank from 1
top10.columns = ['State', 'Average Yield (kg/ha)']

col_t, col_b = st.columns([1, 2])
with col_t:
    st.dataframe(top10, use_container_width=True)
with col_b:
    fig3 = px.bar(
        top10.reset_index(),
        x='Average Yield (kg/ha)', y='State',
        orientation='h',
        color='Average Yield (kg/ha)',
        color_continuous_scale='Greens',
        template='plotly_white',
        labels={'index': 'Rank'}
    )
    fig3.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=320,
        yaxis={'categoryorder': 'total ascending'},
        coloraxis_showscale=False
    )
    st.plotly_chart(fig3, use_container_width=True)

# ── Footer ──
st.divider()
st.caption("📊 Data source: data.gov.in | Built with Streamlit + Plotly | "
           "Agri-Climate Analysis Project")