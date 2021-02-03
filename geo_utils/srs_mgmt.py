from .dataset_mgmt import *
import urllib


def get_esriwkt(epsg):
    """
    Get esriwkt-formatted spatial references with epsg code online
    Usage: get_esriwkt(4326)
    :param epsg: Int of epsg
    :output: str containing esriwkt (if error: default epsg=4326 is used)
    """
    try:
        with urllib.request.urlopen("http://spatialreference.org/ref/epsg/{0}/esriwkt/".format(epsg)) as response:
            return str(response.read()).strip("b").strip("'")
    except Exception:
        pass
    try:
        with urllib.request.urlopen(
                "http://spatialreference.org/ref/sr-org/epsg{0}-wgs84-web-mercator-auxiliary-sphere/esriwkt/".format(
                    epsg)) as response:
            return str(response.read()).strip("b").strip("'")
        # sr-org codes are available at "https://spatialreference.org/ref/sr-org/{0}/esriwkt/".format(epsg)
        # for example EPSG:3857 = SR-ORG:6864 -> https://spatialreference.org/ref/sr-org/6864/esriwkt/ = EPSG:3857
    except Exception as e:
        print("ERROR: Could not find epsg code on spatialreference.org. Returning default WKT(epsg=4326).")
        print(e)
        return 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295],UNIT["Meter",1]]'


def get_srs(dataset):
    """
    Get the spatial reference of any gdal.Dataset
    :param dataset: gdal.Dataset (shapefile or raster)
    :output: osr.SpatialReference
    """
    gdal.UseExceptions()

    if verify_dataset(dataset) == "raster":
        sr = osr.SpatialReference()
        sr.ImportFromWkt(dataset.GetProjection())
    else:
        try:
            sr = osr.SpatialReference(str(dataset.GetLayer().GetSpatialRef()))
        except AttributeError:
            print("ERROR: Invalid source data (%s)." % str(dataset))
            return None
    # auto-detect epsg
    try:
        auto_detect = sr.AutoIdentifyEPSG()
        if auto_detect is not 0:
            sr = sr.FindMatches()[0][0]  # Find matches returns list of tuple of SpatialReferences
            sr.AutoIdentifyEPSG()
    except TypeError:
        print("ERROR: Empty spatial reference.")
        return None
    # assign input SpatialReference
    try:
        sr.ImportFromEPSG(int(sr.GetAuthorityCode(None)))
    except TypeError:
        print("ERROR: Could not retrieve authority code (EPSG import failed).")
    return sr


def get_wkt(epsg, wkt_format="esriwkt"):
    """
    Get WKT-formatted projection information for an epsg code using the osr library
    :param epsg: Int of epsg
    :param wkt_format: Str of wkt format (default is esriwkt for shapefile projections)
    :output: str containing WKT (if error: default epsg=4326 is used)
    """
    default = 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295],UNIT["Meter",1]]'
    spatial_ref = osr.SpatialReference()
    try:
        spatial_ref.ImportFromEPSG(epsg)
    except TypeError:
        print("ERROR: epsg must be integer. Returning default WKT(epsg=4326).")
        return default
    except Exception:
        print("ERROR: epsg number does not exist. Returning default WKT(epsg=4326).")
        return default
    if wkt_format == "esriwkt":
        spatial_ref.MorphToESRI()
    return spatial_ref.ExportToPrettyWkt()


def make_prj(shp_file_name, epsg):
    """
    Generate a projection file for a shapefile
    :param shp_file_name: STR of a shapefile name (with directory e.g., "C:/temp/poly.shp")
    :param epsg: INT of epsg
    """
    shp_dir = shp_file_name.strip(shp_file_name.split("/")[-1].split("\\")[-1])
    shp_name = shp_file_name.split(".shp")[0].split("/")[-1].split("\\")[-1]
    with open(r"" + shp_dir + shp_name + ".prj", "w+") as prj:
        prj.write(get_wkt(epsg))


def reproject(source_dataset, new_projection_dataset):
    """
    Re-project a dataset (raster or shapefile) onto the spatial reference system
    of a (shapefile or raster) layer
    :param source_dataset: gdal.Dataset (shapefile or raster)
    :param new_projection_dataset: gdal.Dataset (shapefile or raster) with new projection info
    :output: if source==raster: GeoTIFF in same directory as source with "_reprojected"
    """

    # get source and target spatial reference systems
    srs_src = get_srs(source_dataset)
    srs_tar = get_srs(new_projection_dataset)

    # get dictionary of layer type and layer (or band=layer)
    layer_dict = get_layer(source_dataset)

    if layer_dict["type"] is "raster":
        reproject_raster(source_dataset, srs_src, srs_tar)

    if layer_dict["type"] is "vector":
        reproject_shapefile(source_dataset, layer_dict["layer"], srs_src, srs_tar)


def reproject_raster(source_dataset, source_srs, target_srs):
    """
    Reproject a raster dataset (preferably use through reproject function)
    :param source_dataset: osgeo.ogr.DataSource (instantiate with ogr.Open(SHP-FILE))
    :param source_srs: osgeo.osr.SpatialReference (instantiate with get_srs(source_dataset))
    :param target_srs: osgeo.osr.SpatialReference (instantiate with get_srs(DATASET-WITH-TARGET-PROJECTION))
    """
    # READ THE SOURCE GEO TRANSFORMATION (ORIGIN_X, PIXEL_WIDTH, 0, ORIGIN_Y, 0, PIXEL_HEIGHT)
    src_geo_transform = source_dataset.GetGeoTransform()

    # DERIVE PIXEL AND RASTER SIZE
    pixel_width = src_geo_transform[1]
    x_size = source_dataset.RasterXSize
    y_size = source_dataset.RasterYSize

    # ensure that TransformPoint (later) uses (x, y) instead of (y, x) with gdal version >= 3.0
    source_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    target_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

    # get CoordinateTransformation
    coord_trans = osr.CoordinateTransformation(source_srs, target_srs)

    # get boundaries of reprojected (new) dataset
    (org_x, org_y, org_z) = coord_trans.TransformPoint(src_geo_transform[0], src_geo_transform[3])
    (max_x, min_y, new_z) = coord_trans.TransformPoint(src_geo_transform[0] + src_geo_transform[1] * x_size,
                                                       src_geo_transform[3] + src_geo_transform[5] * y_size, )

    # INSTANTIATE NEW (REPROJECTED) IN-MEMORY DATASET AS A FUNCTION OF THE RASTER SIZE
    mem_driver = gdal.GetDriverByName('MEM')
    tar_dataset = mem_driver.Create("",
                                    int((max_x - org_x) / pixel_width),
                                    int((org_y - min_y) / pixel_width),
                                    1, gdal.GDT_Float32)
    # create new GeoTransformation
    new_geo_transformation = (org_x, pixel_width, src_geo_transform[2],
                              org_y, src_geo_transform[4], -pixel_width)

    # assign the new GeoTransformation to the target dataset
    tar_dataset.SetGeoTransform(new_geo_transformation)
    tar_dataset.SetProjection(target_srs.ExportToWkt())

    # PROJECT THE SOURCE RASTER ONTO THE NEW REPROJECTED RASTER
    rep = gdal.ReprojectImage(source_dataset, tar_dataset,
                              source_srs.ExportToWkt(), target_srs.ExportToWkt(),
                              gdal.GRA_Bilinear)

    # SAVE REPROJECTED DATASET AS GEOTIFF
    src_file_name = source_dataset.GetFileList()[0]
    tar_file_name = src_file_name.split(".tif")[0] + "_epsg" + target_srs.GetAuthorityCode(None) + ".tif"
    create_raster(tar_file_name, raster_array=tar_dataset.ReadAsArray(),
                  epsg=int(target_srs.GetAuthorityCode(None)),
                  geo_info=tar_dataset.GetGeoTransform())
    print("Saved reprojected raster as %s" % tar_file_name)


def reproject_shapefile(source_dataset, source_layer, source_srs, target_srs):
    """
    Reproject a shapefile dataset (preferably use through reproject function)
    :param source_dataset: osgeo.ogr.DataSource (instantiate with ogr.Open(SHP-FILE))
    :param source_layer:  osgeo.ogr.Layer (instantiate with source_dataset.GetLayer())
    :param source_srs: osgeo.osr.SpatialReference (instantiate with get_srs(source_dataset))
    :param target_srs: osgeo.osr.SpatialReference (instantiate with get_srs(DATASET-WITH-TARGET-PROJECTION))
    """
    # make GeoTransformation
    coord_trans = osr.CoordinateTransformation(source_srs, target_srs)

    # make target shapefile
    tar_file_name = verify_shp_name(source_dataset.GetName(), shorten_to=4).split(".shp")[
                        0] + "_epsg" + target_srs.GetAuthorityCode(None) + ".shp"
    tar_shp = create_shp(tar_file_name, layer_type=get_geom_simplified(source_layer))
    tar_lyr = tar_shp.GetLayer()

    # look up layer (features) definitions in input shapefile
    src_lyr_def = source_layer.GetLayerDefn()
    # copy field names of input layer attribute table to output layer
    for i in range(0, src_lyr_def.GetFieldCount()):
        tar_lyr.CreateField(src_lyr_def.GetFieldDefn(i))

    # instantiate feature definitions object for output layer (currently empty)
    tar_lyr_def = tar_lyr.GetLayerDefn()

    try:
        feature = source_layer.GetNextFeature()
    except AttributeError:
        print("ERROR: Invalid or empty vector dataset.")
        return None
    while feature:
        # get the input geometry
        geometry = feature.GetGeometryRef()
        # re-project (transform) geometry to new system
        geometry.Transform(coord_trans)
        # create new output feature
        out_feature = ogr.Feature(tar_lyr_def)
        # assign in-geometry to output feature and copy field values
        out_feature.SetGeometry(geometry)
        for i in range(0, tar_lyr_def.GetFieldCount()):
            out_feature.SetField(tar_lyr_def.GetFieldDefn(i).GetNameRef(), feature.GetField(i))
        # add the feature to the shapefile
        tar_lyr.CreateFeature(out_feature)
        # prepare next iteration
        feature = source_layer.GetNextFeature()

    # add projection file
    make_prj(tar_file_name, int(source_srs.GetAuthorityCode(None)))
