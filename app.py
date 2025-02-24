import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
from folium.plugins import MarkerCluster
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib import cm, colors
from streamlit_folium import folium_static

# Streamlit App Title
st.title("PM2.5 Data Analysis & Visualization")

# Upload File
uploaded_file = st.file_uploader("Upload your dataset", type=["csv"])

if uploaded_file is not None:
    if uploaded_file.name.endswith("csv"):
        df = pd.read_csv(uploaded_file)
    
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

        copy_df = df.copy()

        st.write("### Data Preview")
        st.dataframe(copy_df.head())

        # selected_years = st.multiselect("Select Year(s)", options=list(df.index.year.unique()), default=list(df.index.year.unique()))
        # df = df[df.index.year.isin(selected_years)]
        # if selected_years != "All":
        #     df = df[df.index.year.isin(selected_years)]
        
        if 'City' in df.columns:
            selected_city = st.selectbox("Select City", options=["All"] + list(df['City'].unique()))
            if selected_city != "All":
                copy_df = copy_df[copy_df['City'] == selected_city]
        
        if 'Name' in df.columns:
            selected_name = st.selectbox("Select Monitor", options=["All"] + list(df['Name'].unique()))
            if selected_name != "All":
                copy_df = copy_df[copy_df['Name'] == selected_name]

        copy_df['PM2.5'] = copy_df['PM2.5'].resample('1h').mean()
        
        # Date Filter options
        start_date, end_date = st.date_input("Select Date Range", [copy_df.index.min(), copy_df.index.max()])
        copy_df = copy_df[(copy_df.index >= pd.Timestamp(start_date)) & (copy_df.index <= pd.Timestamp(end_date))]
        copy_df.sort_index(inplace=True)

        ##################### new section
        st.write("#### \nSummary Statistics")
        st.write(copy_df[['PM2.5']].describe().loc[['min', 'max', 'mean']])
        
        ##################### new section
        st.write("#### PM2.5 Time Series")

        # ma_days = st.number_input("Enter Moving Average Window (Days)", min_value=1, max_value=30, value=7)
        # df['PM2.5_MA'] = df['PM2.5'].rolling(window=ma_days).mean()
        
        scatter = go.Scatter(x=copy_df.index, y=copy_df['PM2.5'], mode='markers')
        # line = go.Scatter(x=df.index, y=df['PM2.5_MA'])
        
        fig = go.Figure()
        fig.add_traces(scatter)
        # fig.add_traces(line)
        st.plotly_chart(fig)

        ##################### new section
        st.write("#### PM2.5 Stripes")
        stripes_df = df.copy()
        selected_city = st.selectbox("Select City", options=list(stripes_df['City'].unique()))   
        stripes_df = stripes_df[stripes_df['City'] == selected_city]
        stripes_df['day_of_year'] = stripes_df.index.dayofyear
        stripes_df['year'] = stripes_df.index.year
        df_grouped = stripes_df.groupby(['year', 'day_of_year'])['PM2.5'].mean().reset_index()
        pm2_5_matrix = df_grouped.pivot(index='year', columns='day_of_year', values='PM2.5')

        cmap = cm.coolwarm
        norm = colors.Normalize(vmin=0, vmax=200)
        
        fig, ax = plt.subplots(figsize=(30, 40))
        cax = ax.imshow(pm2_5_matrix, aspect='auto', cmap=cmap, norm=norm)
        
        ax.set_yticks(np.arange(len(pm2_5_matrix.index)))
        ax.set_yticklabels(pm2_5_matrix.index, color='white', fontsize=24)
        ax.set_xticks([])
        ax.set_xlabel("")
        ax.set_ylabel("")
        
        fig.patch.set_alpha(0)
        ax.set_facecolor("none")
        ax.set_frame_on(False)

        # cbar = fig.colorbar(cax, orientation='horizontal', pad=0.1)
        # cbar.set_label("PM2.5 Levels", color='white')
        # cbar.ax.xaxis.set_tick_params(color='white')
        # plt.setp(cbar.ax.xaxis.get_ticklabels(), color='white')
        
        st.pyplot(fig)

        ##################### new section
        st.write("#### Comparative Analysis")
        if df['City'].nunique() > 1:
            city_avg_pm25 = df.pivot_table(index = 'datetime', columns='City', values='PM2.5', aggfunc='mean')
            selected_cities = st.multiselect("Select Cities", options=list(df['City'].unique()), default=df['City'].unique()[0])
            city_avg_pm25 = city_avg_pm25[selected_cities]

            # daily, monthly, annually
            selected_trend = st.radio("Select Time Trend", options=['Daily', 'Monthly', 'Annually'])

            if selected_trend == 'Daily':
                city_avg_pm25 = city_avg_pm25.resample('d').mean().sort_index()
                city_trends = px.line(city_avg_pm25, x=city_avg_pm25.index, y=selected_cities)
            elif selected_trend == 'Monthly':
                city_avg_pm25 = city_avg_pm25.resample('ms').mean().sort_index()
                city_trends = px.line(city_avg_pm25, x=city_avg_pm25.index, y=selected_cities)
            else:
                city_avg_pm25 = city_avg_pm25.resample('ys').mean().sort_index()
                city_avg_pm25.index = city_avg_pm25.index.year  
                city_trends = px.bar(city_avg_pm25, x=city_avg_pm25.index, y=selected_cities, barmode="group", labels=None)

            st.plotly_chart(city_trends)
        
        else:
            st.write("###### Need more than 1 city for comparison!")

    
        # Geospatial Visualization with Matplotlib Colormap
        if ('latitude' and 'longitude') in df.columns:
            st.write("### Geospatial Visualization")

            map_df = df.copy()
            start_date, end_date = st.date_input("Select Date Range", [map_df.index.min(), map_df.index.max()])
            map_df = map_df.loc[start_date:end_date]
            map_df = pd.DataFrame(map_df.groupby(['Name', 'longitude', 'latitude'])['PM2.5'].mean()).reset_index()

            m = folium.Map(location=[map_df['latitude'].mean(), map_df['longitude'].mean()], zoom_start=8)

            # US EPA PM2.5 Breakpoints and Colors
            pm25_breakpoints = [0, 12, 35.4, 55.4, 150.4, 250.4, 500.4]
            colors = ["#00E400", "#FFFF00", "#FF7E00", "#FF0000", "#8F3F97", "#7E0023"]

            def get_pm25_color(value):
                for i in range(len(pm25_breakpoints) - 1):
                    if pm25_breakpoints[i] <= value <= pm25_breakpoints[i + 1]:
                        return colors[i]
                return "gray"
            
            icon_create_function='''
            function(cluster) {
                var maxPm25 = Math.max.apply(null, cluster.getAllChildMarkers().map(m => parseFloat(m.options.pm25) || -Infinity));

                function getColor(value) {
                    if (value <= 12) return "#00E400";   // Good (Green)
                    if (value <= 35.4) return "#FFFF00";  // Moderate (Yellow)
                    if (value <= 55.4) return "#FF7E00";  // Unhealthy for Sensitive Groups (Orange)
                    if (value <= 150.4) return "#FF0000"; // Unhealthy (Red)
                    if (value <= 250.4) return "#8F3F97"; // Very Unhealthy (Purple)
                    return "#7E0023";                    // Hazardous (Maroon)
                }

                var bgColor = getColor(maxPm25);

                return L.divIcon({
                    html: '<div style="background-color:' + bgColor + '; color: white; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; font-weight: bold;">' + maxPm25.toFixed(0) + '</div>',
                    className: 'marker-cluster',
                    iconSize: L.point(40, 40)
                });
            }
        '''
            
            marker_cluster = MarkerCluster(icon_create_function=icon_create_function)
            
            for _, row in map_df.iterrows():
                color = get_pm25_color(row['PM2.5']) if not pd.isna(row['PM2.5']) else "gray"
                marker = folium.CircleMarker(
                    [row['latitude'], row['longitude']],
                    radius=10,
                    color=color,
                    fill=True,
                    fill_opacity=0.7
                )
                marker.options["pm25"] = round(row['PM2.5'], 0)
                marker.add_to(marker_cluster)
                
                # text_html = f'''<div style="color: white; font-size: 12px; font-weight: bold; text-align: center;">{round(row['PM2.5'])}</div>'''
                folium.Marker(
                    [row['latitude'], row['longitude']]
                ).add_to(marker_cluster)
            
            marker_cluster.add_to(m)
            folium_static(m)