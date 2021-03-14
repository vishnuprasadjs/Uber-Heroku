import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
import folium 
from streamlit_folium import folium_static
import webbrowser
from folium import Marker
from folium.plugins import MarkerCluster
import requests
import pickle
import datetime
import os


from dotenv import load_dotenv
load_dotenv()

ORS_API_KEY = os.getenv('ORS_API_KEY')

pkl_filename = "Est_time_pred.pkl"
with open(pkl_filename, 'rb') as file:
    regressor = pickle.load(file)
    
categories_to_hour = {
    1: [0, 6],
    2: [7, 9],
    3: [10, 15],
    4: [16, 18],
    5: [19, 23]
}

def get_time_period(hour):
    for category, (start_hour, end_hour) in categories_to_hour.items():
        if hour >= start_hour and hour <= end_hour:
            return category
    
def get_driving_route(source_coordinates, dest_coordinates):
    parameters = {
    'api_key': ORS_API_KEY,
    'start' : '{},{}'.format(source_coordinates[1], source_coordinates[0]),
    'end' : '{},{}'.format(dest_coordinates[1], dest_coordinates[0])
    }

    response = requests.get(
        'https://api.openrouteservice.org/v2/directions/driving-car', params=parameters)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print('Request failed.')
        return -9999
    

def get_route(source, destination, date,departure_time,holiday):
    
    day = date.day
    time_period = get_time_period(departure_time.hour)
    dow = date.weekday()
    driving_data = get_driving_route(source, destination)
    summary = driving_data['features'][0]['properties']['summary']
    distance = summary['distance']
    input = [day, time_period, dow, source[1], source[0], destination[1], destination[0], distance, holiday]
    travel_time = round(regressor.predict([input])[0]/60)
    ors_travel_time = round(summary['duration']/60)
    route= driving_data['features'][0]['geometry']['coordinates']
    
    def swap(coord):
        coord[0],coord[1]=coord[1],coord[0]
        return coord

    route=list(map(swap, route))
    m = folium.Map(location=[(source[0] + destination[0])/2,(source[1] + destination[1])/2], zoom_start=13)
    
    tooltip = 'Model predicted time = {} mins, \
        Default travel time = {} mins'.format(travel_time, ors_travel_time)
    folium.PolyLine(
        route,
        weight=8,
        color='blue',
        opacity=0.6,
        tooltip=tooltip
    ).add_to(m)

    folium.Marker(
        location=(source[0],source[1]),
        icon=folium.Icon(icon='play',color='green')
    ).add_to(m)

    folium.Marker(
        location=(destination[0],destination[1]),
        icon=folium.Icon(icon='stop',color='red')
    ).add_to(m)
    folium_static(m)




## Adding a background to streamlit page
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
        


def run():
    date = st.sidebar.date_input('Select date', datetime.date(2020,1,1))
    time = st.sidebar.time_input('Select time', datetime.time(0,00))
    st.write('Date of Journey:',date)
    st.write('Time:',time)
    coordinate_list=['Select',(12.946538, 77.579975),(13.04438892,77.60185844),(12.95275348,77.72982887)]
    source = st.sidebar.selectbox('Choose the source',coordinate_list)
    st.write('You selected source:', source)
    destination = st.sidebar.selectbox('Choose the destination',coordinate_list)
    st.write('You selected destination:', destination) 
    url='https://www.google.com/maps/dir/{},{}/{},{}'.format(source[0],source[1],destination[0],destination[1])

    holiday_check = st.sidebar.checkbox("Holiday")
    if holiday_check:
        holiday=1
    else:
        holiday=0
    departure_time = time
    col1,col2=st.sidebar.beta_columns(2)
    if col1.button('Navigate'):
        get_route(source, destination, date,departure_time,holiday)
    if col2.button("Google Map"):
        webbrowser.open(url)
     


if __name__ == "__main__":
    # front end elements of the web page 
    html_temp = """ 
    <div style ="background-color:yellow;padding:13px"> 
    <h1 style ="color:black;text-align:center;">Travel Time Predictior app</h1> 
    <h2 style ="color:black;text-align:center;">Bangalore City</h2> 
    </div> 
    """
      
    # display the front end aspect
    st.markdown(html_temp, unsafe_allow_html = True) 
    run()

