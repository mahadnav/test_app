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
from matplotlib.colors import ListedColormap, BoundaryNorm
from streamlit_folium import folium_static

st.set_page_config(layout="wide",
                   page_title="PM2.5 Data Analysis & Visualization",
                   page_icon=':earth_americas:',)

# Create a centered layout for everything except the map
centered_col = st.columns([0.15, 0.7, 0.15])  # 15% margin on both sides

def map_legend():
    with centered_col[0]:
        st.markdown("""
            <div style="
                position: relative;
                padding: 10px;
                background: rgba(255, 255, 255, 0);
                border-radius: 8px;
                width: 90%;
                box-shadow: 2px 2px 5px rgba(0,0,0,0);
                margin-top: 550px; /* Adjust this value to move it down */
            ">
                <b>Legend</b><br>
                <span style="background:#00E400; padding:5px; display:inline-block; width:20px;"></span> Good (0 - 12) <br>
                <span style="background:#eedc5b; padding:5px; display:inline-block; width:20px;"></span> Moderate (12.1 - 35.4) <br>
                <span style="background:#FF7E00; padding:5px; display:inline-block; width:20px;"></span> Unhealthy for Sensitive Groups (35.5 - 55.4) <br>
                <span style="background:#FF0000; padding:5px; display:inline-block; width:20px;"></span> Unhealthy (55.5 - 150.4) <br>
                <span style="background:#8F3F97; padding:5px; display:inline-block; width:20px;"></span> Very Unhealthy (150.5 - 250.4) <br>
                <span style="background:#7E0023; padding:5px; display:inline-block; width:20px;"></span> Hazardous (250.5+) <br>
            </div>
        """, unsafe_allow_html=True)

with centered_col[1]:

    # Set the title that appears at the top of the page.
    '''
    # :earth_americas: PM2.5 Data Analysis & Visualization

        This tool allows you to upload your data set and analyze it in just a few seconds!
    '''

    ''
    ''

    def get_data():
        data = st.file_uploader("Upload your dataset", type=["csv"])
        return data
    uploaded_file = get_data()

    if uploaded_file is not None:
        if uploaded_file.name.endswith("csv"):
            df = pd.read_csv(uploaded_file)
        else:
            st.write('Please make sure it\'s a CSV file!')
        
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






            ########################## new section
            # Geospatial Visualization with Matplotlib Colormap
            # st.header('\nAir Quality Map', divider='gray')


            if ('longitude' and 'latitude') in df.columns:
                map_legend()

                map_df = df.copy()
                year = map_df.index.year[-1]
                # start_date, end_date = st.date_input("Select Date Range", [map_df.index.min(), map_df.index.max()])
                # start_date, end_date = [map_df.index.date[-30], map_df.index.date[-1]]
                map_df = map_df[map_df.index.year == year]
                map_df = pd.DataFrame(map_df.groupby(['Name', 'longitude', 'latitude'])['PM2.5'].mean()).reset_index()

                m = folium.Map(location=[map_df['latitude'].mean(), map_df['longitude'].mean()], 
                            zoom_start=5,
                            control_scale=True)
                
                # US EPA PM2.5 Breakpoints and Colors
                pm25_breakpoints = [0, 12, 35.4, 55.4, 150.4, 250.4, 500.4]
                colors = ["#00E400", "#eedc5b", "#FF7E00", "#FF0000", "#8F3F97", "#7E0023"]

                def get_pm25_color(value):
                    for i in range(len(pm25_breakpoints) - 1):
                        if pm25_breakpoints[i] <= value <= pm25_breakpoints[i + 1]:
                            return colors[i]
                    return "gray"
                
                icon_create_function='''
                    function(cluster) {
                        var pm25Values = cluster.getAllChildMarkers()
                            .map(m => parseFloat(m.options.pm25))  // Extract PM2.5 values
                            .filter(v => !isNaN(v));  // Remove NaN values

                        if (pm25Values.length === 0) return L.divIcon({ html: "<div>No Data</div>", className: "marker-cluster" });

                        var meanPm25 = pm25Values.reduce((sum, value) => sum + value, 0) / pm25Values.length; // Compute mean

                        function getColor(value) {
                            if (value <= 12) return "#00E400";   // Good (Green)
                            if (value <= 35.4) return "#eedc5b";  // Moderate (Yellow)
                            if (value <= 55.4) return "#FF7E00";  // Unhealthy for Sensitive Groups (Orange)
                            if (value <= 150.4) return "#FF0000"; // Unhealthy (Red)
                            if (value <= 250.4) return "#8F3F97"; // Very Unhealthy (Purple)
                            return "#7E0023";                    // Hazardous (Maroon)
                        }

                        var bgColor = getColor(meanPm25);

                        return L.divIcon({
                            html: '<div style="background-color:' + bgColor + 
                                '; color: white; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; font-weight: bold;">' 
                                + meanPm25.toFixed(0) + '</div>',
                            className: 'marker-cluster',
                            iconSize: L.point(60, 60)
                        });
                    }
                '''
                
                marker_cluster = MarkerCluster(maxClusterRadius=20,
                                            disableClusteringAtZoom=20,
                                            icon_create_function=icon_create_function, 
                                            )
                
                for _, row in map_df.iterrows():
                    color = get_pm25_color(row['PM2.5']) if not pd.isna(row['PM2.5']) else "gray"
                    marker = folium.CircleMarker(
                        [row['latitude'], row['longitude']],
                        radius=10,
                        color=color,
                        fill=True,
                        fill_opacity=0.7
                    )
                    marker.options["pm25"] = int(row['PM2.5'])
                    marker.add_to(marker_cluster)
                    
                    folium.Marker(
                        [row['latitude'], row['longitude']]
                    ).add_to(marker_cluster)
                
                marker_cluster.add_to(m)

                folium_static(m, width=1220, height=700)





            ################################# new section
            st.header('Filter Dataset', divider='gray')
            copy_df = df.copy()
            if 'City' in df.columns:
                selected_city = st.selectbox("Select City", options=list(copy_df['City'].unique()))
                copy_df = copy_df[copy_df['City'] == selected_city]
            
            if 'Name' in df.columns:
                selected_name = st.selectbox("Select Monitor", options=["All"] + list(copy_df['Name'].unique()))
                if selected_name != "All":
                    copy_df = copy_df[copy_df['Name'] == selected_name]

            copy_df['PM2.5'] = copy_df['PM2.5'].resample('1h').mean()
            copy_df.dropna(inplace=True)
            
            # Date Filter options
            start_year, end_year = st.slider("Select Year Range", 
                                             min_value=copy_df.index.year.min(),
                                             max_value=copy_df.index.year.max(),
                                             value=[copy_df.index.year.min(), copy_df.index.year.max()]
                                             )
            copy_df = copy_df[(copy_df.index.year >= start_year) & (copy_df.index.year <= end_year)]
            copy_df.sort_index(inplace=True)




            ################################### new section
            st.write("#### Air Quality KPIs")

            # Calculate KPIs ####################################### create this for each city in the df
            min_pm25 = int(copy_df["PM2.5"].min())
            max_pm25 = int(copy_df["PM2.5"].max())
            mean_pm25 = int(copy_df["PM2.5"].mean())

            # Create small trend graphs using Plotly
            def create_sparkline(data, color):
                fig = go.Figure()
                fig.add_trace(go.Scatter(y=data, mode="lines", line=dict(color=color, width=1)))
                fig.update_layout(margin=dict(l=75, r=75, t=0, b=5), xaxis=dict(visible=False), yaxis=dict(visible=False), height=50)
                return fig

            col1, col2, col3 = st.columns(3)

            def kpi_card(title, value, unit, color, start_value, end_value):
                percentage_change = ((end_value - start_value) / start_value) * 100 if start_value != 0 else 0
                
                # Set arrow and color
                if percentage_change > 0:
                    arrow = "🔺"
                    percentage_color = "red"
                elif percentage_change < 0:
                    arrow = "🔻"
                    percentage_color = "green"
                else:
                    arrow = "🔵"
                    percentage_color = "blue"
                percentage_color = "red" if percentage_change > 0 else "green"
                
                st.markdown(f"""
                    <div style="border: 2px; border-radius: 10px; padding: 10px; text-align: center;">
                        <p style="margin-bottom: 4px; font-size: 16px; color: gray;">{title}</p>
                        <h2 style="margin: 0; font-size: 48px; color: white; text-align: center">
                            {value}
                        </h2>
                        <p style="font-size: 18px; color: {percentage_color};">
                            {arrow} {int(percentage_change)}%
                        </p>
                    </div>
                """, unsafe_allow_html=True)
                # st.plotly_chart(create_sparkline(copy_df["PM2.5"].resample('1d').mean()[-90:], color), use_container_width=True)

            

            with col1:
                start_value = copy_df[copy_df.index.year.isin([start_year])]['PM2.5'].min()
                end_value = copy_df[copy_df.index.year.isin([end_year])]['PM2.5'].min()
                kpi_card("Min PM2.5", min_pm25, "ug/m3", "green", start_value, end_value)

            with col2:
                start_value = copy_df[copy_df.index.year.isin([start_year])]['PM2.5'].mean()
                end_value = copy_df[copy_df.index.year.isin([end_year])]['PM2.5'].mean()
                kpi_card("Mean PM2.5", mean_pm25, "ug/m3", "blue", start_value, end_value)

            with col3:
                start_value = copy_df[copy_df.index.year.isin([start_year])]['PM2.5'].max()
                end_value = copy_df[copy_df.index.year.isin([end_year])]['PM2.5'].max()
                kpi_card("Max PM2.5", max_pm25, "", "red", start_value, end_value)
            




            ##################### new section
            st.write('### Time Series Chart')
            scatter = go.Scatter(x=copy_df.index, y=copy_df['PM2.5'], mode='markers')
            fig = go.Figure()
            fig.add_traces(scatter)
            st.plotly_chart(fig)





            ##################### new section
            st.write("### PM2.5 Stripes")
            stripes_df = df.copy()
            selected_city2 = st.selectbox("Which city would like to analyze?", options=list(stripes_df['City'].unique()))   
            stripes_df = stripes_df[stripes_df['City'] == selected_city2]
            stripes_df['day_of_year'] = stripes_df.index.dayofyear
            stripes_df['year'] = stripes_df.index.year
            df_grouped = stripes_df.groupby(['year', 'day_of_year'])['PM2.5'].mean().reset_index()
            pm2_5_matrix = df_grouped.pivot(index='year', columns='day_of_year', values='PM2.5')
            
            # Define PM2.5 breakpoints and corresponding colors
            breakpoints = [0, 12, 35.4, 55.4, 150.4, 250.4, 1000]
            colors = ['#A3D8FF', '#FDCB82', '#F89B42', '#F45C5C', '#D34F94', '#7A4D93', '#FF0066']
            categories = ["Good", "Moderate", "Unhealthy for Sensitive Groups", "Unhealthy", "Very Unhealthy", "Hazardous", "Hazardous"]

            # Create colormap and normalizer
            cmap = ListedColormap(colors)
            norm = BoundaryNorm(breakpoints, cmap.N)

            fig, ax = plt.subplots(figsize=(30, pm2_5_matrix.index.nunique()*3))
            cax = ax.imshow(pm2_5_matrix, aspect='auto', cmap=cmap, norm=norm)

            # **Calculate midpoints for labels to align with color segments**
            midpoints = [(breakpoints[i] + breakpoints[i+1]) / 2 for i in range(len(categories) - 1)]
            
            ax.set_yticks(np.arange(len(pm2_5_matrix.index)))
            ax.set_yticklabels(pm2_5_matrix.index, color='white', fontsize=38)
            ax.tick_params(axis='y', which='major', pad=40)
            
            # **Set X-axis labels (Months)**
            month_days = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]  # Approx. start of each month
            month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            ax.set_xticks(month_days)
            ax.set_xticklabels(month_labels, color='white', fontsize=14)

            # **Remove extra labels**
            ax.set_xlabel("")
            ax.set_ylabel("")

            # Add colorbar
            cbar = fig.colorbar(cax, boundaries=breakpoints, orientation='horizontal', pad=0.05, aspect=45)
            cbar.set_ticks(midpoints)
            cbar.set_ticklabels(categories[:-1], fontsize=16)
            cbar.ax.tick_params(axis='x', colors='white', labelsize=16, length=0, pad=10)
            
            fig.patch.set_alpha(0)
            ax.set_facecolor("none")
            ax.set_frame_on(False)

            # cbar = fig.colorbar(cax, orientation='horizontal', pad=0.1)
            # cbar.set_label("PM2.5 Levels", color='white')
            # cbar.ax.xaxis.set_tick_params(color='white')
            # plt.setp(cbar.ax.xaxis.get_ticklabels(), color='white')
            
            st.pyplot(fig)



            ##################### new section
            st.header('Comparative Analysis', divider='gray')
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
                    city_trend = px.line(city_avg_pm25, x=city_avg_pm25.index, y=selected_cities)
                else:
                    city_avg_pm25 = city_avg_pm25.resample('ys').mean().sort_index()
                    city_avg_pm25.index = city_avg_pm25.index.year  
                    city_trends = px.bar(city_avg_pm25, x=city_avg_pm25.index, y=selected_cities, barmode="group")
                
                st.plotly_chart(city_trends)
            
            else:
                st.write("###### Need more than 1 city for comparison!")
