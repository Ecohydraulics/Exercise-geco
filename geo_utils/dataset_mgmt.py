from raster_mgmt import *
from shp_mgmt import *
gdal.UseExceptions()


def coords2offset(geo_transform, x_coord, y_coord):
    """
    Returns x-y pixel offset (inverse of offset2coords function)
    :param geo_transform: osgeo.gdal.Dataset.GetGeoTransform() object
    :param x_coord: FLOAT of x-coordinate
    :param y_coord: FLOAT of y-coordinate
    :return: offset_x, offset_y (both integer of pixel numbers)
    """
    try:
        origin_x = geo_transform[0]
        origin_y = geo_transform[3]
        pixel_width = geo_transform[1]
        pixel_height = geo_transform[5]
    except IndexError:
        print("ERROR: Invalid geo_transform object (%s)." % str(geo_transform))
        return None

    try:
        offset_x = int((x_coord - origin_x) / pixel_width)
        offset_y = int((y_coord - origin_y) / pixel_height)
    except ValueError:
        print("ERROR: geo_transform tuple contains non-numeric data: %s" % str(geo_transform))
        return None
    return offset_x, offset_y


def get_layer(dataset, band_number=1):
    """
    Get a layer=band (RasterDataSet) or layer=ogr.Dataset.Layer() of any dataset
    :param dataset: osgeo.gdal.Dataset or osgeo.ogr.DataSource
    :param band_number: ONLY FOR RASTERS - INT of the raster band number to open (default: 1)
    :output: DICT {GEO-TYPE: if raster: raster_band, if vector: GetLayer(), else: None}
    """
    if verify_dataset(dataset) == "raster":
        return {"type": "raster", "layer": dataset.GetRasterBand(band_number)}
    if verify_dataset(dataset) == "vector":
        return {"type": "vector", "layer":  dataset.GetLayer()}
    return {"type": "None", "layer": None}


def offset2coords(geo_transform, offset_x, offset_y):
    """
    Returns x-y coordinates from pixel offset (inverse of coords2offset function)
    :param geo_transform: osgeo.gdal.Dataset.GetGeoTransform() object
    :param offset_x: integer of x pixel numbers
    :param offset_y: integer of y pixel numbers
    :return: x_coord, y_coord (FLOATs of x-y-coordinates)
    """
    try:
        origin_x = geo_transform[0]
        origin_y = geo_transform[3]
        pixel_width = geo_transform[1]
        pixel_height = geo_transform[5]
    except IndexError:
        print("ERROR: Invalid geo_transform object (%s)." % str(geo_transform))
        return None

    try:
        coord_x = origin_x + pixel_width * (offset_x + 0.5)
        coord_y = origin_y + pixel_height * (offset_y + 0.5)
    except ValueError:
        print("ERROR: geo_transform tuple contains non-numeric data: %s" % str(geo_transform))
        return None
    return coord_x, coord_y


def verify_dataset(dataset):
    """
    Verify if a dataset contains raster or vector data
    :param dataset: osgeo.gdal.Dataset or osgeo.ogr.DataSource
    :return: String (either "mixed", "raster", or "vector")
    """
    # Check the contents of an osgeo.gdal.Dataset
    try:
        if dataset.RasterCount > 0 and dataset.GetLayerCount() > 0:
            return "mixed"
    except AttributeError:
        pass

    try:
        if dataset.RasterCount > 0:
            return "raster"
    except AttributeError:
        pass

    try:
        if dataset.GetLayerCount() > 0:
            return "vector"
        else:
            return "empty"
    except AttributeError:
        print("ERROR: %s is not an osgeo.gdal.Dataset object." % str(dataset))
        return None
