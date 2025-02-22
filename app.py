import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
import xarray as xr
import matplotlib.pyplot as plt
from streamlit_folium import folium_static

# Streamlit App Title
st.title("PM2.5 Data Analysis & Visualization")

# Upload File
uploaded_file = st.file_uploader("Upload your dataset", type=["csv", "xlsx"])

df = None
if uploaded_file is not None:
    if uploaded_file.name.endswith("csv"):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith("xlsx"):
        df = pd.read_excel(uploaded_file)
    
    if df is not None:
        col_name = df.filter(like='PM2.5').columns[0]
        df.rename(columns={col_name: "PM2.5"}, inplace=True)
        df = df[df['PM2.5'] > 5]
        df['PM2.5'] = round(df['PM2.5'], 0)
        
        dt_col_name = df.filter(like='Datetime').columns[0]
        df.rename(columns={dt_col_name: 'datetime'}, inplace=True)

        if ('Name' and 'City') in df.columns:
            df = df[['datetime', 'City', 'Name', 'PM2.5', 'longitude', 'latitude']]
        else:
            df = df[['datetime', 'PM2.5', 'longitude', 'latitude']]

        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)

        st.write("### Data Preview")
        st.dataframe(df.head())

        # selected_years = st.multiselect("Select Year(s)", options=list(df.index.year.unique()), default=list(df.index.year.unique()))
        # df = df[df.index.year.isin(selected_years)]
        # if selected_years != "All":
        #     df = df[df.index.year.isin(selected_years)]
        
        if 'City' in df.columns:
            selected_city = st.selectbox("Select City", options=["All"] + list(df['City'].unique()))
            if selected_city != "All":
                df = df[df['City'] == selected_city]
        
        if 'Name' in df.columns:
            selected_name = st.selectbox("Select Monitor", options=["All"] + list(df['Name'].unique()))
            if selected_name != "All":
                df = df[df['Name'] == selected_name]

        df['PM2.5'] = df['PM2.5'].resample('1h').mean()
        
        # Date Filter options
        start_date, end_date = st.date_input("Select Date Range", [df.index.min(), df.index.max()])
        df = df[(df.index >= pd.Timestamp(start_date)) & (df.index <= pd.Timestamp(end_date))]
        df.sort_index(inplace=True)

        # Display basic statistics
        st.write("#### \nSummary Statistics")
        st.write(df[['PM2.5']].describe().loc[['min', 'max', 'mean']])
        
        st.write("#### PM2.5 Time Series")
        # Time-Series Plot
        ma_days = st.number_input("Enter Moving Average Window (Days)", min_value=1, max_value=30, value=7)
        df['PM2.5_MA'] = df['PM2.5'].rolling(window=ma_days).mean()
        
        scatter = go.Scatter(x=df.index, y=df['PM2.5'], mode='markers', color='red')
        line = go.Scatter(x=df.index, y=df['PM2.5_MA'])
        
        fig = go.Figure()
        fig.add_traces(scatter)
        fig.add_traces(line)
        st.plotly_chart(fig)

        st.write("#### PM2.5 Stripes")

        df['day_of_year'] = df.index.dayofyear
        df['year'] = df.index.year
        df_grouped = df.groupby(['year', 'day_of_year'])['PM2.5'].mean().reset_index()
        pm2_5_matrix = df_grouped.pivot(index='year', columns='day_of_year', values='PM2.5')
        
        fig, ax = plt.subplots(figsize=(30, 30))
        im = ax.imshow(pm2_5_matrix, aspect='auto', 
                       cmap='RdBu_r', 
                       interpolation='nearest', 
                       vmin=0, vmax=250)
        
        # Customizing the appearance
        ax.set_yticks(np.arange(len(pm2_5_matrix.index)))
        ax.set_yticklabels(pm2_5_matrix.index, color='white', fontsize=24)
        ax.set_xticks([])  # Remove xticks
        ax.set_xlabel("")
        # ax.set_ylabel("Year", color='white')
        fig.patch.set_alpha(0)  # Transparent background
        ax.set_facecolor("none")

        # Adding space between plots for each year
        fig.subplots_adjust(bottom=0.5, hspace=0.5)
        
        ax. set_frame_on(False)
        
        st.pyplot(fig)
    
        # # Geospatial Visualization (if lat/lon are present)
        # if 'latitude' in df.columns and 'longitude' in df.columns:
        #     st.write("### Geospatial Visualization")
        #     m = folium.Map(location=[df['latitude'].mean(), df['longitude'].mean()], zoom_start=10)
        #     for _, row in df.iterrows():
        #         folium.CircleMarker([row['latitude'], row['longitude']],
        #                             radius=5,
        #                             color='red',
        #                             fill=True,
        #                             fill_opacity=0.7).add_to(m)
        #     folium_static(m)
