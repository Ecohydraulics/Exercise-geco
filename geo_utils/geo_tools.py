from srs_mgmt import *
import itertools
gdal.UseExceptions()


def float2int(raster_file_name, band_number=1):
    """
    :param raster_file_name: STR of target file name, including directory; must end on ".tif"
    :param band_number: INT of the raster band number to open (default: 1)
    :output: new_raster_file_name (STR)
    """
    raster, array, geo_transform = raster2array(raster_file_name, band_number=band_number)
    try:
        array = array.astype(int)
    except ValueError:
        print("Error: Invalid raster pixel values.")
        return raster_file_name
    new_name = raster_file_name.split(".tif")[0] + "_int.tif"

    # get source coordinate system and exit function if not possible
    src_srs = get_srs(raster)
    if not src_srs:
        # ensure consistency
        return raster_file_name

    # create integer raster
    print(" * info: creating integer raster to Polygonize:\n   >> %s" % new_name)
    create_raster(new_name, array, epsg=int(src_srs.GetAuthorityCode(None)),
                  rdtype=gdal.GDT_Int32, geo_info=geo_transform)
    return new_name


def raster2line(raster_file_name, out_shp_fn, pixel_value):
    """
    Convert a raster to a line shapefile, where pixel_value determines line start and end points
    :param raster_file_name: STR of input raster file name, including directory; must end on ".tif"
    :param out_shp_fn: STR of target shapefile name, including directory; must end on ".shp"
    :param pixel_value: INT/FLOAT of a pixel value
    :return: None (writes new shapefile).
    """

    # calculate max. distance between points
    # ensures correct neighbourhoods for start and end pts of lines
    raster, array, geo_transform = raster2array(raster_file_name)
    pixel_width = geo_transform[1]
    max_distance = np.ceil(np.sqrt(2 * pixel_width**2))

    # extract pixels with the user-defined pixel value from the raster array
    trajectory = np.where(array == pixel_value)
    if np.count_nonzero(trajectory) is 0:
        print("Error: The defined pixel_value (%s) does not occur in the raster band." % str(pixel_value))
        return None

    # convert pixel offset to coordinates and append to nested list of points
    points = []
    count = 0
    for offset_y in trajectory[0]:
        offset_x = trajectory[1][count]
        points.append(offset2coords(geo_transform, offset_x, offset_y))
        count += 1

    # create multiline (write points dictionary to line geometry (wkbMultiLineString)
    multi_line = ogr.Geometry(ogr.wkbMultiLineString)
    for i in itertools.combinations(points, 2):
        point1 = ogr.Geometry(ogr.wkbPoint)
        point1.AddPoint(i[0][0], i[0][1])
        point2 = ogr.Geometry(ogr.wkbPoint)
        point2.AddPoint(i[1][0], i[1][1])

        distance = point1.Distance(point2)
        if distance < max_distance:
            line = ogr.Geometry(ogr.wkbLineString)
            line.AddPoint(i[0][0], i[0][1])
            line.AddPoint(i[1][0], i[1][1])
            multi_line.AddGeometry(line)

    # write multiline (wkbMultiLineString2shp) to shapefile
    new_shp = create_shp(out_shp_fn, layer_name="raster_pts", layer_type="line")
    lyr = new_shp.GetLayer()
    feature_def = lyr.GetLayerDefn()
    new_line_feat = ogr.Feature(feature_def)
    new_line_feat.SetGeometry(multi_line)
    lyr.CreateFeature(new_line_feat)

    # create projection file
    srs = get_srs(raster)
    make_prj(out_shp_fn, int(srs.GetAuthorityCode(None)))
    print(" * success (raster2line): wrote %s" % str(out_shp_fn))


def raster2polygon(file_name, out_shp_fn, band_number=1, field_name="values",
                   add_area=False):
    """
    Convert a raster to polygon
    :param file_name: STR of target file name, including directory; must end on ".tif"
    :param out_shp_fn: STR of a shapefile name (with directory e.g., "C:/temp/poly.shp")
    :param band_number: INT of the raster band number to open (default: 1)
    :param field_name: STR of the field where raster pixel values will be stored (default: "values")
    :param add_area: BOOL (if True, an "area" field will be added, where the area
                                in the shapefiles unit system is calculated - default: False)
    :return: osgeo.ogr.DataSource
    """
    # ensure that the input raster contains integer values only and open the input raster
    file_name = float2int(file_name)
    raster, raster_band = open_raster(file_name, band_number=band_number)

    # create new shapefile with the create_shp function
    new_shp = create_shp(out_shp_fn, layer_name="raster_data", layer_type="polygon")
    dst_layer = new_shp.GetLayer()

    # create new field to define values
    new_field = ogr.FieldDefn(field_name, ogr.OFTInteger)
    dst_layer.CreateField(new_field)

    # Polygonize(band, hMaskBand[optional]=None, destination lyr, field ID, papszOptions=[], callback=None)
    gdal.Polygonize(raster_band, None, dst_layer, 0, [], callback=None)

    # create projection file
    srs = get_srs(raster)
    make_prj(out_shp_fn, int(srs.GetAuthorityCode(None)))
    print(" * success (Polygonize): wrote %s" % str(out_shp_fn))
    return new_shp


def rasterize(in_shp_file_name, out_raster_file_name, pixel_size=10, no_data_value=-9999,
              rdtype=gdal.GDT_Float32, **kwargs):
    """
    Converts any shapefile to a raster
    :param in_shp_file_name: STR of a shapefile name (with directory e.g., "C:/temp/poly.shp")
    :param out_raster_file_name: STR of target file name, including directory; must end on ".tif"
    :param pixel_size: INT of pixel size (default: 10)
    :param no_data_value: Numeric (INT/FLOAT) for no-data pixels (default: -9999)
    :param rdtype: gdal.GDALDataType raster data type - default=gdal.GDT_Float32 (32 bit floating point)
    :kwarg field_name: name of the shapefile's field with values to burn to the raster
    :return: produces the shapefile defined with in_shp_file_name
    """

    # open data source
    try:
        source_ds = ogr.Open(in_shp_file_name)
    except RuntimeError as e:
        print("Error: Could not open %s." % str(in_shp_file_name))
        return None
    source_lyr = source_ds.GetLayer()

    # read extent
    x_min, x_max, y_min, y_max = source_lyr.GetExtent()

    # get x and y resolution
    x_res = int((x_max - x_min) / pixel_size)
    y_res = int((y_max - y_min) / pixel_size)

    # create destination data source (GeoTIff raster)
    try:
        target_ds = gdal.GetDriverByName('GTiff').Create(out_raster_file_name, x_res, y_res, 1, eType=rdtype)
    except RuntimeError as e:
        print("Error: Could not create %s." % str(out_raster_file_name))
        return None
    target_ds.SetGeoTransform((x_min, pixel_size, 0, y_max, 0, -pixel_size))
    band = target_ds.GetRasterBand(1)
    band.Fill(no_data_value)
    band.SetNoDataValue(no_data_value)

    # get spatial reference system and assign to raster
    srs = get_srs(source_ds)
    try:
        srs.ImportFromEPSG(int(srs.GetAuthorityCode(None)))
    except RuntimeError as e:
        print(e)
        return None
    target_ds.SetProjection(srs.ExportToWkt())

    # RasterizeLayer(Dataset dataset, int bands, Layer layer, pfnTransformer=None, pTransformArg=None,
    # int burn_values=0, options=None, GDALProgressFunc callback=0, callback_data=None)
    try:
        if kwargs.get("field_name"):
            gdal.RasterizeLayer(target_ds, [1], source_lyr, None, None, burn_values=[0],
                                options=["ALL_TOUCHED=TRUE", "ATTRIBUTE=" + str(kwargs.get("field_name"))])
        else:
            gdal.RasterizeLayer(target_ds, [1], source_lyr, None, None, burn_values=[0],
                                options=["ALL_TOUCHED=TRUE"])
    except RuntimeError as e:
        print("Error: Could not rasterize (burn values from %s)." % str(in_shp_file_name))
        return None

    # release raster band
    band.FlushCache()

