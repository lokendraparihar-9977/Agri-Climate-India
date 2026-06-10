# pages/2_Map.py
import streamlit as st
import pandas as pd
import json
import os
import sys
import folium
from streamlit_folium import st_folium

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import load_all_data

st.set_page_config(
    page_title="Map View | AgriClimate India",
    page_icon="🗺️",
    layout="wide"
)

crop_df, rain_df, temp_df, water_df = load_all_data()

st.markdown("## 🗺️ India Crop Yield Map")
st.markdown("Geographic distribution of average crop yield across Indian states.")
st.divider()

# ── Sidebar filters ──
st.sidebar.header("🔧 Map Filters")

# Crop filter
all_crops = ['All Crops'] + sorted(crop_df['Crop'].unique())
selected_crop = st.sidebar.selectbox("Select Crop", all_crops)

# Year range
min_yr = int(crop_df['Crop_Year'].min())
max_yr = int(crop_df['Crop_Year'].max())
year_range = st.sidebar.slider(
    "Year Range",
    min_value=min_yr, max_value=max_yr,
    value=(min_yr, max_yr)
)

# Season filter
all_seasons = ['All Seasons'] + sorted(crop_df['Season'].unique())
selected_season = st.sidebar.selectbox("Select Season", all_seasons)

# ── Apply filters ──
map_df = crop_df[
    (crop_df['Crop_Year'] >= year_range[0]) &
    (crop_df['Crop_Year'] <= year_range[1])
]
if selected_crop != 'All Crops':
    map_df = map_df[map_df['Crop'] == selected_crop]
if selected_season != 'All Seasons':
    map_df = map_df[map_df['Season'] == selected_season]

# ── State name mapping (same as Week 5) ──
STATE_MAP = {
    'Andaman And Nicobar Islands' : 'Andaman and Nicobar',
    'Dadra And Nagar Haveli'      : 'Dadra and Nagar Haveli',
    'Daman And Diu'               : 'Daman and Diu',
    'Jammu And Kashmir'           : 'Jammu and Kashmir',
    'Ladakh'                      : 'Jammu and Kashmir',
    'Odisha'                      : 'Orissa',
    'Uttarakhand'                 : 'Uttaranchal',
}
map_df = map_df.copy()
map_df['State_geo'] = map_df['State'].replace(STATE_MAP)

# ── Compute state-level yield ──
state_yield = (
    map_df.groupby('State_geo')['Yield']
    .mean().reset_index()
)
state_yield.columns = ['State', 'avg_yield']
state_yield['avg_yield'] = state_yield['avg_yield'].round(3)

# ── Sidebar stats ──
st.sidebar.divider()
st.sidebar.metric("States with data", state_yield['State'].nunique())
st.sidebar.metric("Avg yield (filtered)",
                  f"{state_yield['avg_yield'].mean():.3f} kg/ha")
st.sidebar.metric("Highest yielding state",
                  state_yield.loc[state_yield['avg_yield'].idxmax(), 'State'])

# ── Load GeoJSON ──
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
geo_path = os.path.join(BASE_DIR, 'Outputs', 'india_states.geojson')

try:
    with open(geo_path) as f:
        geo = json.load(f)
    geo_loaded = True
except FileNotFoundError:
    geo_loaded = False
    st.error("GeoJSON file not found. Make sure india_states.geojson is in your Outputs folder.")

if geo_loaded:
    # Find key field
    key_field = None
    for k in ['NAME_1', 'ST_NM', 'name', 'NAME']:
        if k in geo['features'][0]['properties']:
            key_field = k
            break

    # Add yield to GeoJSON properties for popup
    yield_dict = dict(zip(state_yield['State'],
                          state_yield['avg_yield'].astype(str) + ' kg/ha'))
    for feat in geo['features']:
        sname = feat['properties'].get(key_field, '')
        feat['properties']['avg_yield'] = yield_dict.get(sname, 'No data')

    # ── Build map ──
    m = folium.Map(
        location=[20.5937, 78.9629],
        zoom_start=5,
        tiles='CartoDB positron',
        prefer_canvas=True
    )

    choropleth = folium.Choropleth(
        geo_data=geo,
        name='Crop Yield',
        data=state_yield,
        columns=['State', 'avg_yield'],
        key_on=f'feature.properties.{key_field}',
        fill_color='YlGn',
        fill_opacity=0.75,
        line_opacity=0.4,
        line_color='white',
        legend_name=f'Avg Yield (kg/ha) — {selected_crop} | {selected_season}',
        highlight=True,
        nan_fill_color='#e0e0e0',
    ).add_to(m)

    folium.GeoJsonTooltip(
        fields=[key_field, 'avg_yield'],
        aliases=['State:', 'Avg Yield:'],
        style="""
            background-color: white;
            border: 1px solid #333;
            border-radius: 4px;
            padding: 6px 10px;
            font-size: 13px;
        """
    ).add_to(choropleth.geojson)

    # Title overlay
    title_html = f"""
    <div style="position:fixed;top:15px;left:50%;transform:translateX(-50%);
         z-index:1000;background:white;padding:8px 18px;
         border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.2);
         font-family:sans-serif;font-size:14px;font-weight:bold;color:#2C3E50;">
        🌾 {selected_crop} · {selected_season} · {year_range[0]}–{year_range[1]}
    </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))

    # ── Render map in Streamlit ──
    st.info("💡 Hover over any state to see its average yield. "
            "Use sidebar filters to explore different crops and seasons.")

    map_data = st_folium(m, width=1100, height=580)

    # ── Yield ranking table below map ──
    st.divider()
    st.subheader("State Yield Rankings")

    col_a, col_b = st.columns([1, 2])

    with col_a:
        ranked = (state_yield
                  .sort_values('avg_yield', ascending=False)
                  .reset_index(drop=True))
        ranked.index += 1
        ranked.columns = ['State', 'Avg Yield (kg/ha)']
        st.dataframe(ranked, use_container_width=True, height=400)

    with col_b:
        import plotly.express as px
        top15 = ranked.head(15)
        fig = px.bar(
            top15,
            x='Avg Yield (kg/ha)',
            y='State',
            orientation='h',
            color='Avg Yield (kg/ha)',
            color_continuous_scale='YlGn',
            template='plotly_white',
            title=f'Top 15 States — {selected_crop} · {selected_season}'
        )
        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            coloraxis_showscale=False,
            margin=dict(l=0, r=0, t=40, b=0),
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

# ── Footer ──
st.divider()
st.caption("📊 Data source: data.gov.in | Built with Streamlit + Folium | "
           "Agri-Climate Analysis Project")