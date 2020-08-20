from fun import *
from raster import Raster


def calculate_habitat_area(layer, epsg):
    """
    Calculate the usable habitat area
    :param layer: osgeo.ogr.Layer
    :param epsg: int (Authority code drives area units)
    :return: None
    """
    pass

    


def main():
    """
    Calculate the usable physical habitat area based on a previously created chsi raster.
    Use the create_hsi_rasters.py script first to create a chsi raster.
    > uses chsi_ras_name: string (directory and file name ending on ".tif")
    > uses chsi_threshold_value: float (min=0.0, max=1.0)
    """
    pass


if __name__ == '__main__':
    chsi_raster_name = os.path.abspath("") + "\\habitat\\chsi.tif"
    chsi_threshold = 0.4

    # launch main function
    main()
