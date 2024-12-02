import os
import json
import time
from functools import cache

import requests
import numpy as np
import pandas as pd

import folium
from folium.plugins import MarkerCluster
from folium import MacroElement

from flask import Flask, render_template, request

df = pd.read_csv("zillow.csv")

app = Flask(__name__)

@app.route('/')
def index():
    global df

    if os.path.exists('templates/property_map.html'):
        return render_template('property_map.html')
    else:
        df = df.dropna(subset=['longitude','latitude']) # Drop NA's for coordinates
        # Turn features to numerical features
        df['rentZestimate'] = pd.to_numeric(df['rentZestimate'], errors='coerce')
        df['zestimate'] = pd.to_numeric(df['zestimate'], errors='coerce')
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        # Craft additional features
        df['annual_rent'] = df['rentZestimate'] * 12
        df['gross_rental_yield'] = (df['annual_rent'] / df['zestimate']) * 100

        df['gross_rental_yield'] = df['gross_rental_yield'].replace([np.inf, -np.inf], np.nan) # Could be diveded by zero

        def get_marker_color(gross_yield, off_market):
            if off_market:
                return 'black'
            elif pd.isna(gross_yield):
                return 'gray'
            elif gross_yield < 5:
                return 'red'
            elif gross_yield <8:
                return 'orange'
            else:
                return 'green'
            
        map_center = [df['latitude'].mean(), df['longitude'].mean()] # Center map arroun average location

        m = folium.Map(location=map_center, zoom_start=12)

        marker_cluster = MarkerCluster().add_to(m)

        for idx, row in df.iterrows():
            price = row['price']
            address = row['address']
            bedrooms = row['bedrooms']
            bathrooms = row['bathrooms']
            living_area = row['livingArea']
            gross_yield = row['gross_rental_yield']
            zestimate = row['zestimate']
            rent_estimate = row['rentZestimate']
            property_url = row['url']
            zpid = row['zpid']

            if not pd.isna(price):
                price_formatted = f'${price:.2f}'
            else:
                price_formatted = 'N/A'

            if not pd.isna(zestimate):
                zestimate_formatted = f'${zestimate:.2f}'
            else:
                zestimate_formatted = 'N/A'
            
            if not pd.isna(rent_estimate):
                rent_estimate_formatted = f'${rent_estimate:.2f}'
            else:
                rent_estimate_formatted = 'N/A'
            
            if not pd.isna(gross_yield):
                gross_yield_formatted = f'%{gross_yield:.2f}'
            else:
                gross_yield_formatted = 'N/A'

            bedrooms = int(bedrooms) if not pd.isna(bedrooms) else 'N/A'
            bathrooms = int(bathrooms) if not pd.isna(bathrooms) else 'N/A'
            living_area = int(living_area) if not pd.isna(living_area) else 'N/A'

            address_dict = json.loads(address)
            street_address = address_dict['streetAddress']

            popup_text = f""" 
            <b>Address:</b> {street_address} <br>
            <b>Price:</b> {price_formatted} <br>
            <b>Bedrooms:</b> {bedrooms} <br>
            <b>Bathrooms:</b> {bathrooms} <br>
            <b>Living Area:</b> {living_area} <br>
            <b>Gross Rental Yield:</b> {gross_yield_formatted} <br>
            <b>Zestimate:</b> {zestimate_formatted} <br>
            <b>Rent Zestimate:</b> {rent_estimate_formatted} <br>
            <a href= "{property_url}" target="_blank">Zillow Link</a><br>
            <button id="button-{idx}" onclick="showLoadingAndRedirect({idx}, '{zpid}')">Show Price History</button>
            <div id="loading-{idx}" style="display: none;">
                <img src="https://upload.wikimedia.org/wikipedia/commons/a/a3/Lightness_rotate_36f_cw.gif?20110914212036" alt="loading.." width="50" height="50">
            </div>

            <script>
                function showLoadingAndRedirect(idx, zpid) {{
                    document.getElementById('button-' + idx).style.display = 'none;
                    document.getElementById('loading-' + idx).style.display = 'block';
                    window.location.href = 'http://localhost:5000/price_history/' + zpid;
                }}
            </script>
            """

            color = get_marker_color(row['gross_rental_yield'], row['isOffMarket'])

            folium.Marker(
                location= [row['latitude'], row['longitude']],
                popup= folium.Popup(folium.IFrame(popup_text, width=300, height=250)),
                icon = folium.Icon(color=color, icon='home',prefix='fa')
            ).add_to(marker_cluster)

        m.save('templates/property_map.html')
        return render_template('property_map.html')
            

if __name__ == '__main__':
    app.run(debug=True)

    