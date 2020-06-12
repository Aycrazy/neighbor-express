#%%
import pandas as pd
from airtable import Airtable
import os
import re
from datetime import timedelta
import plotly.express as px
import chart_studio.plotly as py
import plotly.graph_objects as go
import folium
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
zip_delivery_timedelta['days'] = zip_delivery_timedelta['timedelta_avg'].apply(lambda x: timedelta(seconds=x))

fig_agency_bar_top5 = px.bar(agency_delivery_counts.sort_values('freq',ascending=False).head(), x='agencyname',y='freq')

fig_agency_bar_top5.show()

## Zip Units Bar

data = go.Bar( x=zip_units.sort_values('total', ascending=False).head().zips, y=zip_units.sort_values('total', ascending=False).head().total)

layout = go.Layout(xaxis=dict(type='category'))

fig_zip_units_top5  = go.Figure(data=data, layout=layout)

fig_zip_units_top5.show()

### Map these things next
zips = gpd.read_file('../zcta_zips/Zip_Code_Tabulation_Areas__ZCTA_.shp')

zips['delivery_zip_code'] = zips.ZIPCODE

zips.to_file("zips.geojson", driver='GeoJSON')

milwaukee_coords = [43.03, -87.88]
mke_zips = f'zips.geojson'
#Create the map
#my_map = folium.Map(location = milwaukee_coords, zoom_start = 11)

#Display the map

map_with_tiles = folium.Map(location = milwaukee_coords, tiles = 'Stamen Toner')

choropleth = folium.Choropleth(
    name='choropleth',
    geo_data=zip_units,
    data=mke_zips,
    columns=['delivery_zip_code','total'],
   #key_on="feature.properties.ZIPCODES",
    fill_color='YlGn',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Total Units'
).add_to(map_with_tiles)

choropleth.geojson.add_child(
    folium.features.GeoJsonTooltip(['delivery_zip_code','total'], labels=False)
)

#not appearing in vscode
map_with_tiles