# pages/1_EDA.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import load_all_data

# ── Page config ──
st.set_page_config(
    page_title="EDA Explorer | AgriClimate India",
    page_icon="📊",
    layout="wide"
)

# ── Load data ──
crop_df, rain_df, temp_df, water_df = load_all_data()

# ── Header ──
st.markdown("## 📊 EDA Explorer")
st.markdown("Interactively explore crop yield patterns across states, crops, and years.")
st.divider()

# ════════════════════════════════════════════
# SIDEBAR FILTERS
# ════════════════════════════════════════════
st.sidebar.header("🔧 Filters")
st.sidebar.markdown("Use these to slice the data any way you want.")

# Year range slider
min_year = int(crop_df['Crop_Year'].min())
max_year = int(crop_df['Crop_Year'].max())
year_range = st.sidebar.slider(
    "Year Range",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),   # default: all years selected
    step=1
)

# State multiselect
all_states = sorted(crop_df['State'].unique())
selected_states = st.sidebar.multiselect(
    "Select States",
    options=all_states,
    default=['Punjab', 'Haryana', 'Uttar Pradesh',
             'Maharashtra', 'Tamil Nadu', 'West Bengal']
)

# Crop selector
all_crops = sorted(crop_df['Crop'].unique())
selected_crops = st.sidebar.multiselect(
    "Select Crops",
    options=all_crops,
    default=['Rice', 'Wheat']
)

# Season filter
all_seasons = sorted(crop_df['Season'].unique())
selected_seasons = st.sidebar.multiselect(
    "Select Seasons",
    options=all_seasons,
    default=all_seasons   # all seasons by default
)

# ── Apply filters ──
# This is the filtered dataframe — all charts below use this
filtered_df = crop_df[
    (crop_df['Crop_Year'] >= year_range[0]) &
    (crop_df['Crop_Year'] <= year_range[1])
]

# Only filter by state/crop/season if user selected something
if selected_states:
    filtered_df = filtered_df[filtered_df['State'].isin(selected_states)]
if selected_crops:
    filtered_df = filtered_df[filtered_df['Crop'].isin(selected_crops)]
if selected_seasons:
    filtered_df = filtered_df[filtered_df['Season'].isin(selected_seasons)]

# Show how many records match current filters
st.sidebar.divider()
st.sidebar.metric("Records matching filters", f"{len(filtered_df):,}")

# Guard: if filters return no data, show warning
if filtered_df.empty:
    st.warning("⚠️ No data matches your current filters. "
               "Try selecting more states, crops, or a wider year range.")
    st.stop()

# ════════════════════════════════════════════
# ROW 1 — Yield trend + State comparison
# ════════════════════════════════════════════
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("Yield Trend Over Time")

    if selected_crops and len(selected_crops) <= 8:
        # Line per crop
        trend_data = (
            filtered_df.groupby(['Crop_Year', 'Crop'])['Yield']
            .mean().reset_index()
        )
        fig = px.line(
            trend_data,
            x='Crop_Year', y='Yield',
            color='Crop',
            markers=True,
            labels={'Crop_Year': 'Year', 'Yield': 'Avg Yield (kg/ha)'},
            template='plotly_white',
            color_discrete_sequence=px.colors.qualitative.Set2
        )
    else:
        # Overall trend
        trend_data = filtered_df.groupby('Crop_Year')['Yield'].mean().reset_index()
        fig = px.area(
            trend_data,
            x='Crop_Year', y='Yield',
            labels={'Crop_Year': 'Year', 'Yield': 'Avg Yield (kg/ha)'},
            template='plotly_white',
            color_discrete_sequence=['#2E86AB']
        )

    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=350,
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    fig.update_traces(line_width=2.5)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("State-wise Average Yield")

    state_avg = (
        filtered_df.groupby('State')['Yield']
        .mean().sort_values(ascending=True)
        .reset_index()
    )

    fig2 = px.bar(
        state_avg,
        x='Yield', y='State',
        orientation='h',
        color='Yield',
        color_continuous_scale='YlGn',
        labels={'Yield': 'Avg Yield (kg/ha)', 'State': ''},
        template='plotly_white'
    )
    fig2.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=350,
        coloraxis_showscale=False
    )
    st.plotly_chart(fig2, use_container_width=True)

# ════════════════════════════════════════════
# ROW 2 — Distribution + Crop comparison
# ════════════════════════════════════════════
st.divider()
col3, col4 = st.columns(2)

with col3:
    st.subheader("Yield Distribution by Crop")

    if not selected_crops:
        st.info("Select crops in the sidebar to see distribution.")
    else:
        fig3 = go.Figure()
        colors = px.colors.qualitative.Set2

        for i, crop in enumerate(selected_crops):
            crop_data = filtered_df[filtered_df['Crop'] == crop]['Yield']
            if not crop_data.empty:
                fig3.add_trace(go.Violin(
                    y=crop_data,
                    name=crop,
                    box_visible=True,       # show box plot inside violin
                    meanline_visible=True,  # show mean line
                    fillcolor=colors[i % len(colors)],
                    opacity=0.7,
                    line_color=colors[i % len(colors)]
                ))

        fig3.update_layout(
            template='plotly_white',
            margin=dict(l=0, r=0, t=10, b=0),
            height=350,
            yaxis_title='Yield (kg/ha)',
            showlegend=False,
            violingap=0.3
        )
        st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("Top Crops by Cultivated Area")

    crop_area = (
        filtered_df.groupby('Crop')['Area']
        .sum().sort_values(ascending=False)
        .head(10).reset_index()
    )

    fig4 = px.bar(
        crop_area,
        x='Crop', y='Area',
        color='Area',
        color_continuous_scale='Greens',
        labels={'Area': 'Total Area (ha)', 'Crop': ''},
        template='plotly_white'
    )
    fig4.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=350,
        coloraxis_showscale=False,
        xaxis_tickangle=-30
    )
    st.plotly_chart(fig4, use_container_width=True)

# ════════════════════════════════════════════
# ROW 3 — Rainfall correlation + Season breakdown
# ════════════════════════════════════════════
st.divider()
col5, col6 = st.columns(2)

with col5:
    st.subheader("Yield vs Area — Bubble Chart")
    st.caption("Each bubble = one state · Size = total production · Colour = yield")

    bubble_data = (
        filtered_df.groupby('State').agg(
            avg_yield       = ('Yield', 'mean'),
            avg_area        = ('Area', 'mean'),
            total_production= ('Production', 'sum')
        ).reset_index()
    )

    fig5 = px.scatter(
        bubble_data,
        x='avg_area',
        y='avg_yield',
        size='total_production',
        color='avg_yield',
        hover_name='State',
        color_continuous_scale='YlGn',
        size_max=60,
        labels={
            'avg_area' : 'Avg Area per Record (ha)',
            'avg_yield': 'Avg Yield (kg/ha)',
        },
        template='plotly_white'
    )
    fig5.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=350,
        coloraxis_showscale=False
    )
    st.plotly_chart(fig5, use_container_width=True)

with col6:
    st.subheader("Season-wise Yield Comparison")

    season_yield = (
        filtered_df.groupby('Season')['Yield']
        .mean().sort_values(ascending=False)
        .reset_index()
    )

    fig6 = px.bar(
        season_yield,
        x='Season', y='Yield',
        color='Season',
        color_discrete_sequence=px.colors.qualitative.Set2,
        labels={'Yield': 'Avg Yield (kg/ha)', 'Season': ''},
        template='plotly_white',
        text='Yield'
    )
    fig6.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig6.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=350,
        showlegend=False
    )
    st.plotly_chart(fig6, use_container_width=True)

# ════════════════════════════════════════════
# ROW 4 — Raw data explorer
# ════════════════════════════════════════════
st.divider()
st.subheader("🔍 Raw Data Explorer")
st.caption("Explore the filtered data directly — sortable and searchable.")

# Summary stats
c1, c2, c3, c4 = st.columns(4)
c1.metric("Records", f"{len(filtered_df):,}")
c2.metric("Avg Yield", f"{filtered_df['Yield'].mean():.3f} kg/ha")
c3.metric("Max Yield", f"{filtered_df['Yield'].max():.3f} kg/ha")
c4.metric("Min Yield", f"{filtered_df['Yield'].min():.3f} kg/ha")

# Show/hide raw data toggle
if st.checkbox("Show raw data table"):
    st.dataframe(
        filtered_df.sort_values('Yield', ascending=False)
                   .reset_index(drop=True)
                   .head(500),   # cap at 500 rows for performance
        use_container_width=True,
        height=300
    )
    st.caption("Showing top 500 rows by yield. "
               "Download the full dataset from the Data/ folder.")

# ── Footer ──
st.divider()
st.caption("📊 Data source: data.gov.in | Built with Streamlit + Plotly | "
           "Agri-Climate Analysis Project")