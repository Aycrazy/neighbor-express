#%%
import pandas as pd
import os
import re
from datetime import timedelta
import plotly.express as px
import chart_studio.plotly as py
import plotly.graph_objects as go
import numpy as np
from shapely.geometry import LineString, MultiLineString
from plotly.express import choropleth_mapbox
import folium
from airtable import Airtable
import geopandas as gpd

#%%
#Changing drive to where control file/parameters file is held
#os.chdir(r'')


#In file I have my base id, API identifier, and API identifier for google maps API


parameters = pd.read_excel('Parameters.xlsx')

base = str(parameters['Base'].loc[0])

api = str(parameters['API'].loc[0])

#%%

def air(table):


    #Connecting to Airtable API with base key, api key, and table name specified when function called

    airtable = Airtable(base_key=base,api_key=api, table_name=table)


    #Could pull all records in this table

    records = airtable.get_all()


    #Otherwise, specific view

    # records = airtable.get_all(view = 'All submissions')


    #Make table from dictionary/records - Doing this to export tables

    df = pd.DataFrame.from_records((r['fields'] for r in records))


    #Create list of fields to drop for clean up


    dropping_list = []


    #Removing some columns I don't need

    for columns in df.columns:
        columns2 = str(columns)
        if columns2.find('don\'t use') > -1 or columns2.find('do not touch') > -1 or columns2.find('old') > -1 or columns2.find('older') > -1:
            dropping_list.append(columns2)



    #Cleaning up columns. Dropping columns from list and name clean up to sort later


    df.drop(dropping_list,inplace=True,axis=1)

    df.columns = df.columns.str.replace('"', '')
    df.columns = df.columns.str.replace('(', '')
    df.columns = df.columns.str.replace(')', '')
    df.columns = df.columns.str.replace('#', 'Number ')



    #Sort column names alphabetically

    df = df.reindex(sorted(df.columns), axis=1)



    #Sort by Agency Name

    try:
        df = df.sort_values(by='AgencyName')

    except:
        pass



    return df



#Calling function here in loop in case I want to pull multiple tables at once.

#%%
for tables in parameters['Tables']:
    if str(tables) != 'nan':
        print(tables)
        x = air(tables)
        export = x.to_csv(str(tables).replace(' ','_') + '.csv',index=False)
#%%

x.rename(columns={c:re.sub(" |-",'_',c).lower() for c in x.columns}, inplace=True)

# %%
perc_na = x[pd.isna(x.delivery_zip_code)].shape[0]/x.shape[0]

zip_counts = x[['agencyname','delivery_zip_code']].groupby('delivery_zip_code').count().reset_index().rename(columns={'agencyname':'freq'}).sort_values('freq', ascending = False)

agency_delivery_counts = x[['agencyname','box_numbers']].groupby('agencyname').count().reset_index().rename(columns={'box_numbers':'freq'}).sort_values('freq', ascending = False)

#masks_total_boxes_times_700
zip_units = x[['delivery_zip_code','masks_total_boxes_times_700']].groupby('delivery_zip_code').sum().reset_index().rename(columns={'masks_total_boxes_times_700':'total'}).sort_values('total', ascending = False)

x['conversion_time'] = pd.to_timedelta(pd.to_datetime(x.delivery_date).apply(lambda x: x.date())-pd.to_datetime(x.submission_date).apply(lambda x: x.date()))

average_delivery_time = x['conversion_time'].mean()

zip_delivery_timedelta = x[pd.notna(x.conversion_time)][['delivery_zip_code','conversion_time']].groupby('delivery_zip_code').apply(
    lambda x: x['conversion_time'].astype('timedelta64[s]').mean()).reset_index().rename(columns={0:'timedelta_avg'})

#average length in days to zip -- wonder how accurate submission time as delivery is
zip_delivery_timedelta['days'] = zip_delivery_timedelta['timedelta_avg'].apply(lambda x: round(x/86400,2))


fig_agency_bar_top5 = px.bar(agency_delivery_counts.sort_values('freq',ascending=False).head(), x='agencyname',y='freq')

fig_agency_bar_top5.show()

## Zip Units Bar

data = go.Bar( x=zip_units.sort_values('total', ascending=False).head().zips, y=zip_units.sort_values('total', ascending=False).head().total)

layout = go.Layout(xaxis=dict(type='category'))

fig_zip_units_top5  = go.Figure(data=data, layout=layout)

fig_zip_units_top5.show()

#%%
### Map these things next
zips = gpd.read_file('../zcta_zips/Zip_Code_Tabulation_Areas__ZCTA_.shp')


#zips['delivery_zip_code'] = zips.ZCTA5CE10

zips['delivery_zip_code'] = zips.ZIPCODE

#zips.to_file("zips.geojson", driver='GeoJSON')

zips = zips.loc[1:zips.shape[0]-2]

zips.ZIPCODE = zips.ZIPCODE.astype(int)



milwaukee_coords = [43.03, -87.88]
mke_zips = f'zips.geojson'
#Create the map
#my_map = folium.Map(location = milwaukee_coords, zoom_start = 11)

#Display the map

##function
import numpy as np

from shapely.geometry import LineString, MultiLineString

#adapted from https://plotly.com/~empet/15238/tips-to-get-a-right-geojson-dict-to-defi/#/
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
###
#%%



zips_temp = zips.set_index('ZIPCODE')

zips_geo = shapefile_to_geojson(zips_temp, index_list = zips_temp.index)
#%%

fig_units= choropleth_mapbox(data_frame = zip_counts,
                geojson =zips_geo,
                  locations='delivery_zip_code',
                  #animation_frame = 'datetime',
                  color='freq',
                  color_continuous_scale = px.colors.sequential.Viridis,
                  #range_color = [0,1400],
                  featureidkey='features.ZIPCODE',
                  zoom =10,
                  opacity = .6,
                  center = {"lat": milwaukee_coords[0], "lon": milwaukee_coords[1]},
                  mapbox_style = "carto-positron")
##


# %%
fig_units.show()
# %%

fig_deliveries= choropleth_mapbox(data_frame = zip_counts,
                geojson =zips_geo,
                  locations='delivery_zip_code',
                  #animation_frame = 'datetime',
                  color='total',
                  color_continuous_scale = px.colors.sequential.Viridis,
                  #range_color = [0,1400],
                  featureidkey='features.ZIPCODE',
                  zoom =10,
                  opacity = .6,
                  center = {"lat": milwaukee_coords[0], "lon": milwaukee_coords[1]},
                  mapbox_style = "carto-positron")

fig_deliveries.show()

#%%
fig_delivery_time= choropleth_mapbox(data_frame = zip_delivery_timedelta,
                geojson =zips_geo,
                  locations='delivery_zip_code',
                  #animation_frame = 'datetime',
                  color='days',
                  color_continuous_scale = px.colors.sequential.Viridis,
                  #range_color = [0,1400],
                  labels={'days':'Time in Days'},
                  featureidkey='features.ZIPCODE',
                  zoom =10,
                  opacity = .6,
                  center = {"lat": milwaukee_coords[0], "lon": milwaukee_coords[1]},
                  mapbox_style = "carto-positron")


# %%
