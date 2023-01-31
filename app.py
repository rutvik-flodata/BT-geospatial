from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    import pandas as pd
    import geopandas as gpd
    from random import randint
    import numpy as np
    import leafmap.foliumap as leafmap
    from ipyleaflet import Map, GeoJSON,GeoData
    from ipywidgets import VBox, Dropdown,HTML
    import json
    import re
    import folium
    gdf = gpd.read_file("New York_1.shp")
    gdf['zip_code'] =gdf['zip_code'].astype(int)
    df = pd.read_excel("final_subzone_nyc.xlsx",sheet_name="Sheet1")
    df = df[['zip','zone','sub_zone']]
    df.rename({'zip':'zip_code'},inplace=True,axis=1)
    gdf = gdf.merge(df, on='zip_code', how='left')
    gdf = gpd.GeoDataFrame(gdf)
    # Group by a column 'col'
    grouped = gdf.groupby("zone")

    # Find the union of all polygons within each group
    unionized = grouped.apply(lambda x: x.unary_union)
    gdf2 =gpd.GeoDataFrame(unionized,columns=['geometry']).reset_index()
    gdf2.crs = {'init': 'epsg:4326'}

    options=["All Zone"]
    for zone in  gdf2['zone']:
        options.append("zone-"+str(zone))
    dropdown = Dropdown(options=options)
    gdf["total_subzone"] = gdf['zone'].map(gdf.groupby("zone")["sub_zone"].count().to_dict())
    np.random.seed(12)
    color = []
    n = len(gdf['zone'].unique())
    count=0
    while count<n:
        new_color = '#%06X' % randint(0, 0xFFFFFF)
        if new_color not in color:
            color.append(new_color)
            count=count+1
        else:
            pass
        max_total_subzone = gdf['total_subzone'].max()
        
    subzone_count = 0
    color_new= []
    while subzone_count<max_total_subzone:
        new_color = '#%06X' % randint(0, 0xFFFFFF)
        if new_color not in color:
            color_new.append(new_color)
            subzone_count=subzone_count+1
        else:
            pass
    def style_func(data):
        index_no = data['properties']['zone']
        style= {
                "color": "black",
                "weight": 1,
                "opacity": 1,
                "fill": True,
                "fillOpacity": 1.0,
                "fillColor": color[index_no],
            }
        return style

    def style_func2(feature):
        index_no = feature['properties']['sub_zone']
        style = {
            "color": "black",
                "weight": 2.5,
                "opacity": 1,
                "fill": True,
                "fillOpacity":1,
                "fillColor": color_new[index_no-1],
        }
        return style
    layers = []
    def update_data(change):
        # get selected option
        selected_option = dropdown.value
        if selected_option!="All Zone":
            match = re.search(r"\d+", selected_option)
            zone = int(match.group())
            bounds  = gdf2['geometry'][zone].bounds
            temp = json.loads(gdf[gdf["zone"]==zone].to_json())
            for layer in layers:
                if isinstance(layer,folium.features.GeoJson):
                    layers.remove(layer)
                    m.add_gdf(gdf2,layer_name='Zoning',style_function=style_func)
            layer  = folium.GeoJson(temp,style_function=style_func2,tooltip=folium.features.GeoJsonTooltip(fields=["zone","sub_zone"], aliases=["zone","sub_zone"]))
            m.add_layer(layer)
            lat_long = gdf2['geometry'].iloc[zone].centroid
            m.set_center(lat_long.x,lat_long.y)
            m.zoom = 10
            layers.append(layer)
            map_widget.value = m._repr_html_()
            vbox = VBox([dropdown,map_widget])
        else:
            m.add_gdf(gdf2,layer_name='Zoning',style_function=style_func)
            map_widget.value = m._repr_html_()
            vbox = VBox([dropdown,map_widget])
    m = leafmap.Map(center=(50, -100), zoom=4)
    m.add_gdf(gdf2,layer_name='Zoning',style_function=style_func)
    dropdown.observe(update_data, 'value')
    map_widget = HTML(m._repr_html_())
    vbox = VBox([dropdown,map_widget])
    vbox
    return m._repr_html_()

if __name__ == "__main__":
    app.run()