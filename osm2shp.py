#!/usr/bin/env python
# python

# REQUIRED BUILT-IN MODULES
import overpy
import fiona
import pyproj
import sys

api = overpy.Overpass()

####################################################
# Module to extract Building OpenStreetMapData     #
# and write it into 'shp' files                    #
# ** if height of the building is not available,   #
#    default height is 5m                          #
# ** OpenStreetmap Data is automatically projected #
#    into UTM ZONE 31 Coordinate # System          #
####################################################


def apiquery(query_str):
    '''
    query_str = string used by the overpassAPI to read OSM files

    query_str must follow the format provided. See 'https://wiki.openstreetmap.org/wiki/Overpass_API/Language_Guide'

    e.g.

    """
    (node["building"](52.72, 4.69,52.73,4.70);
    way["building"](52.72, 4.69,52.73,4.70);
    relation["building"](52.72, 4.69,52.73,4.70););
    (._;>;);
    out body;
    """

    way = the OSM component (either node, way, or relative)
    (52.72, 4.69,52.73,4.70) = bounding box in (south, west, north, east) GPS coordinates
    out body; = used to close the query
    '''
    result = api.query(query_str)

    return result


def write_shape(apiresult, shp_name):
    '''
    apiresult = returned object from doing an inquiry using the overpass API
    shp_name = name of the shapefile. Do NOT INCLUDE '.shp' extension (e.g. 'foo').
    '''
    schema = {'geometry': 'Polygon',
              'properties': {'OGID': 'str:17', 'GID': 'str:24', 'EGID': 'int:9',
                             'ART': 'str:20', 'STATUS': 'str:20',
                             'REGION': 'str:10', 'H0': 'float:5.1',
                             'H1': 'float:5.1', 'H2': 'float:5.1',
                             'HRELMIN': 'float:5.1', 'HRELMAX': 'float:5.1'}
              }
    driver = 'ESRI Shapefile'

    crs = {'datum': 'WGS84', 'ellps': 'WGS84',
           'proj': 'utm', 'units': 'm', 'zone': 31}

    proj = '+proj=utm +zone=31 +ellps=WGS84 +datum=WGS84 +units=m +nodefs'

    shapeout = str(shp_name) + '.shp'

    with fiona.open(shapeout, 'w', crs=crs, driver=driver, schema=schema) as output:
        for way in apiresult.ways:
            for node in way.nodes:
                x, y = gps2proj(
                    float(node.lon), float(node.lat), proj=proj)
                build = {'type': 'Polygon', 'coordinates': [[
                    (x, y) for node in way.nodes]]}

            prop = {'OGID': way.tags.get("ogid"),
                    'GID': way.tags.get("gid"),
                    'EGID': way.tags.get("egid"),
                    'ART': way.tags.get("art"),
                    'STATUS': way.tags.get("status"),
                    'REGION': way.tags.get("region"),
                    'H0': way.tags.get("h0"),
                    'H1': way.tags.get("h1"),
                    'H2': way.tags.get("h2"),
                    "HRELMIN": way.tags.get("height", float(5.0)),
                    'HRELMAX': way.tags.get("height", float(5.0))}

            output.write({'geometry': build, 'properties': prop})


def gps2proj(lon, lat, proj, inverse=False):
    '''
    x: band 0 from APEX geo location
    y: band 1 from APEX geo location

    proj: proj4 description (e.g. from: http://spatialreference.org)

    Examples for proj:
        CH1903 (Swiss Coordinate System) = '+proj=somerc +lat_0=46.95240555555556 +lon_0=7.439583333333333 +k_0=1 +x_0=600000 +y_0=200000 +ellps=bessel +towgs84=674.374,15.056,405.346,0,0,0,0 +units=m +no_defs'
        Switzerland: "SWISS LV03"
        Rotterdam:   "+proj=utm +zone=31 +ellps=WGS84 +datum=WGS84 +units=m +nodefs"
    '''
    p = pyproj.Proj(proj)
    x, y = p(lon, lat, inverse=inverse)

    return x, y


def main(query_str, shp_name):
    api_result = apiquery(query_str)
    write_shape(api_result, shp_name)


if __name__ == '__main__':
    query_str = sys.argv[1]
    shp_name = sys.argv[2]

    main(query_str, shp_name)
