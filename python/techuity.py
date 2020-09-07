#%%
import pandas as pd 
import geopandas as gpd 

import re 
import os
#import plotly
import plotly.express as px
import chart_studio.plotly as py
import plotly.graph_objects as go
import plotly.offline
import numpy as np
from shapely.geometry import LineString, MultiLineString
from plotly.express import choropleth_mapbox
import folium
#%%

int_df = pd.read_csv('internet_clean.csv')

meta_int_df = pd.read_csv('../census/acs5yr_internet_clean_meta.csv')

race_df = pd.read_excel('../census/Race_clean.xlsx')

zips = gpd.read_file('zips.geojson')

zips = zips.iloc[1:zips.shape[0]-1]

zips.ZIPCODE = zips.ZIPCODE.astype(int)

milwaukee_coords = [43.03, -87.88]

#%%

def shapefile_to_geojson(gdf, index_list, level = 1, tolerance=0.025): 
    # gdf - geopandas dataframe containing the geometry column and values to be mapped to a colorscale
    # index_list - a sublist of list(gdf.index)  or gdf.index  for all data
    # level - int that gives the level in the shapefile
    # tolerance - float parameter to set the Polygon/MultiPolygon degree of simplification
    
    # returns a geojson type dict 
   
    geo_names = index_list
    geojson = {'type': 'FeatureCollection', 'features': []}
    for idx,index in enumerate(index_list):
        #print(gdf.index)
        #print(index)
        geo = gdf['geometry'].loc[index]
        
        #print(geo.boundary)
        if isinstance(geo.boundary, LineString):
            gtype = 'Polygon'
            bcoords = np.dstack(geo.boundary.coords.xy).tolist()
    
        elif isinstance(geo.boundary, MultiLineString):
            gtype = 'MultiPolygon'
            bcoords = []
            for b in geo.boundary:
                x, y = b.coords.xy
                coords = np.dstack((x,y)).tolist() 
                bcoords.append(coords) 
#         else: pass
        
        
       
        feature = {'type': 'Feature', 
                   'id' : index,
                   'properties': {'name': geo_names[idx]},
                   'geometry': {'type': gtype,
                                'coordinates': bcoords},
                    }
                                
        geojson['features'].append(feature)
    return geojson

#%%
zips_temp = zips.set_index('ZIPCODE')

zips_geo = shapefile_to_geojson(zips_temp, index_list = zips_temp.index)
#%%
int_x_race_df = pd.merge(int_df, race_df, left_on ='zcta' , right_on = 'ZCTA')

int_x_race_df['percent_bb'] = (int_x_race_df['S2801_C01_014E']/int_x_race_df['S2801_C01_001E'])*100

int_x_race_df['ZIPCODE'] = int_x_race_df['zcta']
#%%

#percent broadband access by household plotly 


fig_bb= choropleth_mapbox(data_frame = int_x_race_df,
                geojson =zips_geo,
                  locations='zcta',
                  #animation_frame = 'datetime',
                  color='percent_bb',
                  color_continuous_scale = px.colors.sequential.Viridis,
                  #range_color = [0,1400],
                  featureidkey='feature.ZIPCODE',
                  zoom =10,
                  opacity = .6,
                  labels={'percent_bb':'Broadband Access (%)'},
                  center = {"lat": milwaukee_coords[0], "lon": milwaukee_coords[1]},
                  mapbox_style = "carto-positron")

# %%
fig_bb

# %%

#S2801_C01_012E internet subscription

#percent internet access by household plotly 

int_x_race_df['percent_int'] = (int_x_race_df['S2801_C01_012E']/int_x_race_df['S2801_C01_001E'])*100

fig_int= choropleth_mapbox(data_frame = int_x_race_df,
                geojson =zips_geo,
                  locations='zcta',
                  #animation_frame = 'datetime',
                  color='percent_int',
                  color_continuous_scale = px.colors.sequential.Viridis,
                  #range_color = [0,1400],
                  featureidkey='feature.ZIPCODE',
                  zoom =10,
                  opacity = .6,
                  labels={'percent_int':'Internet Access (%)'},
                  center = {"lat": milwaukee_coords[0], "lon": milwaukee_coords[1]},
                  mapbox_style = "carto-positron")

# %%
fig_int

# %%

#% internet access by household folium 

m1 = folium.Map(
    location=milwaukee_coords,
    zoom_start=10
)

folium.Choropleth(
    geo_data=zips,
    name='choropleth',
    data=int_x_race_df,
    columns=['ZIPCODE','percent_int'],
    key_on='feature.properties.ZIPCODE',
    fill_color='YlGn',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Internet Access (%)').add_to(m1)

folium.LayerControl().add_to(m1)

m1

# %%

#