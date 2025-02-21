import streamlit as st
import pandas as pd
import plotly.express as px
import folium
import xarray as xr
from streamlit_folium import folium_static

# Streamlit App Title
st.title("PM2.5 Data Analysis & Visualization Tool")

# Upload File
uploaded_file = st.file_uploader("Upload your dataset (CSV, Excel, or NetCDF)", type=["csv", "xlsx", "nc"])

df = None
if uploaded_file is not None:
    if uploaded_file.name.endswith("csv"):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith("xlsx"):
        df = pd.read_excel(uploaded_file)
    elif uploaded_file.name.endswith("nc"):
        ds = xr.open_dataset(uploaded_file)
        df = ds.to_dataframe().reset_index()
    
    if df is not None:
        st.write("### Data Preview")
        st.dataframe(df.head())
        
        # Display basic statistics
        st.write("### Summary Statistics")
        st.write(df.describe())
        
        # Filter options
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
            start_date, end_date = st.date_input("Select Date Range", [df['datetime'].min(), df['datetime'].max()])
            df = df[(df['datetime'] >= pd.Timestamp(start_date)) & (df['datetime'] <= pd.Timestamp(end_date))]
        
        # Time-Series Plot
        if 'datetime' in df.columns and 'PM2.5' in df.columns:
            fig = px.line(df, x='datetime', y='PM2.5', title='PM2.5 Levels Over Time')
            st.plotly_chart(fig)
        
        # Geospatial Visualization (if lat/lon are present)
        if 'latitude' in df.columns and 'longitude' in df.columns:
            st.write("### Geospatial Visualization")
            m = folium.Map(location=[df['latitude'].mean(), df['longitude'].mean()], zoom_start=10)
            for _, row in df.iterrows():
                folium.CircleMarker([row['latitude'], row['longitude']],
                                    radius=5,
                                    color='red',
                                    fill=True,
                                    fill_opacity=0.7).add_to(m)
            folium_static(m)
